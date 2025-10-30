from typing import Any, MutableMapping, cast

from .base import *

DEBUG = True

RF = cast(MutableMapping[str, Any], REST_FRAMEWORK)
LG = cast(MutableMapping[str, Any], LOGGING)

# Примеры модификаций — меняем через алиасы:
RF.setdefault("DEFAULT_AUTHENTICATION_CLASSES", [])
RF["DEFAULT_AUTHENTICATION_CLASSES"] = [
    "rest_framework_simplejwt.authentication.JWTAuthentication",
]

# если модифицируешь пагинацию/рендереры/прочее — тоже через RF[...] = ...

# Тестовая БД SQLite — строго строка, не Path:
DATABASES["default"]["NAME"] = str(BASE_DIR / "test.sqlite3")

# ✅ Тестовая БД — всегда SQLite (никаких сетевых коннектов)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": str(BASE_DIR / "test.sqlite3"),
    }
}

# ✅ Кэш — в память (никаких внешних сервисов в unit-тестах)
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
# LOGGING = copy.deepcopy(LOGGING)  # чтобы не мутировать базовые настройки

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
