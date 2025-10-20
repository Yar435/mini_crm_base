from .base import *
import copy

DEBUG = True

# ✅ Тестовая БД — всегда SQLite (никаких сетевых коннектов)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "test.sqlite3",
    }
}

# ✅ Кэш — в память
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

# ✅ Celery — синхронно/в памяти (без Redis)
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_BROKER_URL = "memory://"
CELERY_RESULT_BACKEND = "cache+memory://"

# ✅ Логи — попроще в тестах (без JSON-форматтера)
LOGGING = copy.deepcopy(LOGGING)  # чтобы не мутировать базовые настройки

fmt = "%(levelname)s %(name)s:%(lineno)d %(message)s"

# 1) Гарантируем наличие форматтера 'simple'
formatters = LOGGING.setdefault("formatters", {})
formatters.setdefault(
    "simple",
    {
        "class": "logging.Formatter",
        "format": fmt,
        "datefmt": "%H:%M:%S",
    },
)

# 2) Гарантируем наличие/исправность консольного хендлера и ставим 'simple'
handlers = LOGGING.setdefault("handlers", {})
if "console" in handlers and isinstance(handlers["console"], dict):
    # Переключаем существующий на StreamHandler + simple
    handlers["console"]["class"] = "logging.StreamHandler"
    handlers["console"]["formatter"] = "simple"
else:
    # Создаём заново консольный хендлер, если его не было
    handlers["console"] = {
        "class": "logging.StreamHandler",
        "level": "INFO",
        "formatter": "simple",
    }

# 3) Убедимся, что корневой логгер и django пишут в console
LOGGING.setdefault("root", {"handlers": ["console"], "level": "INFO"})
loggers = LOGGING.setdefault("loggers", {})
loggers.setdefault("django", {"handlers": ["console"], "level": "INFO", "propagate": False})


# (опционально) если у тебя есть строгая проверка /health
HEALTH_STRICT_DEFAULT = False
