# Инкрементальная синхронизация с amoCRM API

Первичная заливка истории выполняется из снимков SQLite (`Blondon_memory`, `RAW_MEM`) командами `sync_amo_transitions` и `sync_amo_entities`. Для актуальных данных без полного пересканирования дампа используйте API amoCRM поверх уже загруженного состояния.

## Принцип

1. **Сущности** (leads, tasks, contacts, …): периодический опрос с фильтром `updated_at` (или эквивалент в версии API), хранение максимального `updated_at` / курсора в таблице состояния синка (отдельная модель `AmoSyncState` или JSON в Redis).
2. **События / переходы**: поток `events` с `created_at` больше последнего сохранённого watermark; для `lead_transitions` — либо пересборка через `transition.py` по новым событиям, либо инкрементальная вставка из распарсенных событий смены статуса.
3. **Идемпотентность**: те же ключи, что и при батч-импорте (`event_id` для переходов, `id` для лидов/задач, уникальный ключ для связей).

## Рекомендуемый порядок внедрения

| Шаг | Действие |
| --- | --- |
| 1 | Завершить первичный импорт из `RAW_MEM` в PostgreSQL (`sync_amo_transitions`, `sync_amo_entities`). |
| 2 | Сверка объёмов: `python manage.py verify_amo_sync --raw-mem` (или без `--raw-mem` для копии в `Blondon_memory/`). Флаг `--fail-on-mismatch` завершает процесс с кодом 1 при расхождении. |
| 3 | Модель состояния синка: `AmoSyncState` (ключ `leads`, поле `watermark_updated_at`). |
| 4 | Клиент amoCRM: [`src/analytics/amocrm_client.py`](../src/analytics/amocrm_client.py) (список лидов с `filter[updated_at][from]`). Переменные окружения: `AMOCRM_SUBDOMAIN`, `AMOCRM_ACCESS_TOKEN`. |
| 5 | Ручной запуск: `python manage.py sync_amo_leads_incremental`. Celery: задача `analytics.tasks.incremental_sync_leads` (beat раз в 15 минут в [`base.py`](../src/config/settings/base.py)); без токена задача возвращает `skipped:no-credentials`. |
| 6 | После стабилизации — не полагаться на локальные `.db` в рантайме API. |

### Дополнительные read-only API (аналитика)

- `GET /api/analytics/pipeline-funnel/?pipeline_id=` — счётчики лидов по статусам (текущий снимок `AmoLead`).
- `GET /api/analytics/transitions-by-user/?pipeline_id=&from_ts=&to_ts=` — агрегат переходов по `by_user` за интервал.

## Наблюдаемость и алерты

- Метрика `analytics_process_graph_build_seconds` (Prometheus histogram) отражает время построения графа при промахе кэша. Имеет смысл алертить на **p95 / p99** выше порога (например 5–10 с) при ожидаемом объёме данных.
- Очередь Celery и длительность задачи `rebuild_graph_snapshots` — контролировать через существующий стек (broker Redis, экспорт метрик воркеров при необходимости).
- При росте таблицы `amo_lead_transitions` рассмотреть **партиционирование по `at`** (месяц/квартал) в PostgreSQL до перехода на отдельное колоночное хранилище.

## Ссылки на код

- Контракт query-параметров: [`src/analytics/api_contract.py`](../src/analytics/api_contract.py)
- Ключи кэша графа: [`src/analytics/cache_keys.py`](../src/analytics/cache_keys.py)
- Импорт сущностей из дампа: `python manage.py sync_amo_entities` ([`src/analytics/management/commands/sync_amo_entities.py`](../src/analytics/management/commands/sync_amo_entities.py))
- Сверка SQLite vs Postgres: [`src/analytics/management/commands/verify_amo_sync.py`](../src/analytics/management/commands/verify_amo_sync.py)
- Инкремент лидов: [`src/analytics/services/incremental_leads_sync.py`](../src/analytics/services/incremental_leads_sync.py)
