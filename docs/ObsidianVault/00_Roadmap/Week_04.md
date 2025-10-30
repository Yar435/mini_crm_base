

## 🎯 Цель
- Гарантировать корректную работу фоновых задач.
- Закрыть отзыв JWT.
- Включить docker-build и smoke-тест `/health` в CI.

## ⚙️ Практика

## 🧩 Задания
1. **Celery**
    - Дописать `config/celery.py` (broker/backend из settings, автодискавер задач).
    - `core/tasks.py`: `heartbeat()` + e2e-тест через `CELERY_TASK_ALWAYS_EAGER=True` (в тестах).
    - Health-пробки: `celery inspect ping` в make/скрипте и healthcheck для `worker`.
2. **JWT-revocation (token_version)**
    - Поле `token_version` в `User` (или прокси-модель), инкремент при `logout`/`password_change`.
    - Кастомный `TokenObtainPairView`, добавляющий `token_version` в claim; кастомный аутентификатор, валидирующий claim с актуальной версией из БД/кэша.
    - Ручка `POST /api/auth/logout/` (инкремент версии) + тесты.
3. **CI**
    - Триггеры `push`/`pull_request`, Python 3.11.
    - Services: Postgres 16, Redis 7; миграции, тесты с coverage xml.
    - Job docker-build (no-push) + контейнерный smoke: `docker compose up -d web && curl /health`.

**DoD**
- `/health` отдаёт 200 в контейнере в CI.
- `celery beat/worker` запускаются, `heartbeat` выполняется (лог/Flower).
- Тесты зелёные, coverage ≥ 70% (одинаковый отчёт локально и в CI).
- `POST /api/auth/logout/` инвалидирует старый access (провален тест на старом токене).

## 📓 Итоги недели
- Что сделал:
	- - **Celery + Redis** полностью подняты и работают (heartbeat проверен).
	- **JWT revocation** реализован (logout → token_version).
	- **CI** собран и проходит smoke (тесты + docker + /health).
	- **tasks.ps1** готов, удобен под Windows.
	- **drf-spectacular** в зелёном состоянии, схема валидна.

	Можно считать, что «фаза DevOps + Quality foundation» завершена.

- Что было сложно:
- Что делать дальше:
	1. **Реальные Celery-таски** — не просто heartbeat, а:
	    - пример рассылки (email или webhook);
	    - логирование активности клиента/сделки;
	    - возможно — интеграция с внешним API (через `requests`).
	2. **Планирование задач (beat)** — добавить несколько crontab-примеров.
	3. **Добавить метрики и мониторинг**:
	    - health-check для Celery,
	    - настройка Flower (уже есть, но можно улучшить),
	    - мини-дашборд или Prometheus-совместимые метрики.
	4. **Рефакторинг core/tasks.py** — вынести логику heartbeat, уведомлений и т.п.
	5. **Обновить документацию (Obsidian)** — `Celery_Integration.md`, `Background_Tasks.md`.

> Clockify: ____ ч
