
# 🏠 Home

> Быстрые ссылки: [[00_Roadmap/Roadmap_Overview]] ·

## 🎯 Roadmap — ближайшие задачи
```dataview
TASK
FROM "00_Roadmap"
WHERE !completed
SORT file.name asc
LIMIT 5
```
## 📝 Журнал — последние записи

```dataview
TABLE file.mtime as "Обновлено"
FROM "01_Journal"
SORT file.mtime desc
LIMIT 7
```

## 🔄 Недавние изменения (весь вольт)

```dataview
TABLE file.mtime as "Обновлено"
FROM ""
SORT file.mtime desc
LIMIT 5
```

# 1) Быстрые горячие клавиши (Hotkeys)
Settings → **Hotkeys** (предложение):
- Open daily note (Periodic Notes): `Alt+D`
- Open weekly note (Periodic Notes): `Alt+W`
- Insert template: `Alt+T`
- Toggle Calendar: `Alt+C`
- Quick switcher: `Ctrl+O` (по умолчанию)
- New note: `Ctrl+N`

# 2) Как работать ежедневно (короткий ритуал)
1) `Alt+D` — открыть дневную заметку → заполнить “Фокус дня”.
2) Открыть `Home.md` → блок **Roadmap — ближайшие задачи** → выбрать 2–3 задачи на день.
3) Вести время в Clockify (проекты: `amo_backup`, `graphscope`; теги: `coding`/`testing`/`devops`/`docs`).
4) В конце дня — чекбоксы, «Сделано», «Блокеры» → 2–3 строки ретро.
5) В конце недели `Alt+W` — Weekly Review: итоги, что улучшить, план на следующую неделю.

# 3) Мини-тюнинг под PyCharm
В PyCharm:
- Включи **Black** + **isort** + **Flake8**.
- Создай Run/Debug конфигурации для Django и pytest.
- Для проектов в вольте держи рядом соответствующие репозитории Git (README в `02_Projects/*/README.md` можно синкать с реальными репами).




# Структура в схемах:
##  Уровень 1 — сервисы / контейнеры

```mermaid
flowchart LR
    subgraph Client["Клиент (браузер / API клиент)"]
        U["/api/..."]
        D[Swagger / Redoc<br> /api/docs · /api/redoc]
    end

    subgraph Compose["Docker Compose сеть"]
        WEB[Web: Django + Gunicorn<br/>container: web:8000]
        DB[(Postgres<br/>container: db:5432)]
        REDIS[(Redis<br/>container: redis:6379)]
        WORKER[Celery Worker<br/>container: worker]
        BEAT[Celery Beat<br/>container: beat]
    end

    U -->|HTTP| WEB
    D -->|HTTP| WEB

    WEB -->|ORM| DB
    WEB -->|JWT auth<br/>DRF| WEB

    WEB -->|enqueue task<br/>CELERY_BROKER_URL| REDIS
    BEAT -->|schedule tasks| REDIS
    WORKER -->|consume tasks| REDIS
    WORKER -->|при необходимости| DB

    classDef svc fill:#0ea5e9,stroke:#0369a1,color:#fff
    classDef store fill:#f59e0b,stroke:#b45309,color:#fff
    classDef ctrl fill:#22c55e,stroke:#15803d,color:#fff
    class WEB svc
    class WORKER,BEAT ctrl
    class DB,REDIS store
```

---

### Последовательность — синхронный запрос API


```mermaid
sequenceDiagram
    participant C as Client
    participant W as Web (Django/Gunicorn)
    participant P as Postgres
    Note over C,W: Пример: GET /api/clients/
    C->>W: HTTP GET /api/clients/
    W->>W: DRF ViewSet + Permissions + Pagination
    W->>P: ORM Query
    P-->>W: Rows
    W-->>C: 200 OK + JSON (count, results[])

```


---

### Последовательность — отложенная задача Celery

```mermaid
sequenceDiagram
    participant C as Client
    participant W as Web (Django)
    participant R as Redis (Broker)
    participant WK as Celery Worker
    participant P as Postgres

    Note over C,W: Пример: POST /api/deals/ (создание сделки)
    C->>W: HTTP POST /api/deals/
    W->>P: ORM INSERT (Deal)
    W->>R: debug_task.delay({...})
    W-->>C: 201 Created (task_id=...)
    R-->>WK: доставляет задачу из очереди "celery"
    WK->>W: импортирует код (autodiscover_tasks)
    WK->>P: (опционально) читает/пишет данные
    WK-->>R: пишет результат (result backend)
```


---

## Уровень 2 — структура проекта / ключевые файлы

```mermaid
flowchart TB
  subgraph SRC["src"]
    subgraph CONFIG["config/"]
      A[asgi.py]
      W[wsgi.py]
      U[urls.py]
      I[__init__.py – exports celery_app]
      subgraph SETTINGS["settings/"]
        B[base.py]
        D[dev.py]
        PR[prod.py]
      end
      C[celery.py]
    end

    subgraph CORE["core/"]
      CV[views.py – health, queue_test]
      CT[tasks.py – debug_task, heartbeat]
      CP[pagination.py]
      CM[models.py]
    end

    subgraph CLIENTS["clients/"]
      CLM[models.py]
      CLS[serializers.py]
      CLV[views.py]
    end

    subgraph DEALS["deals/"]
      DM[models.py]
      DS[serializers.py]
      DV[views.py]
    end

    M[manage.py]
    S[schema.yaml]
  end

  subgraph ROOT["repo root"]
    DC[Dockerfile – multi-stage]
    EN[.env / .env.prod]
    COM[docker-compose.yml]
    EP[entrypoint.sh]
    GHA[GitHub Actions workflow]
    PC[.pre-commit-config.yaml]
    PJI[pytest.ini]
    REQ[requirements-dev.txt]
  end

  %% Links between real nodes (no arrows to subgraph names)
  M --> SETTINGS
  M --> W
  W --> SETTINGS
  A --> SETTINGS
  I --> C
  C --> SETTINGS
  U --> CORE
  U --> CLIENTS
  U --> DEALS
  CORE --> SETTINGS
  CLIENTS --> SETTINGS
  DEALS --> SETTINGS
  CT --> C
  I --> C

  COM --> DC
  COM --> EN
  EP --> DC
  GHA --> S
  GHA --> PJI
  GHA --> REQ

  classDef code fill:#6366f1,stroke:#3730a3,color:#fff
  classDef infra fill:#16a34a,stroke:#166534,color:#fff
  classDef cfg fill:#0ea5e9,stroke:#075985,color:#fff

  class A,W,U,I,B,D,PR,C,CORE,CLIENTS,DEALS,M,S,CLM,CLS,CLV,DM,DS,DV,CV,CT,CP,CM code
  class DC,COM,EP,EN infra
  class GHA,PC,PJI,REQ cfg

```

---

### Пайплайн CI/CD (нынешний)

```mermaid
flowchart LR
  A[Push or PR] --> B[GitHub Actions CI]
  B --> C[OpenAPI validate]
  B --> D[Pytest + coverage]
  B --> E[Upload artifacts: schema.xml + coverage.xml]

  %% future steps
  E --> F[Docker build]
  F --> G[Container registry]
  G --> H[Deploy – manual or auto]

  classDef step fill:#94a3b8,stroke:#475569,color:#fff
  class A,B,C,D,E,F,G,H step

```



```mehrmaid
graph LR
T1 --> T2 & T3 --> T4 & T5 --> T6

T1("![|100x100](https://upload.wikimedia.org/wikipedia/commons/thumb/1/10/2023_Obsidian_logo.svg/1024px-2023_Obsidian_logo.svg.png)")
T2("$\nabla_\theta \mathbb{E}_{\tau\sim p_\theta}[R(\tau)]x$")
T3("| First Name | Last Name |
| ---------- | --------- |
| Doug       | Engelbart |")
T4("#plugins/mehrmaid")
T5("[[mehrmaid]]")
T6("![|80](https://upload.wikimedia.org/wikipedia/commons/thumb/6/60/Obsidian_software_logo.svg/1297px-Obsidian_software_logo.svg.png)")
```
