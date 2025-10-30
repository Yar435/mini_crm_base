import os

from .base import *  # noqa

DEBUG = False


def _split_hosts(raw: str) -> list[str]:
    return [host.strip() for host in raw.split(",") if host.strip()]


SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "set-me")
ALLOWED_HOSTS = _split_hosts(os.getenv("DJANGO_ALLOWED_HOSTS", "localhost"))
INTERNAL_IPS = []

STATIC_URL = "/static/"
STATIC_ROOT = "/app/staticfiles"


def _env_flag(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = _env_flag("SESSION_COOKIE_SECURE", True)
CSRF_COOKIE_SECURE = _env_flag("CSRF_COOKIE_SECURE", True)
SECURE_SSL_REDIRECT = _env_flag("SECURE_SSL_REDIRECT", False)
SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "31536000"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = _env_flag("SECURE_HSTS_INCLUDE_SUBDOMAINS", True)
SECURE_HSTS_PRELOAD = _env_flag("SECURE_HSTS_PRELOAD", True)

SECURE_REFERRER_POLICY = "same-origin"
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

CSRF_TRUSTED_ORIGINS = _split_hosts(os.getenv("CSRF_TRUSTED_ORIGINS", ""))
