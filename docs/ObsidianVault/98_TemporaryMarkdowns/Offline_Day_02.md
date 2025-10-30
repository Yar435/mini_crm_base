# Offline_Day_02 — Checklist (mini_crm_base)

Цель дня: довести проект до стабильного состояния **после миграций**: админка и API работают, есть базовые тесты, код отформатирован, всё зафиксировано в Obsidian.

---

## 0) Разогрев среды (5–10 мин)
- [x] Открыть проект в **PyCharm** ✅ 2025-10-08
- [x] Активировать venv: ✅ 2025-10-08
```powershell
.\.venv\Scripts\Activate.ps1
```
- [x] Проверить, что **Docker** контейнеры запущены: ✅ 2025-10-08
```powershell
docker ps   # должны быть postgres и redis
```
- [x] Убедиться, что работа идёт из **src/** ✅ 2025-10-08
```powershell
cd src
```

## 1) Валидация структуры и настроек (10–15 мин)
- [x] Есть ли файл `src/config/settings/__init__.py` (даже пустой) ✅ 2025-10-08
- [x] В `src/manage.py`, `src/config/wsgi.py`, `src/config/asgi.py`: ✅ 2025-10-08
  - [x] `DJANGO_SETTINGS_MODULE=config.settings.dev` ✅ 2025-10-08
- [x] В `src/config/settings/dev.py`: ✅ 2025-10-08
  - [x] `from .base import *` ✅ 2025-10-08
  - [x] `INSTALLED_APPS` содержит `rest_framework`, `core`, `clients`, `deals` ✅ 2025-10-08
  - [x] Параметры БД читаются из `.env` ✅ 2025-10-08

Проверка:
```powershell
python manage.py check
```

## 2) Миграции и суперпользователь (10–15 мин)
- [x] Создать и применить миграции ✅ 2025-10-08
```powershell
python manage.py makemigrations
python manage.py migrate
```
- [x] Создать суперпользователя ✅ 2025-10-08
```powershell
python manage.py createsuperuser
```

## 3) Быстрый ручной прогон (15–20 мин)
- [x] Запустить сервер ✅ 2025-10-08
```powershell
python manage.py runserver
```
- [x] Зайти в админку и создать тестовые записи: ✅ 2025-10-08
  - [x] `Client` (2–3 шт) ✅ 2025-10-08
  - [x] `Manager` (1–2 шт) ✅ 2025-10-08
  - [x] `Deal` (связать с Client/Manager) ✅ 2025-10-08
- [x] Проверить API (в браузере/HTTP-клиенте): ✅ 2025-10-08
  - [x] GET `http://127.0.0.1:8000/api/clients/` ✅ 2025-10-08
  - [x] GET `http://127.0.0.1:8000/api/deals/` ✅ 2025-10-08

Пример POST (Deal):
```json
{
  "title": "Первый контракт",
  "amount": "15000.00",
  "status": "new",
  "client": 1,
  "manager": 1
}
```

## 4) Кодовая гигиена (15–25 мин)
- [x] Остановить сервер (`Ctrl+C`) и прогнать хуки: ✅ 2025-10-08
```powershell
pre-commit run --all-files
```
- [x] Добавить минимальные тесты: ✅ 2025-10-08
  - `src/tests/test_smoke.py`
```python
def test_smoke():
    assert 2 + 2 == 4
```
  - `src/tests/test_models.py` (проверка создания Client)
```python
import pytest
from clients.models import Client

@pytest.mark.django_db
def test_create_client():
    c = Client.objects.create(name="Test", email="t@example.com")
    assert c.id is not None
```
- [x] Запустить тесты: ✅ 2025-10-08
```powershell
pytest -q
```

## 5) (Опционально) Инструменты разработчика (10–15 мин)
*(Только если пакеты уже установлены заранее — без интернета новые не ставим)*
- [x] Включить `django-debug-toolbar` в `dev.py` и добавить в `urls.py` ✅ 2025-10-08
- [x] Посмотреть SQL в списке `Deal` и убедиться, что `select_related("client","manager")` работает ✅ 2025-10-08

## 6) Документация/журнал в Obsidian (10–20 мин)
- [x] Открыть `01_Journal/Daily/` → Заполнить за сегодня: ✅ 2025-10-08
  - [x] «Фокус дня» ✅ 2025-10-08
  - [x] «Сделано» — перечислить чекпоинты ✅ 2025-10-08
  - [x] «Проблемы/блокеры» ✅ 2025-10-08
  - [x] «Идеи/заметки» ✅ 2025-10-08
- [x] В `00_Roadmap/Week_01.md` → отметь выполненные пункты в **Задания** ✅ 2025-10-08
- [x] Добавить в `README.md` проекта: ✅ 2025-10-08
  - [x] Краткое описание ✅ 2025-10-08
  - [x] Как запустить локально (venv, docker, миграции) ✅ 2025-10-08
  - [x] Эндпоинты API ✅ 2025-10-08

## 7) Коммиты и финальный контроль (5–10 мин)
```powershell
git add .
pre-commit run --all-files
git commit -m "feat: base models/admin, REST endpoints, migrations; docs & tests"
```

---

## Если встрял (быстрые проверки)
- `ModuleNotFoundError: config.settings.dev` → проверь `src` как **Sources Root** и наличие `config/settings/__init__.py`
- `psycopg` не коннектится → `docker ps`, `.env` (хост/порт/логин), `POSTGRES_HOST=localhost`, порт 5432
- DRF импорт ругается → `INSTALLED_APPS` и `rest_framework` в dev.py
- IDE не видит импорты, но runtime ок → File → *Invalidate Caches / Restart*

---

### Мини-цели на завтра
- [ ] Добавить фильтрацию/пагинацию в DRF
- [ ] Подключить JWT/permissions (через simplejwt)
- [ ] Начать писать интеграционные тесты API (pytest + APIClient/httpx)
