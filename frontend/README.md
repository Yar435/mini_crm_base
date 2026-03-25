# Аналитика (локальный фронт)

Стек: Vite + React + TypeScript + Tailwind CSS + [@xyflow/react](https://reactflow.dev/). Запросы к API идут на тот же origin, что и dev-сервер Vite; прокси пересылает `/api` на Django (CORS не нужен).

## Требования

- Node.js 18+ и npm
- Запущенный бэкенд Django (по умолчанию `http://127.0.0.1:8000`)

## Запуск

**Терминал 1 — Django** (из каталога `mini_crm_base/src`):

```powershell
cd path\to\mini_crm_base\src
$env:DJANGO_SETTINGS_MODULE="config.settings.dev"
py -3.11 manage.py runserver 0.0.0.0:8000
```

Если вы уже в каталоге `frontend`, можно: `cd ../src` и затем команды выше.

При другом порте задайте переменную **`VITE_PROXY_TARGET`** (см. ниже).

**Терминал 2 — фронт:**

```powershell
cd frontend
npm install
npm run dev
```

Откройте в браузере адрес, который выведет Vite (обычно `http://localhost:5173`). Войдите пользователем Django; откроется экран графа процессов (`GET /api/analytics/process-graph/`).

### Прокси на другой порт бэкенда

Скопируйте `.env.example` в `.env` и укажите, например:

```env
VITE_PROXY_TARGET=http://127.0.0.1:8002
```

Перезапустите `npm run dev`.

## Сборка production-артефакта (локально)

```powershell
npm run build
```

Каталог `dist/` — статика; раздача в проде не входит в текущий scope.

## Ограничения

- На `/api/auth/token/` действует rate limit (5 запросов в минуту с одного IP) — не спамьте логином при отладке.
