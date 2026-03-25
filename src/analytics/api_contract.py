"""
Контракт HTTP API аналитики (параметры, лимиты, коды ответов).

Используется в ProcessGraphView и в OpenAPI (drf-spectacular).
"""

from __future__ import annotations

# --- process-graph ---

# Квант времени для группировки кэша (совпадает с bucket в cache_keys).
BUCKET_STEP_SECONDS = 60

# TTL кэша ответа графа (секунды).
CACHE_TIMEOUT_SECONDS = 15 * 60

TOP_K_DEFAULT = 20
TOP_K_MAX = 500

# Celery: прогрев rolling_window за последние N минутных bucket'ов.
CELERY_ROLLING_BUCKETS_BACK = 30
CELERY_ROLLING_WINDOW_MINUTES_DEFAULT = 30
CELERY_TOP_K_DEFAULT = TOP_K_DEFAULT

# Режимы графа
GRAPH_MODES = ("replay_speed", "rolling_window")

# Ошибки клиента: все с HTTP 400, тело вида {"detail": "<сообщение>"}.
# Коды ниже — для документации и тестов (константа detail).
ERR_PIPELINE_ID_REQUIRED = "pipeline_id is required"
ERR_AS_OF_REQUIRED = "as_of is required"
ERR_PIPELINE_ID_INVALID = "pipeline_id must be int"
ERR_MODE_INVALID = "mode must be replay_speed or rolling_window"
ERR_WINDOW_MINUTES_INVALID = "window_minutes must be int"
ERR_WINDOW_MINUTES_REQUIRED = "window_minutes is required for rolling_window"
ERR_TOP_K_INVALID = "top_k must be int"
ERR_TOP_K_BOUNDS = "top_k out of bounds"
ERR_FROM_STATUS_ID_INVALID = "from_status_id must be int"
ERR_AS_OF_INVALID = "as_of must be unix timestamp or ISO datetime"
ERR_MIN_PRICE_INVALID = "min_price must be a non-negative number"
ERR_MAX_PRICE_INVALID = "max_price must be a non-negative number"
ERR_PRICE_RANGE_INVALID = "min_price cannot be greater than max_price"
