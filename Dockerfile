# ---------- Base builder (install deps) ----------
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl netcat-openbsd \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# requirements
COPY requirements.txt /app/requirements.txt
# requirements-dev.txt не копируем в прод образ
RUN pip install --upgrade pip \
  && pip wheel --no-cache-dir --no-deps --wheel-dir /wheels -r requirements.txt

# ---------- Final runtime ----------
FROM python:3.11-slim AS prod

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src

RUN adduser --disabled-password --gecos "" appuser
WORKDIR /app

# Ставим runtime wheels
COPY --from=builder /wheels /wheels
RUN pip install --no-cache /wheels/* && rm -rf /wheels

# Копируем только то, что нужно приложению
COPY src /app/src
COPY ops/docker/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Директория для статики
RUN mkdir -p /app/staticfiles && chown -R appuser:appuser /app

USER appuser
EXPOSE 8000

# Uvicorn (ASGI)
CMD [ "sh", "-lc", "DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE:-config.settings.prod} uvicorn config.asgi:application --host 0.0.0.0 --port 8000 --workers ${UVICORN_WORKERS:-4} --timeout-keep-alive 65" ]

# ==== ВАРИАНТ 2: gunicorn + uvicorn.worker (раскомментируй при желании) ====
# CMD [ "sh", "-lc", "DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE:-config.settings.prod} gunicorn config.asgi:application -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000 --workers ${GUNICORN_WORKERS:-3} --timeout 60 --access-logfile - --error-logfile -" ]
