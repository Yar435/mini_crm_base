## Проверено перед релизом

✅ API: /api/docs и /api/redoc открываются
✅ OpenAPI схема валидна
✅ Coverage = 93%
✅ CI workflow (GitHub Actions) зелёный
✅ Docker Compose запускает web/db/redis
✅ Gunicorn стартует под prod настройками
✅ pre-commit (black, isort, flake8, spectacular) — passed

## Важно к следующему этапу

- Добавить бейджи (coverage, build)
- CI: добавить docker build + smoke test
- Docker: подготовить push-pipeline (prod-image)
- Pre-commit: добавить debug-statement hook
- Celery/Redis интеграция → Week_04
