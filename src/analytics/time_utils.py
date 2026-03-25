"""Парсинг unix / ISO из query-параметров аналитики."""

from __future__ import annotations

from datetime import datetime, timezone


def parse_query_timestamp(value: str) -> int:
    try:
        return int(value)
    except Exception:
        pass
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp())
