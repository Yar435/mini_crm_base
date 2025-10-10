#!/usr/bin/env bash
set -e

# ждём БД (если указана)
if [ -n "$POSTGRES_HOST" ]; then
  echo "⏳ Waiting for DB at $POSTGRES_HOST:${POSTGRES_PORT:-5432}..."
  until nc -z "$POSTGRES_HOST" "${POSTGRES_PORT:-5432}"; do
    sleep 1
  done
fi

echo "📦 migrate..."
python src/manage.py migrate --noinput || (echo 'migrate failed' && exit 1)

echo "🧹 collectstatic..."
python src/manage.py collectstatic --noinput || true

echo "🚀 start gunicorn..."
exec gunicorn config.wsgi:application
