# Week 05

## Week_05 — RBAC, Observability, стабильный OpenAPI

**Цели**

- Базовая ролевая модель и пермишены.

- Наблюдаемость и трассировка запросов.

- Автовалидация OpenAPI в CI.


**Задачи**

1. **RBAC скелет**

    - Роли: `admin`, `manager`, `viewer` (через `Group` + `Permission` или флаги).

    - DRF permissions на ViewSet’ах (создание/редактирование сделок только manager/admin).

    - E2E-тесты happy/deny.

2. **Observability**

    - `X-Request-ID` middleware, логирование JSON (uvicorn/gunicorn формат через `LOGGING`).

    - Rate throttling (DRF Anon/User) + тесты 429.

3. **OpenAPI**

    - Единый источник `schema.yaml` — генерить в CI артефактом; pre-commit hook spectacular-validate уже есть.


**DoD**

- Набор интеграционных тестов прав доступа зелёный.

- В логах виден `request_id`, поля: метод, путь, статус, длительность.

- CI валидирует сгенерённую схему и сохраняет как artifact.

## 📓 Итоги недели
- Что сделал:
- Что было сложно:
- Что повторить:

> Clockify: ____ ч
