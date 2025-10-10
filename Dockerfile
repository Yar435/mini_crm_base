# syntax=docker/dockerfile:1
FROM python:3.11-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates netcat-traditional && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements-dev.txt ./requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt
RUN useradd -m appuser
USER appuser

# dev-раздел можно добавить позже при желании
FROM base AS build
WORKDIR /app
COPY --chown=appuser:appuser ./src ./src

FROM base AS prod
WORKDIR /app
COPY --from=build --chown=appuser:appuser /app/src ./src
COPY --chown=appuser:appuser docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENV DJANGO_SETTINGS_MODULE=config.settings.prod \
    GUNICORN_CMD_ARGS="--workers=3 --bind=0.0.0.0:8000 --timeout=60 --access-logfile - --error-logfile -" \
    PYTHONPATH="/app/src"
EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
