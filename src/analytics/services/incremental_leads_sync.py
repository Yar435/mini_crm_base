"""Инкрементальная подгрузка лидов из amoCRM API в AmoLead."""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any

from django.db import transaction
from django.db.models import Max

from analytics.amocrm_client import AmoCRMClientError, iter_leads_updated_since
from analytics.models import AmoLead, AmoPipeline, AmoStatus, AmoSyncState

SYNC_KEY_LEADS = "leads"


def _lead_row_from_api(
    item: dict[str, Any],
    *,
    valid_pipelines: set[int],
    valid_statuses: set[int],
) -> AmoLead | None:
    lid = item.get("id")
    if lid is None:
        return None
    pid = item.get("pipeline_id")
    if pid is None:
        return None
    try:
        pipeline_id = int(pid)
    except Exception:
        return None
    if pipeline_id not in valid_pipelines:
        return None

    sid = item.get("status_id")
    if sid is None:
        status_id = None
    else:
        try:
            si = int(sid)
        except Exception:
            status_id = None
        else:
            status_id = si if si in valid_statuses else None

    price = item.get("price")
    if price is not None:
        try:
            price_float = float(price)
        except Exception:
            price_float = None
    else:
        price_float = None

    created = item.get("created_at")
    updated = item.get("updated_at")
    is_deleted = bool(item.get("is_deleted", False))

    return AmoLead(
        id=int(lid),
        pipeline_id=pipeline_id,
        status_id=status_id,
        name=(item.get("name") or "")[:512],
        price=price_float,
        created_at=int(created) if created is not None else None,
        updated_at=int(updated) if updated is not None else None,
        responsible_user_id=item.get("responsible_user_id"),
        is_deleted=is_deleted,
        raw_json=item if isinstance(item, dict) else {},
    )


def run_incremental_leads_sync(
    *,
    subdomain: str,
    token: str,
    chunk_size: int = 200,
) -> dict[str, Any]:
    """
    Загружает лиды с updated_at >= watermark, upsert в БД, обновляет AmoSyncState.
    """
    valid_pipelines = set(AmoPipeline.objects.values_list("id", flat=True))
    valid_statuses = set(AmoStatus.objects.values_list("id", flat=True))
    if not valid_pipelines:
        return {"ok": False, "error": "no pipelines in DB; run sync_amo_transitions first"}

    state, _ = AmoSyncState.objects.get_or_create(
        key=SYNC_KEY_LEADS,
        defaults={"watermark_updated_at": 0},
    )
    wm_stored = int(state.watermark_updated_at)
    if wm_stored > 0:
        watermark = wm_stored
    else:
        max_db = AmoLead.objects.aggregate(m=Max("updated_at"))["m"]
        watermark = int(max_db) if max_db is not None else int(time.time()) - 86400 * 7

    processed = 0
    max_seen = watermark

    try:
        batch: list[AmoLead] = []
        for item in iter_leads_updated_since(subdomain, token, watermark):
            row = _lead_row_from_api(
                item, valid_pipelines=valid_pipelines, valid_statuses=valid_statuses
            )
            if row is None:
                continue
            if row.updated_at is not None:
                max_seen = max(max_seen, int(row.updated_at))
            batch.append(row)
            if len(batch) >= chunk_size:
                with transaction.atomic():
                    AmoLead.objects.bulk_create(
                        batch,
                        batch_size=chunk_size,
                        update_conflicts=True,
                        unique_fields=["id"],
                        update_fields=[
                            "pipeline_id",
                            "status_id",
                            "name",
                            "price",
                            "created_at",
                            "updated_at",
                            "responsible_user_id",
                            "is_deleted",
                            "raw_json",
                        ],
                    )
                processed += len(batch)
                batch.clear()

        if batch:
            with transaction.atomic():
                AmoLead.objects.bulk_create(
                    batch,
                    batch_size=chunk_size,
                    update_conflicts=True,
                    unique_fields=["id"],
                    update_fields=[
                        "pipeline_id",
                        "status_id",
                        "name",
                        "price",
                        "created_at",
                        "updated_at",
                        "responsible_user_id",
                        "is_deleted",
                        "raw_json",
                    ],
                )
            processed += len(batch)

        state.watermark_updated_at = max_seen
        state.last_error = ""
        state.last_run_at = datetime.now(tz=timezone.utc)
        state.save(update_fields=["watermark_updated_at", "last_error", "last_run_at"])

        return {
            "ok": True,
            "processed": processed,
            "watermark_from": watermark,
            "watermark_to": max_seen,
        }
    except AmoCRMClientError as e:
        state.last_error = str(e)[:2000]
        state.last_run_at = datetime.now(tz=timezone.utc)
        state.save(update_fields=["last_error", "last_run_at"])
        return {"ok": False, "error": str(e)}


def reset_leads_watermark(value: int = 0) -> None:
    AmoSyncState.objects.update_or_create(
        key=SYNC_KEY_LEADS,
        defaults={"watermark_updated_at": value, "last_error": ""},
    )
