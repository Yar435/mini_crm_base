#!/usr/bin/env bash
set -euo pipefail

# Ждём доступность Postgres (простая проверка)
if [ -n "${POSTGRES_HOST:-}" ]; then
  echo "[entrypoint] waiting for postgres at ${POSTGRES_HOST}:${POSTGRES_PORT:-5432}..."
  for i in {1..30}; do
    if python - <<'PY'
import sys, os, socket
host=os.environ.get("POSTGRES_HOST","db"); port=int(os.environ.get("POSTGRES_PORT","5432"))
s=socket.socket(); s.settimeout(1)
try:
    s.connect((host,port))
    sys.exit(0)
except Exception:
    sys.exit(1)
PY
    then
      break
    fi
    sleep 1
  done
fi

echo "[entrypoint] migrate"
python manage.py migrate --noinput

echo "[entrypoint] setup RBAC"
python manage.py setup_rbac || true

echo "[entrypoint] collectstatic"
python manage.py collectstatic --noinput

echo "[entrypoint] starting app"
exec "$@"
