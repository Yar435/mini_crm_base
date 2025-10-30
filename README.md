[![Build](https://github.com/Yar435/mini_crm_base/actions/workflows/ci.yml/badge.svg)](https://github.com/Yar435/mini_crm_base/actions/workflows/ci.yml)
[![Coverage Status](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/Yar435/e717d3682a0aef086b4a673a8683c47a/raw/coverage.json)](https://github.com/Yar435/mini_crm_base/actions)
[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)]()
[![Django](https://img.shields.io/badge/Django-5.0+-green.svg)]()
[![License](https://img.shields.io/badge/license-MIT-lightgrey.svg)](LICENSE)

# Mini CRM Base

Backend-шаблон для учебных и продовых CRM‑проектов: Django 5 + DRF, Celery, PostgreSQL, Redis, Prometheus/Grafana и готовые пайплайны CI. Репозиторий задуман как фундамент для интеграций (GraphScope, amo_backup и др.), поэтому содержит минимально необходимую бизнес-логику и максимум инфраструктуры.

---

## 📦 Что внутри

- **Django 5 / DRF** — API, модели и административный интерфейс.
- **JWT (SimpleJWT)** — аутентификация, кастомный сериализатор с `token_version`.
- **RBAC-заготовка** — базовые пермишены, `setup_rbac` management-команда.
- **Celery + Beat + Flower** — асинхронные задачи, heartbeat и мониторинг очередей.
- **PostgreSQL + Redis** — боевой стек для прод-запуска и CI.
- **Prometheus + Grafana + celery-exporter** — метрики приложения и воркеров.
- **nginx** — реверс-прокси и отдача статики в прод-стеке.
- **Pytest + coverage** — тесты, отчёты, GitHub Actions (postgres + makemigrations --check).
- **Black / isort / flake8 / mypy / bandit / safety** — линтеры и статический анализ.
- **Документация** — OpenAPI (drf-spectacular), README, Obsidian vault с заметками.

---

## 🗂️ Структура

```
mini_crm_base/
├── src/
│   ├── manage.py
│   ├── config/            # настройки Django (base/dev/prod/test + URLs, celery)
│   ├── core/              # общие компоненты: auth, permissions, metrics, ready и т.д.
│   ├── clients/, deals/   # примерные доменные приложения
│   └── tests/             # pytest
├── ops/docker/            # продовый compose, entrypoint, nginx.conf, prometheus.yml
├── docker-compose.yml     # локальный «разработческий» стек
├── Dockerfile             # multi-stage: builder + runtime (uvicorn ASGI)
├── requirements*.txt      # зависитимости (prod/dev)
├── .github/workflows/ci.yml
├── .env.example           # пример окружения
└── docs/ObsidianVault/    # рабочие заметки (избранные папки в git)
```

---

## 🚀 Быстрый старт

### 1. Клонируем и настраиваем окружение

```bash
git clone https://github.com/Yar435/mini_crm_base.git
cd mini_crm_base

cp .env.example .env
cp .env.example .env.prod   # или заполните вручную
```

### 2. Локальная разработка (Docker Compose)

```bash
# web + postgres + redis + celery + beat + flower + prometheus + grafana
docker compose up --build
```

После старта доступны:

| URL | Назначение |
| --- | ---------- |
| http://localhost/ready | readiness (Postgres + Redis) |
| http://localhost/health | liveness (без внешних зависимостей) |
| http://localhost/api/docs/ | Swagger UI |
| http://localhost/api/redoc/ | ReDoc |
| http://localhost/metrics | Django Prometheus |
| http://localhost:5555 | Flower |
| http://localhost:9090 | Prometheus |
| http://localhost:3000 | Grafана (логин/пароль: admin / admin) |

> Если IP контейнера `web` поменялся (после `--force-recreate`), перезапустите `nginx`, чтобы он переподхватил новый адрес:
> `docker compose restart web nginx`

### 3. Прод-стек (с nginx и entrypoint-скриптом)

```bash
docker compose -f ops/docker/compose.prod.yml up --build

# Проверка
curl http://localhost/ready
curl http://localhost/health
```

В этом варианте web, celery, beat и flower собираются из одного Dockerfile (`target: prod`), а `entrypoint.sh` сам запускает `migrate → setup_rbac → collectstatic`, прежде чем стартовать Uvicorn/Celery.

### 4. Без Docker (pure Python)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
pip install -r requirements.txt

export DJANGO_SETTINGS_MODULE=config.settings.dev
python src/manage.py migrate
python src/manage.py runserver
```

---

## ⚙️ Переменные окружения

Основные настройки (см. `.env.example`):

| Переменная | По умолчанию | Описание |
| --- | --- | --- |
| `DJANGO_SECRET_KEY` | `change-me` | секрет Django |
| `DJANGO_SETTINGS_MODULE` | `config.settings.prod` | модуль настроек |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1,web,nginx` | список хостов |
| `POSTGRES_*` | см. `.env.example` | параметры базы |
| `REDIS_URL` | `redis://redis:6379/0` | Redis для кэша и Celery |
| `CELERY_BROKER_URL` | `REDIS_URL` | брокер очереди |
| `CELERY_RESULT_BACKEND` | `REDIS_URL` | backend Celery |
| `FLOWER_BROKER_URL` | `CELERY_BROKER_URL` | broker для Flower |
| `SECURE_SSL_REDIRECT` | `0` (локально) | редирект на https в prod |
| `SENTRY_*` | пусто | заготовки под интеграцию (код пока не инициализирует SDK) |

---

## 🧪 Тесты и качество

```bash
pytest -q --maxfail=1 --disable-warnings
```

CI (GitHub Actions):

- поднимает postgres-сервис,
- накатывает миграции,
- гоняет тесты,
- проверяет, что `makemigrations --check` ничего не генерирует.

Дополнительные утилиты:

```bash
pytest --cov=src                # покрытие
mypy                            # статическая типизация
bandit -r src                   # security lint
safety check                    # CVE в зависимостях
python src/manage.py spectacular --validate --fail-on-warn --file src/schema.yaml
```

---

## 🛠️ Management-команды и полезные скрипты

- `python src/manage.py setup_rbac` — первичная настройка групп/ролей.
- `python src/manage.py createsuperuser` — администратор.
- `python src/manage.py spectacular ...` — генерация OpenAPI схемы.
- `docker compose exec web python src/manage.py shell` — интерактивная консоль.
- `ops/docker/entrypoint.sh` — migrate → setup_rbac → collectstatic → запуск.

Celery heartbeat-таска (`core.tasks.heartbeat`) пишет тик в Redis и лог для проверки доступности beat.

---

## 📚 Полезные ссылки

- **OpenAPI**: `src/schema.yaml`
- **Obsidian**: `docs/ObsidianVault/` (разделено на roadmaps, словари, чек-листы). Личные журналы и временные файлы исключены из VCS.
- **Coverage badge gist**: обновляется CI (`.github/workflows/ci.yml`).

---

## 📌 Roadmap / TODO

- Вынести dev-инструменты в отдельный compose (`docker-compose.dev.yml`).
- Настроить автогенерацию Sentry release / environment и включить SDK.
- Добавить smoke-тесты для `/ready` и метрик в CI.
- Подготовить практические гайды по GraphScope/amoCRM интеграциям.
- Подключить pre-commit (hook definition в `pyproject.toml` уже готов).

---

## 🧾 Лицензия

MIT — см. `LICENSE`.

---

Проект развивается как база знаний и стартовый шаблон. Если что-то не заводится или хочется обсудить расширения — создавайте issue или пишите в заметках (`docs/ObsidianVault/03_Checklists/Code_Review_Checklist.md`). Удачной разработки! 🚀
