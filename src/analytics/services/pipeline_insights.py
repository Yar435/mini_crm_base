"""Сводки по воронке и переходам для read-only API."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from django.db.models import Count, Q

from analytics.models import AmoLead, AmoLeadTransition, AmoStatus


def build_pipeline_funnel(*, pipeline_id: int, include_deleted: bool) -> dict[str, Any]:
    qs = AmoLead.objects.filter(pipeline_id=pipeline_id)
    if not include_deleted:
        qs = qs.filter(is_deleted=False)

    status_ids = (
        AmoStatus.objects.filter(pipeline_id=pipeline_id)
        .order_by("sort", "id")
        .values_list("id", flat=True)
    )
    status_meta = {
        s.id: s
        for s in AmoStatus.objects.filter(pipeline_id=pipeline_id).only(
            "id", "name", "is_final", "sort"
        )
    }

    counts_by_status: dict[int | None, int] = {}
    agg = qs.values("status_id").annotate(c=Count("id"))
    for row in agg:
        counts_by_status[row["status_id"]] = int(row["c"])

    statuses_out: list[dict[str, Any]] = []
    for sid in status_ids:
        sm = status_meta.get(sid)
        statuses_out.append(
            {
                "status_id": sid,
                "name": sm.name if sm else str(sid),
                "is_final": bool(sm.is_final) if sm else False,
                "count": counts_by_status.get(sid, 0),
            }
        )

    null_count = counts_by_status.get(None, 0)
    if null_count:
        statuses_out.append(
            {
                "status_id": None,
                "name": "(no status)",
                "is_final": False,
                "count": null_count,
            }
        )

    total = qs.count()
    return {
        "pipeline_id": pipeline_id,
        "statuses": statuses_out,
        "meta": {
            "total_leads": total,
            "include_deleted": include_deleted,
            "computed_at": int(datetime.now(tz=timezone.utc).timestamp()),
        },
    }


def build_transitions_by_user(
    *,
    pipeline_id: int,
    from_ts: int,
    to_ts: int,
    top_k: int,
) -> dict[str, Any]:
    if from_ts > to_ts:
        raise ValueError("from_ts must be <= to_ts")

    base = AmoLeadTransition.objects.filter(
        at__gte=from_ts,
        at__lte=to_ts,
        from_status__pipeline_id=pipeline_id,
        to_status__pipeline_id=pipeline_id,
    )

    rows = (
        base.values("by_user")
        .annotate(transitions=Count("event_id"))
        .order_by("-transitions")[: max(1, top_k)]
    )

    out: list[dict[str, Any]] = []
    for row in rows:
        uid = row["by_user"]
        out.append(
            {
                "user_id": uid,
                "transitions": int(row["transitions"]),
            }
        )

    unknown = (
        base.filter(Q(by_user__isnull=True) | Q(by_user=0))
        .aggregate(c=Count("event_id"))["c"]
        or 0
    )

    return {
        "pipeline_id": pipeline_id,
        "from_ts": from_ts,
        "to_ts": to_ts,
        "top_k": top_k,
        "by_user": out,
        "meta": {
            "unknown_user_transitions": int(unknown),
            "computed_at": int(datetime.now(tz=timezone.utc).timestamp()),
        },
    }
