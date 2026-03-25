import os
from datetime import timedelta
from pathlib import Path

from celery.schedules import crontab
from dotenv import load_dotenv

# BASE_DIR = .../src/config (как у тебя)
BASE_DIR = Path(__file__).resolve().parent.parent

# Грузим .env из КОРНЯ проекта (…/mini_crm_base/.env)
# Было: BASE_DIR_TO_ENV.parent / ".env" (это на директорию ВЫШЕ, мимо репо)
PROJECT_ROOT = Path(__file__).resolve().parents[2]  # …/src
load_dotenv(PROJECT_ROOT.parent / ".env")  # …/mini_crm_base/.env

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-key")
DEBUG = False  # по умолчанию выключен (dev включит)
ALLOWED_HOSTS = ["127.0.0.1", "localhost"]
INTERNAL_IPS = ["127.0.0.1", "localhost"]

INSTALLED_APPS = [
    # Django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # DRF + Spectacular
    "rest_framework",
    "django_filters",
    "drf_spectacular",
    "drf_spectacular_sidecar",
    "django_prometheus",
    "ratelimit",
    # Твои приложения
    "analytics",
    "core",
    "clients",
    "deals",
]

MIDDLEWARE = [
    "core.middleware.RequestIDMiddleware",
    "django_prometheus.middleware.PrometheusBeforeMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_prometheus.middleware.PrometheusAfterMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# DRF
REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.FormParser",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "core.auth.VersionedJWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PAGINATION_CLASS": "core.pagination.DefaultPagination",
    "PAGE_SIZE": 10,
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
}

# Spectacular
SPECTACULAR_SETTINGS = {
    "TITLE": "mini_crm_base API",
    "DESCRIPTION": "Учебно-практический CRM backend (Django + DRF + JWT)",
    "VERSION": "0.1.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "SECURITY": [{"bearerAuth": []}],
    "COMPONENTS": {
        "securitySchemes": {
            "bearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
            }
        }
    },
}

# --- Redis cache ---
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/1")
CACHES = {
    "default": {
        "BACKEND": "django_prometheus.cache.backends.redis.RedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
        "KEY_PREFIX": "mini_crm",
    }
}


# --- Celery broker/backend ---
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", REDIS_URL)
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", REDIS_URL)

CELERY_TIMEZONE = "UTC"
CELERY_TASK_TRACK_STARTED = True
# Пересборка графов может быть тяжёлой на больших данных; при алертах смотреть
# analytics_process_graph_build_seconds и длительность задачи rebuild_graph_snapshots.
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 min

CELERY_BEAT_SCHEDULE = {
    "heartbeat-every-minute": {
        "task": "core.tasks.heartbeat",
        "schedule": crontab(minute="*/1"),  # каждую минуту
        "args": (),
    },
    "analytics-rebuild-graphs-every-minute": {
        "task": "analytics.tasks.rebuild_graph_snapshots",
        "schedule": crontab(minute="*/1"),
        "args": (),
    },
    "analytics-incremental-leads": {
        "task": "analytics.tasks.incremental_sync_leads",
        "schedule": crontab(minute="*/15"),
        "args": (),
    },
}

# База: Postgres по env, иначе SQLite
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "")
POSTGRES_USER = os.getenv("POSTGRES_USER", "")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")

DATABASE_URL = os.getenv("DATABASE_URL", "")
if DATABASE_URL:
    import dj_database_url

    DATABASES = {
        "default": dj_database_url.parse(DATABASE_URL, conn_max_age=600, ssl_require=False)
    }
elif all([POSTGRES_HOST, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD]):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "HOST": POSTGRES_HOST,
            "PORT": POSTGRES_PORT,
            "NAME": POSTGRES_DB,
            "USER": POSTGRES_USER,
            "PASSWORD": POSTGRES_PASSWORD,
            "CONN_MAX_AGE": 600,
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": str(BASE_DIR / "db.sqlite3"),
        }
    }

ENGINE = DATABASES["default"]["ENGINE"]

PROM_ENGINES = {
    "django.db.backends.postgresql": "django_prometheus.db.backends.postgresql",
    "django.db.backends.sqlite3": "django_prometheus.db.backends.sqlite3",
    "django.db.backends.mysql": "django_prometheus.db.backends.mysql",
}

if ENGINE in PROM_ENGINES:
    DATABASES["default"]["ENGINE"] = PROM_ENGINES[ENGINE]

# Пароли / i18n / статика
VALIDATORS_BASE = "django.contrib.auth.password_validation."
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": VALIDATORS_BASE + "UserAttributeSimilarityValidator"},
    {"NAME": VALIDATORS_BASE + "MinimumLengthValidator"},
    {"NAME": VALIDATORS_BASE + "CommonPasswordValidator"},
    {"NAME": VALIDATORS_BASE + "NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,  # удобно для prod-паттернов
    "BLACKLIST_AFTER_ROTATION": False,  # мы пойдём через token_version
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
}


# --- Logging (JSON-ish) ---
try:
    import pythonjsonlogger  # noqa: F401

    _JSON_FORMATTER = {
        "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
        "fmt": "%(asctime)s %(levelname)s %(name)s %(message)s %(request_id)s",
    }
except Exception:
    # Fallback, чтобы проект мог стартовать без python-json-logger в окружении.
    _JSON_FORMATTER = {
        "class": "logging.Formatter",
        "format": "%(asctime)s %(levelname)s %(name)s %(message)s %(request_id)s",
    }

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "add_request_id": {
            "()": "core.logging_filters.RequestIDFilter",
        },
    },
    "formatters": {
        "json": _JSON_FORMATTER,
        # для локалки можно оставить и обычный формат при желании
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "filters": ["add_request_id"],
            "formatter": "json",
        },
    },
    "loggers": {
        "django": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "django.request": {"handlers": ["console"], "level": "WARNING", "propagate": False},
        # твой проект
        "core": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "clients": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "deals": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
    "root": {"handlers": ["console"], "level": "INFO"},
}


# --- Sentry (stub, integration disabled intentionally) ---
SENTRY_DSN = os.getenv("SENTRY_DSN", "")
SENTRY_ENV = os.getenv("SENTRY_ENV", "dev")
SENTRY_RELEASE = os.getenv("SENTRY_RELEASE", "")


HEALTH_STRICT_DEFAULT = True
HEALTH_STRICT = False
HEALTH_REQUIRE_BEAT = True  # в проде требуем пульс beat


METRICS_ENABLED = os.getenv("METRICS_ENABLED", "1") == "1"

# amoCRM REST API (incremental sync); задача incremental_sync_leads пропускается без этих значений
AMOCRM_SUBDOMAIN = os.getenv("AMOCRM_SUBDOMAIN", "").strip()
AMOCRM_ACCESS_TOKEN = os.getenv("AMOCRM_ACCESS_TOKEN", "").strip()
