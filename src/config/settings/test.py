# from .dev import *

# ⚠️ В тестах не ходим во внешний Redis: локальный in-memory cache
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "mini_crm_test_cache",
    }
}

# Celery: исполняем задачи синхронно в том же процессе (без брокера)
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_BROKER_URL = "memory://"
CELERY_RESULT_BACKEND = "cache+memory://"

# На всякий случай — отключаем Sentry в тестах
SENTRY_DSN = ""
