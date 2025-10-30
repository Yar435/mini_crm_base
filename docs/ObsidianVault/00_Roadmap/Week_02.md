# Week 02

## 🎯 Цель

- Укрепить технический фундамент проекта **mini_crm_base**: тестирование, автодокументация, DevOps-инструменты и единый код-стайл.
- Подготовить инфраструктуру к CI/CD и будущим фоновым задачам (Celery + Redis).

---

## ⚙️ Практика

- Настроен **pytest-django** и базовые **API-тесты** (`APIClient`, фикстуры, CRUD-тесты).
- Включён **django-filter**, добавлены фильтры, пагинация и сортировка в API.
- Подключён **JWT-аутентификатор** через `djangorestframework-simplejwt`.
- Настроены **permissions** (`IsAuthenticatedOrReadOnly`).
- Подключены и протестированы **pre-commit hooks** (`black`, `isort`, `flake8`, `end-of-file-fixer`, `trailing-whitespace`).
- Подготовлен **Docker Compose** с рабочим окружением (`docker compose up` работает).
- Разделены **настройки** (`base.py`, `dev.py`), добавлен `django-debug-toolbar`.
- Создана и систематизирована структура в **Obsidian Vault** для DevOps, Django, Git и Docker.

---

## 🧩 Задания

- [x] Настроить и протестировать **pytest + APIClient** ✅ 2025-10-10
- [x] Подключить **JWT-аутентификацию** и базовые permissions ✅ 2025-10-10
- [x] Реализовать **фильтрацию, пагинацию, поиск** через `django-filter` ✅ 2025-10-10
- [x] Настроить **pre-commit** и вычистить кодстайл ✅ 2025-10-10
- [x] Подключить **Docker Desktop / compose**, протестировать окружение ✅ 2025-10-10
- [x] Ввести **dev/prod настройки** и `debug-toolbar` ✅ 2025-10-10
- [x] Систематизировать материалы в **Obsidian Vault** (Django, DevOps, Git) ✅ 2025-10-10

---

## 📓 Итоги недели

**Что сделал:**

- Завершил основной CRUD-функционал API (Client, Deal, Manager).
- Настроил JWT-аутентификацию, фильтры и тесты.
- Внедрил единый pre-commit-pipeline и docker-окружение.
- Подготовил базу для CI/CD и автогенерации схемы API.

**Что было сложно:**

- Первичная настройка docker-окружения и зависимостей.
- Совместная работа pytest и DRF с JWT-аутентификацией.
- Корректное подключение хуков pre-commit (black/isort конфликтовали по форматированию импортов).

**Что повторить:**

- Pytest-фикстуры, клиентские тесты и маркеры.
- Dockerfile / Compose: различия dev ↔ prod.
- Git-workflow с rebase и конфликт-резолвом.

> Clockify: **~17 ч**
