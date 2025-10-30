# Week_03 — Swagger (drf-spectacular), Coverage, DevOps Docs

## 🎯 Цель

- Сделать backend «прозрачным» и измеримым: добавить Swagger/Redoc-документацию, настроить pytest-coverage и внедрить базовый CI pipeline.
- Обновить DevOps-документацию в Obsidian и привести docker/prod-сборку к рабочему состоянию.

---

## ⚙️ Практика

- Интегрировать **drf-spectacular** для автогенерации Swagger и Redoc.
- Настроить **pytest-cov** для подсчёта покрытия тестов.
- Подключить **GitHub Actions** (или GitLab CI) для автоматической проверки и отчётов.
- Обновить **Dockerfile** и `docker-compose.yml` под dev/prod режимы.
- Добавить расширенные **pre-commit hooks** (yesqa, debug-statements, merge-conflict и т.п.).
- Пополнить Obsidian Vault новыми заметками: `Coverage_and_CI.md`, `DRF_Spectacular_Notes.md`, `Release_Readiness.md`.

---

## 🧩 Задания

- [x] Интегрировать **drf-spectacular** для автогенерации Swagger и Redoc. ✅ 2025-10-10
- [x] Настроить **pytest-cov** для подсчёта покрытия тестов. ✅ 2025-10-10
- [x] Подключить **GitHub Actions** (или GitLab CI) для автоматической проверки и отчётов. ✅ 2025-10-10
- [x] Обновить **Dockerfile** и `docker-compose.yml` под dev/prod режимы. ✅ 2025-10-10
- [x] Добавить расширенные **pre-commit hooks** (yesqa, debug-statements, merge-conflict и т.п.). ✅ 2025-10-10
- [x] Пополнить Obsidian Vault новыми заметками: `Coverage_and_CI.md`, `DRF_Spectacular_Notes.md`, `Release_Readiness.md`. ✅ 2025-10-10

---

## 📓 Итоги недели

- **Что сделал:**
    - Завершил интеграцию **drf-spectacular** — схема генерируется, валидируется, `/api/docs` и `/api/redoc` открываются.
    - Настроил **pytest с coverage (93%)**, добавил отчёт `coverage.xml` для CI.
    - Подключил и довёл до зелёного состояния **pre-commit** (black, isort, flake8, spectacular-validate).
    - Развернул полноценный **Docker Compose** с web/db/redis, gunicorn работает под `prod`-настройками.
    - Добавил **GitHub Actions CI** для валидации схемы и автотестов.
    - Обновил **Obsidian Vault**: Docker, CI/CD, Spectacular, Release Readiness.
    - Репозиторий связан с GitHub и проходит pipeline без ошибок.

- **Что было сложно:**
    - Разобраться с импортами `*` в `prod.py` и F403/F405 от flake8.
    - Отладка pre-commit hook’а spectacular-validate на Windows (bash → python).
    - Проблема `No module named 'config'` при запуске gunicorn (решена через `PYTHONPATH=/app/src`).
    - Мелкие нюансы Docker Compose (volume, env-файлы, healthcheck).

- **Что повторить:**
    - Настройку multi-stage Dockerfile и entrypoint.sh для prod.
    - Конфигурацию REST_FRAMEWORK + SPECTACULAR_SETTINGS.
    - Создание CI workflow с валидацией схемы и coverage-отчётом.
    - Логику pre-commit (установка, ручной запуск, игнор правил flake8).

> Week_03 — полностью закрыт по DoD. Репозиторий готов к CI/CD и переходу на Celery + Redis в Week_04. 🚀

> Clockify: ____ ч
