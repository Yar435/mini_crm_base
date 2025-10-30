from .base import *  # noqa

DEBUG = True
ALLOWED_HOSTS = ["127.0.0.1", "localhost"]
INTERNAL_IPS = ["127.0.0.1", "localhost"]

STATIC_URL = "/static/"
STATIC_ROOT = "/app/staticfiles"

INSTALLED_APPS = INSTALLED_APPS + ["django.contrib.staticfiles",]

MIDDLEWARE = MIDDLEWARE + ["whitenoise.middleware.WhiteNoiseMiddleware"]

# Дополнительно (опционально)
WHITENOISE_AUTOREFRESH = True
WHITENOISE_MAX_AGE = 0

# Dev-специфика при необходимости, например debug-toolbar:
# INSTALLED_APPS += ["debug_toolbar"]
# MIDDLEWARE = ["debug_toolbar.middleware.DebugToolbarMiddleware"] + MIDDLEWARE
