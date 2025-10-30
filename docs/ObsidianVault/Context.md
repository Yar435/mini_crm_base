## 🧩 Контекст разработчика

**Имя:** Ярослав
**Роль:** Python fullstack / Django backend developer (Junior → Middle+)
**Цель:** Развитие backend-навыков через проект *mini_crm_base* (Django + DRF + JWT + Docker + CI/CD).
**Рабочая среда:** Windows 10, PyCharm, Obsidian (vault для теории и journaling), Clockify (учёт времени).

---

## 💻 Проект: mini_crm_base

**Описание:**
Учебно-практический CRM backend на Django 4.2, ориентированный на связку с внешними CRM (amoCRM, Yclients).
Фокус — чистая архитектура, тестирование, документация и инфраструктура (Docker, pre-commit, CI/CD).

**Текущее состояние:**
- ✅ Django/DRF структура по src-layout (`config/`, `core/`, `clients/`, `deals/`)
- ✅ CRUD API на DRF (Deal, Client, Manager)
- ✅ Фильтрация, пагинация, поиск, сортировка (`django-filter`)
- ✅ JWT-аутентификация (`djangorestframework-simplejwt`)
- ✅ Permissions: `IsAuthenticatedOrReadOnly`
- ✅ Автотесты API (`pytest-django`, `APIClient`)
- ✅ pre-commit (black, isort, flake8, hooks настроены)
- ✅ Docker Desktop работает (готов `docker compose up`)
- ⚙️ dev/prod настройки (`config/settings/base.py`, `dev.py`)
- 🔧 подключен `django-debug-toolbar`
- 🧠 ведётся параллельный `Obsidian Vault` (структура Django / DevOps / Git / Docker / Precommit)

---

## 📅 Текущие задачи (Week_02)

**Технический фокус:**
1. Подключить Swagger / Redoc через `drf-spectacular`
2. Настроить coverage отчёты в pytest (`--cov=src`)
3. Продолжить систематизацию DevOps-знаний:
   - Git: workflows, rebase, конфликт-резолв
   - Docker: контейнеризация и compose
   - Pre-commit: хуки и автоформатирование
4. Подготовить Git-визуализацию и документацию (Git-vault)

**Следующие шаги после Week_02:**
- Добавить Celery + Redis для фоновых задач
- Ввести CI/CD pipeline
- Подключить swagger-декорации и документацию моделей

---

## 🧭 Структура Obsidian Vault

```
Obsidian Vault
├── 00_Roadmap
│   ├── Roadmap_Overview.md
│   ├── Week_01.md
│   ├── Week_02.md
│   ├── Week_03.md
│   └── ... (27 file(s) hidden)
├── 01_Journal
│   ├── Daily
│   │   ├── 2025-10-07.md
│   │   ├── 2025-10-08.md
│   │   └── 2025-10-09.md
│   └── Weekly
├── 02_Projects
│   ├── amo_backup
│   │   └── README.md
│   └── graphscope
│       └── README.md
├── 03_Checklists
│   ├── Code_Review_Checklist.md
│   ├── Deploy_Checklist.md
│   ├── Interview_Prep_Checklist.md
│   └── Testing_Checklist.md
├── 04_Resources
│   ├── Environment_Notes.md
│   └── Useful_Links.md
├── 98_TemporaryMarkdowns
│   ├── Offline_Day_02.md
│   └── Offline_Day_02_Extra.md
├── 99_Templates
│   ├── Daily_Journal_Template.md
│   ├── Learning_Note_Template.md
│   ├── Project_Plan_Template.md
│   └── Weekly_Review_Template.md
├── DevOps
│   ├── CI_CD
│   │   ├── Docker_Build_Pipeline.md
│   │   ├── GitHub_Actions.md
│   │   └── GitLab_CI.md
│   ├── Docker
│   │   ├── Docker_Basic.md
│   │   ├── Docker_Compose.md
│   │   ├── Docker_Debugging.md
│   │   └── Docker_Images_and_Networks.md
│   ├── Git
│   │   ├── Git_Advanced.md
│   │   ├── Git_Basic.md
│   │   ├── Git_Debugging.md
│   │   └── Git_Workflows.md
│   ├── PreCommit
│   │   ├── Black_Isort_Flake8.md
│   │   ├── Precommit_Debug.md
│   │   └── Precommit_Hooks.md
│   └── Notes_Index.md
├── Django
│   ├── Концепции
│   │   └── Структура изучения.md
│   ├── Практика
│   ├── Словарь
│   │   ├── JWT-токен.md
│   │   ├── Миксин.md
│   │   ├── Пагинация.md
│   │   └── Фильтрация.md
│   ├── Теория
│   └── Индекс.md
├── Context.md
├── Home.md
└── README.md

```

---

## 🧠 Ментальная модель проекта

- Django REST API — основа CRM-логики
- JWT → безопасная авторизация без сессий
- pytest → проверка API и интеграции
- pre-commit → контроль качества и единый стиль
- Docker → изоляция окружения и будущий деплой
- Obsidian → центр знаний и планирования

---

## ✅ Запрос при старте
> “Продолжай с текущего контекста mini_crm_base (JWT, DRF, Docker, pre-commit, Obsidian).
> Следующий шаг — работа над Week_03 (Swagger, coverage, DevOps docs).”
