# src/config/asgi.py
import os
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.prod")  # В прод-контейнере можно переопределить ENV
application = get_asgi_application()
