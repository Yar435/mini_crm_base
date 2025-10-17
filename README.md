# 🧭 Mini CRM Base



![CI](https://github.com/Yar435/mini_crm_base/actions/workflows/ci.yml/badge.svg)
![Coverage](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/Yar435/your-gist-id/raw/coverage-badge.json)
[![CI](https://github.com/Yar435/mini_crm_base/actions/workflows/ci.yml/badge.svg?branch=develop)](https://github.com/Yar435/mini_crm_base/actions/workflows/ci.yml)



Учебно-разработческая база проекта **mini_crm_base** — Django + Django REST Framework, с докером, тестами и линтерами.
Предназначен как стартовая заготовка для GraphScope и других интеграций с amoCRM.

`mini_crm_base` — это технический фундамент для CRM-проектов, интегрирующихся с amoCRM и другими внешними сервисами (Tilda, Yclients, Wazzup и т.д.).
Проще говоря — это чистая база Django + DRF, на которой будут строиться будущие проекты вроде GraphScope или amo_backup, но без бизнес-логики, только с базовыми слоями: API, модели, тесты, инфраструктура, CI-проверки.
---

## 📁 Структура проекта
```
mini_crm_base/
│
├── .pre-commit-config.yaml # хуки (black, isort, flake8, end-of-file)
├── pyproject.toml # общая конфигурация black/isort/flake8/pytest
├── requirements.txt # прод-зависимости
├── requirements-dev.txt # dev/линтеры/pytest/debug-toolbar
├── docker-compose.yml # docker окружение (Postgres, Redis, web)
│
├── src/ # основной код приложения
│ ├── manage.py # Django CLI entrypoint
│ ├── config/ # конфигурация Django
│ │ ├── init.py
│ │ ├── asgi.py
│ │ ├── wsgi.py
│ │ ├── urls.py # маршруты проекта
│ │ └── settings/
│ │ │ ├── base.py # общие настройки
│ │ │ └── dev.py # dev-настройки (DB, debug_toolbar)
│ │
│ ├── clients/ # приложение клиентов
│ │ ├── models.py
│ │ ├── serializers.py
│ │ ├── views.py
│ │ └── admin.py
│ │
│ ├── deals/ # приложение сделок
│ │ ├── models.py
│ │ ├── serializers.py
│ │ ├── views.py
│ │ └── admin.py
│ │
│ ├── core/ # общие компоненты, utils, mixins и т.п.
│ └── tests/ # pytest-тесты (unit + integration)
│ └── test_smoke.py
│
├── .editorconfig
├── pass.txt
├── README.md
└── .env # локальные секреты и конфигурация окружения
```

---

## ⚙️ Локальный запуск

```bash
# установить зависимости
pip install -r requirements-dev.txt

# применить миграции
python src/manage.py migrate

# запустить сервер
python src/manage.py runserver
```

```bash
docker compose up -d

docker ps
```


---

## 🧩 Используемые пакеты

| Компонент | Назначение |
|---|---|
| `Django 4.2` | Базовый фреймворк |
| `Django REST Framework` | API и сериализация |
| `django-debug-toolbar` | Отладочная панель |
| `pytest / pytest-django` | Тестирование |
| `black / isort / flake8` | Стиль и статанализ |
| `pre-commit` | Авто-проверки при коммитах |
| `docker-compose` | Контейнеризация (Postgres, Redis, web) |


---
## 🧠 Принципы структуры

- src-layout: весь код внутри src/, чтобы избежать конфликтов имён при импортах.
- Модульность: каждое приложение изолировано (clients, deals, core).
- Настройки: делятся на base.py (общее) и dev.py (локальная разработка).
- Pre-commit hooks: гарантируют чистый код до каждого коммита.
- .env: хранит ключи, пароли, порты и др. чувствительные данные.

---

## 🧪 Тесты

```bash
pytest -q #из файла src/tests/test_smoke.py
```

Тесты используют временную БД и не влияют на данные разработки.

---

## 🧰 Отладка

- Django Debug Toolbar: доступен по адресу __debug__/
- Включение: DEBUG=True и "debug_toolbar" в INSTALLED_APPS

---

## 🚀 TODO / Roadmap

- Настроить Redis как брокер кэша / Celery (по проекту GraphScope)
- Добавить JWT-аутентификацию в API
- Подключить swagger/openapi схемы
- Подготовить демо-фронтенд для CRM-операций


## JWT авторизация

```
body = @{username="yar435"; password="4351"} | ConvertTo-Json
```
```
$resp = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/auth/token/" -Method POST -ContentType "application/json" -Body $body
```
 ```
 $resp | ConvertTo-Json -Depth 5
 ```
```
$access = $resp.access
```
```
 $headers = @{ Authorization = "Bearer $access" }

```
```
Invoke-RestMethod -Uri http://127.0.0.1:8000/api/clients/ -Headers $headers

```

## Spectacular
```
python manage.py spectacular --validate --fail-on-warn --file schema.yaml
```
