# src/config/settings/dev.py
import os
from pathlib import Path

from dotenv import load_dotenv

from . import base as base

DEBUG = True
ALLOWED_HOSTS = ["127.0.0.1", "localhost"]
INTERNAL_IPS = ["127.0.0.1", "localhost"]

# .env и секрет
BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR.parent / ".env")
SECRET_KEY = base.SECRET_KEY  # или твоя загрузка из .env

# ── унаследовать обязательные настройки ──
ROOT_URLCONF = base.ROOT_URLCONF
WSGI_APPLICATION = base.WSGI_APPLICATION
ASGI_APPLICATION = base.ASGI_APPLICATION
TEMPLATES = base.TEMPLATES
MIDDLEWARE = [
    "debug_toolbar.middleware.DebugToolbarMiddleware",
] + base.MIDDLEWARE


# локаль/статик/прочее
LANGUAGE_CODE = base.LANGUAGE_CODE
TIME_ZONE = base.TIME_ZONE
USE_I18N = base.USE_I18N
USE_TZ = base.USE_TZ
STATIC_URL = base.STATIC_URL
STATICFILES_DIRS = getattr(base, "STATICFILES_DIRS", [])
DEFAULT_AUTO_FIELD = base.DEFAULT_AUTO_FIELD

# БД (как у тебя было)
DB_NAME = os.getenv("POSTGRES_DB", "app")
DB_USER = os.getenv("POSTGRES_USER", "app")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "app")
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": DB_NAME,
        "USER": DB_USER,
        "PASSWORD": DB_PASSWORD,
        "HOST": DB_HOST,
        "PORT": DB_PORT,
        "OPTIONS": {"sslmode": "disable"},
    }
}

# ВАЖНО: расширяем тут, а не мутируем base
INSTALLED_APPS = base.INSTALLED_APPS + [
    "rest_framework",
    "core",
    "clients",
    "deals",
    "debug_toolbar",
]

# DRF
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
}
