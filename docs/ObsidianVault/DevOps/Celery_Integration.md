# Celery Integration — mini_crm_base

## Компоненты
- Celery (основной воркер)
- Redis (брокер + backend)
- Celery Beat (планировщик периодических задач)

## Тестовые задачи
- `debug_task(payload)` — проверка очереди
- `heartbeat()` — периодический тик каждую минуту

## Docker Compose
- web — Django + Gunicorn
- worker — Celery worker
- beat — Celery beat scheduler
- redis — брокер сообщений

## Проверка
```bash
docker compose exec web python src/manage.py shell -c "from core.tasks import debug_task; r=debug_task.delay({'ping':'pong'}); print(r.id)"
docker compose logs -f worker
docker compose logs -f beat
```
