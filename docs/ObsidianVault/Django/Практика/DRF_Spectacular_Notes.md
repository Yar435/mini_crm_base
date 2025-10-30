## Цель

Автогенерация OpenAPI-схемы, Swagger и Redoc UI.

## Конфигурация

- Установлен: drf-spectacular + drf-spectacular-sidecar
- Подключено в REST_FRAMEWORK:
    `"DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema"`
- Представления: `@extend_schema_view`, `OpenApiExample` для Client / Deal / Manager.
- Swagger: `/api/docs/`
- Redoc: `/api/redoc/`
- JWT auth:
    `SPECTACULAR_SETTINGS = {     "SECURITY": [{"bearerAuth": []}],     "COMPONENTS": {"securitySchemes": {"bearerAuth": {"type": "http", "scheme": "bearer"}}} }`

## Валидация

- Команда: `python manage.py spectacular --validate --fail-on-warn --file src/schema.yaml`
- Добавлен pre-commit hook: `spectacular-validate`
- Схема проходит валидацию без ошибок (schema.yaml обновляется автоматически)
