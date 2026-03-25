from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Literal, Optional, Set, Tuple

from analytics.models import AmoLead, AmoLeadTransition, AmoStatus


GraphMode = Literal["replay_speed", "rolling_window"]


@dataclass(frozen=True)
class ProcessGraphQuery:
    pipeline_id: int
    as_of_ts: int
    mode: GraphMode
    window_minutes: Optional[int]
    top_k: int
    from_status_id: Optional[int]
    min_price: Optional[float] = None
    max_price: Optional[float] = None


def lead_ids_matching_price(
    *,
    pipeline_id: int,
    min_price: Optional[float],
    max_price: Optional[float],
) -> Optional[set[int]]:
    """
    Если min_price и max_price оба None — фильтр по цене не применяется (вернуть None).
    Иначе вернуть множество lead_id из AmoLead по воронке и диапазону цены.
    Лиды без price (NULL) при активном фильтре не включаются.
    """
    if min_price is None and max_price is None:
        return None
    qs = AmoLead.objects.filter(pipeline_id=pipeline_id, is_deleted=False).exclude(
        price__isnull=True
    )
    if min_price is not None:
        qs = qs.filter(price__gte=min_price)
    if max_price is not None:
        qs = qs.filter(price__lte=max_price)
    return set(qs.values_list("id", flat=True))


def _parse_ts_as_int(as_of: str | int) -> int:
    if isinstance(as_of, int):
        return as_of
    try:
        return int(as_of)
    except Exception:
        pass
    # ISO datetime fallback
    try:
        dt = datetime.fromisoformat(as_of.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return int(dt.timestamp())
    except Exception as e:
        raise ValueError(f"Invalid as_of value: {as_of!r}") from e


def build_process_graph(query: ProcessGraphQuery) -> dict[str, Any]:
    # Import here to keep module import fast for URLConf/tests.
    from django.db.models import Case, Count, IntegerField, Sum, Value, When

    if query.mode not in ("replay_speed", "rolling_window"):
        raise ValueError(f"Unsupported mode: {query.mode}")

    if query.mode == "rolling_window":
        if query.window_minutes is None:
            raise ValueError("window_minutes is required for rolling_window")
        if query.window_minutes <= 0:
            raise ValueError("window_minutes must be positive")
        window_seconds = int(query.window_minutes) * 60
        start_ts = query.as_of_ts - window_seconds
    else:
        start_ts = None

    # Statuses within the pipeline to provide node labels + is_final flag.
    pipeline_statuses_qs = AmoStatus.objects.filter(pipeline_id=query.pipeline_id).only(
        "id", "name", "is_final"
    )
    statuses_by_id: Dict[int, AmoStatus] = {s.id: s for s in pipeline_statuses_qs}

    # Candidate transitions for edge counts / p_final.
    qs = AmoLeadTransition.objects.filter(
        at__lte=query.as_of_ts,
        from_status__pipeline_id=query.pipeline_id,
        to_status__pipeline_id=query.pipeline_id,
        from_status_id__isnull=False,
        to_status_id__isnull=False,
    )
    if start_ts is not None:
        qs = qs.filter(at__gte=start_ts)
    if query.from_status_id is not None:
        qs = qs.filter(from_status_id=query.from_status_id)

    lead_price_filter = lead_ids_matching_price(
        pipeline_id=query.pipeline_id,
        min_price=query.min_price,
        max_price=query.max_price,
    )
    if lead_price_filter is not None:
        qs = qs.filter(lead_id__in=lead_price_filter)

    edge_stats_qs = (
        qs.values("from_status_id", "to_status_id")
        .annotate(
            weight=Count("event_id"),
            final_count=Sum(
                Case(
                    When(to_status__is_final=True, then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField(),
                )
            ),
        )
    )

    edge_stats = list(edge_stats_qs)
    # Sort by weight, then by p_final (stable tie-breaker).
    def _sort_key(e: dict[str, Any]) -> Tuple[int, float]:
        w = int(e.get("weight") or 0)
        fc = int(e.get("final_count") or 0)
        p = (fc / w) if w else 0.0
        return (w, p)

    edge_stats.sort(key=_sort_key, reverse=True)
    selected = edge_stats[: max(1, int(query.top_k))]
    selected_edges: Set[Tuple[int, int]] = {
        (int(e["from_status_id"]), int(e["to_status_id"])) for e in selected
    }

    # For avg_time_sec we need proper sequencing by lead_id.
    from_ids = [x for x, _ in selected_edges]
    to_ids = [y for _, y in selected_edges]
    selected_lead_ids_qs = qs.filter(
        from_status_id__in=from_ids,
        to_status_id__in=to_ids,
    ).values_list("lead_id", flat=True).distinct()
    lead_ids = list(selected_lead_ids_qs)

    avg_time_by_edge: Dict[Tuple[int, int], Tuple[float, int]] = {}
    if lead_ids:
        # Fetch full transition sequence for those leads.
        seq_qs = (
            AmoLeadTransition.objects.filter(
                lead_id__in=lead_ids,
                at__lte=query.as_of_ts,
                from_status__pipeline_id=query.pipeline_id,
                to_status__pipeline_id=query.pipeline_id,
            )
            .only("lead_id", "at", "from_status_id", "to_status_id")
            .order_by("lead_id", "at")
        )
        if start_ts is not None:
            seq_qs = seq_qs.filter(at__gte=start_ts)

        prev_at_by_lead: Dict[int, Optional[int]] = {}
        for t in seq_qs.iterator():
            lead_id = int(t.lead_id)
            at = int(t.at)
            prev_at = prev_at_by_lead.get(lead_id)

            edge = (int(t.from_status_id), int(t.to_status_id))
            if prev_at is not None and edge in selected_edges:
                dt = at - int(prev_at)
                if dt >= 0:
                    current_sum, current_cnt = avg_time_by_edge.get(edge, (0.0, 0))
                    avg_time_by_edge[edge] = (current_sum + float(dt), current_cnt + 1)

            prev_at_by_lead[lead_id] = at

    # Nodes: only statuses that are part of selected edges.
    node_ids: Set[int] = set()
    for f_id, t_id in selected_edges:
        node_ids.add(f_id)
        node_ids.add(t_id)

    nodes = [
        {
            "id": sid,
            "name": statuses_by_id[sid].name if sid in statuses_by_id else str(sid),
            "is_final": bool(statuses_by_id[sid].is_final) if sid in statuses_by_id else False,
        }
        for sid in node_ids
    ]
    # Make output deterministic for UI diffing.
    nodes.sort(key=lambda n: n["id"])

    edges_out: list[dict[str, Any]] = []
    for e in selected:
        from_id = int(e["from_status_id"])
        to_id = int(e["to_status_id"])
        w = int(e["weight"])
        fc = int(e.get("final_count") or 0)
        p_final = (fc / w) if w else 0.0

        sum_cnt = avg_time_by_edge.get((from_id, to_id))
        if sum_cnt is None:
            avg_time_sec = None
        else:
            total_dt, cnt_dt = sum_cnt
            avg_time_sec = (total_dt / cnt_dt) if cnt_dt else None

        edges_out.append(
            {
                "from_status_id": from_id,
                "to_status_id": to_id,
                "weight": w,
                "avg_time_sec": avg_time_sec,
                "p_final": p_final,
            }
        )

    return {
        "nodes": nodes,
        "edges": edges_out,
        "meta": {
            "pipeline_id": query.pipeline_id,
            "as_of": query.as_of_ts,
            "mode": query.mode,
            "window_minutes": query.window_minutes,
            "top_k": query.top_k,
            "from_status_id": query.from_status_id,
            "min_price": query.min_price,
            "max_price": query.max_price,
            "computed_at": int(datetime.now(tz=timezone.utc).timestamp()),
        },
    }


def build_process_graph_from_params(
    *,
    pipeline_id: int,
    as_of: str | int,
    mode: GraphMode,
    window_minutes: Optional[int],
    top_k: int,
    from_status_id: Optional[int],
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
) -> dict[str, Any]:
    as_of_ts = _parse_ts_as_int(as_of)
    query = ProcessGraphQuery(
        pipeline_id=pipeline_id,
        as_of_ts=as_of_ts,
        mode=mode,
        window_minutes=window_minutes,
        top_k=top_k,
        from_status_id=from_status_id,
        min_price=min_price,
        max_price=max_price,
    )
    return build_process_graph(query)

