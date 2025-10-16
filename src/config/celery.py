from celery import Celery

# ВАЖНО: НЕ переопределяем DJANGO_SETTINGS_MODULE здесь.
# Django уже загружен к моменту импортов Celery в manage.py/test-runner.

app = Celery("config")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
