"""
Единый способ строить ключи кэша для графа процессов (views + Celery).
Любой новый query-параметр, влияющий на результат, обязан попасть сюда.
"""

from __future__ import annotations

from typing import Optional

from analytics.api_contract import BUCKET_STEP_SECONDS
from analytics.services.graph_builder import GraphMode


def _price_segment(
    min_price: Optional[float],
    max_price: Optional[float],
) -> str:
    if min_price is None and max_price is None:
        return "price=none"
    lo = "" if min_price is None else str(min_price)
    hi = "" if max_price is None else str(max_price)
    return f"price={lo}-{hi}"


def make_process_graph_cache_key(
    *,
    pipeline_id: int,
    mode: GraphMode,
    as_of_ts: int,
    window_minutes: Optional[int],
    top_k: int,
    from_status_id: Optional[int],
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
) -> str:
    bucket_start = as_of_ts - (as_of_ts % BUCKET_STEP_SECONDS)
    from_part = str(from_status_id) if from_status_id is not None else "all"
    window_part = str(window_minutes) if window_minutes is not None else "na"
    price_part = _price_segment(min_price, max_price)
    return (
        f"analytics:graph:pipeline={pipeline_id}:mode={mode}:bucket={bucket_start}:"
        f"window={window_part}:top_k={top_k}:from={from_part}:{price_part}"
    )


def make_pipeline_funnel_cache_key(*, pipeline_id: int, include_deleted: bool) -> str:
    return f"analytics:funnel:pipeline={pipeline_id}:del={int(include_deleted)}"


def make_transitions_by_user_cache_key(
    *, pipeline_id: int, from_ts: int, to_ts: int, top_k: int
) -> str:
    return f"analytics:by_user:pipeline={pipeline_id}:from={from_ts}:to={to_ts}:top={top_k}"
