# src/config/settings/test.py
from . import dev as base

globals().update(vars(base))

# Cache: in-memory (никакого django-redis)
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "mini_crm_test_cache",
    }
}

# Celery: выполняем синхронно, без внешнего брокера/бэкенда
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_BROKER_URL = "memory://"
CELERY_RESULT_BACKEND = "cache+memory://"

# На всякий случай — глушим Sentry
SENTRY_DSN = ""

HEALTH_STRICT_DEFAULT = False
HEALTH_REQUIRE_BEAT = False  # в тестах beat не обязателен
