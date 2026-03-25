from __future__ import annotations

import time
from typing import Optional

from celery import shared_task
from django.conf import settings
from django.core.cache import cache

import analytics.api_contract as contract
from analytics.cache_keys import make_process_graph_cache_key
from analytics.models import AmoPipeline
from analytics.services.graph_builder import build_process_graph_from_params


@shared_task
def rebuild_graph_snapshots() -> str:
    """
    Rebuild near real-time snapshots for graph endpoint.

    MVP-approach:
    - rolling_window snapshots for last N buckets
    - replay_speed snapshot only for current bucket

    Ключи кэша должны совпадать с make_process_graph_cache_key (без фильтров по цене).
    """
    pipeline_ids = list(AmoPipeline.objects.values_list("id", flat=True))
    if not pipeline_ids:
        return "no-pipelines"

    now_ts = int(time.time())
    current_bucket = now_ts - (now_ts % contract.BUCKET_STEP_SECONDS)
    window_minutes = contract.CELERY_ROLLING_WINDOW_MINUTES_DEFAULT
    from_status_id: Optional[int] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None

    updated = 0

    rolling_as_of_values = [
        current_bucket - i * contract.BUCKET_STEP_SECONDS
        for i in range(contract.CELERY_ROLLING_BUCKETS_BACK)
    ]
    for pipeline_id in pipeline_ids:
        for as_of_ts in rolling_as_of_values:
            key = make_process_graph_cache_key(
                pipeline_id=pipeline_id,
                mode="rolling_window",
                as_of_ts=as_of_ts,
                window_minutes=window_minutes,
                top_k=contract.CELERY_TOP_K_DEFAULT,
                from_status_id=from_status_id,
                min_price=min_price,
                max_price=max_price,
            )
            graph = build_process_graph_from_params(
                pipeline_id=pipeline_id,
                as_of=as_of_ts,
                mode="rolling_window",
                window_minutes=window_minutes,
                top_k=contract.CELERY_TOP_K_DEFAULT,
                from_status_id=from_status_id,
                min_price=min_price,
                max_price=max_price,
            )
            cache.set(key, graph, timeout=contract.CACHE_TIMEOUT_SECONDS)
            updated += 1

    for pipeline_id in pipeline_ids:
        as_of_ts = current_bucket
        key = make_process_graph_cache_key(
            pipeline_id=pipeline_id,
            mode="replay_speed",
            as_of_ts=as_of_ts,
            window_minutes=None,
            top_k=contract.CELERY_TOP_K_DEFAULT,
            from_status_id=from_status_id,
            min_price=min_price,
            max_price=max_price,
        )
        graph = build_process_graph_from_params(
            pipeline_id=pipeline_id,
            as_of=as_of_ts,
            mode="replay_speed",
            window_minutes=None,
            top_k=contract.CELERY_TOP_K_DEFAULT,
            from_status_id=from_status_id,
            min_price=min_price,
            max_price=max_price,
        )
        cache.set(key, graph, timeout=contract.CACHE_TIMEOUT_SECONDS)
        updated += 1

    return f"ok:{updated}"


@shared_task
def incremental_sync_leads() -> str:
    """
    Инкрементальная подгрузка лидов из amoCRM API (требуются AMOCRM_SUBDOMAIN + AMOCRM_ACCESS_TOKEN).
    """
    subdomain = (getattr(settings, "AMOCRM_SUBDOMAIN", None) or "").strip()
    token = (getattr(settings, "AMOCRM_ACCESS_TOKEN", None) or "").strip()
    if not subdomain or not token:
        return "skipped:no-credentials"

    from analytics.services.incremental_leads_sync import run_incremental_leads_sync

    out = run_incremental_leads_sync(subdomain=subdomain, token=token)
    if not out.get("ok"):
        err = str(out.get("error", "unknown"))[:500]
        return f"error:{err}"
    return f"ok:processed={out.get('processed', 0)}"
