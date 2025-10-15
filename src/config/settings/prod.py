import os

from .base import *

DEBUG = False
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "set-me")
ALLOWED_HOSTS = [
    h
    for h in os.getenv(
        "ALLOWED_HOSTS",
        "127.0.0.1,localhost",
    ).split(",")
    if h
]
INTERNAL_IPS = []  # не нужно в prod

# Статика: простейший вариант — WhiteNoise (потом можно отдать через Nginx)
INSTALLED_APPS += ["whitenoise.runserver_nostatic"]
MIDDLEWARE = ["whitenoise.middleware.WhiteNoiseMiddleware"] + MIDDLEWARE
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
WHITENOISE_USE_FINDERS = True

# Базовая безопасность (при реальном домене расширим)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
HOSTS = ("127.0.0.1", "localhost")
SECURE_HSTS_SECONDS = 3600
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
CSRF_TRUSTED_ORIGINS = (
    os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",") if os.getenv("CSRF_TRUSTED_ORIGINS") else []
)
