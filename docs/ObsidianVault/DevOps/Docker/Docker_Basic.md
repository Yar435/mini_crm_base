# Docker — mini_crm_base

- Multi-stage Dockerfile: base/dev/prod
- Prod: gunicorn, migrate + collectstatic в entrypoint
- Compose: web + db (postgres) + redis
- ENV:
  - POSTGRES_* (HOST=db), REDIS_URL=redis://redis:6379/1
  - DJANGO_SETTINGS_MODULE=config.settings.prod
- Команды:
  - docker compose up --build
  - docker compose logs -f web
  - smoke: /health/, /api/docs/
