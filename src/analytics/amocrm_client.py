"""Минимальный HTTP-клиент amoCRM API v4 (leads list) без внешних зависимостей."""

from __future__ import annotations

import json
import logging
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Iterator

logger = logging.getLogger(__name__)


class AmoCRMClientError(Exception):
    pass


def _http_get_json(url: str, token: str, *, timeout: int = 60) -> dict[str, Any]:
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "mini_crm_base/analytics",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8")
            if not body.strip():
                return {}
            return json.loads(body)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise AmoCRMClientError(f"HTTP {e.code}: {body[:500]}") from e
    except urllib.error.URLError as e:
        raise AmoCRMClientError(str(e)) from e


def iter_leads_updated_since(
    subdomain: str,
    token: str,
    updated_from_ts: int,
    *,
    limit: int = 250,
    sleep_sec: float = 0.3,
) -> Iterator[dict[str, Any]]:
    """
    Идём по страницам /api/v4/leads с filter[updated_at][from].
    Пауза между запросами для снижения риска 429.
    """
    base = f"https://{subdomain}.amocrm.ru/api/v4/leads"
    params: dict[str, Any] = {
        "filter[updated_at][from]": updated_from_ts,
        "limit": min(limit, 250),
    }
    query = urllib.parse.urlencode(params)
    url: str | None = f"{base}?{query}"

    while url:
        data = _http_get_json(url, token)
        for lead in data.get("_embedded", {}).get("leads", []):
            yield lead
        next_obj = data.get("_links", {}).get("next")
        if isinstance(next_obj, dict):
            url = next_obj.get("href")
        else:
            url = None
        if url and sleep_sec > 0:
            time.sleep(sleep_sec)
