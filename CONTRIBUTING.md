# Contributing

## Быстрый старт (dev)
```bash
# локально
python -m venv venv && source venv/bin/activate  # (Windows: venv\Scripts\activate)
pip install -r requirements-dev.txt
cp .env.sample .env  # при необходимости, проверь переменные
python src/manage.py migrate
python src/manage.py runserver
```
```bash
# docker
docker compose up --build
# web: http://localhost:8000, swagger: /api/docs, metrics: /metrics
```
## Тесты и стиль
```bash
Копировать код
pytest -q               # тесты
pre-commit install
pre-commit run -a       # формат/линт
```
## Ветки и PR
`main`— стабильная; `develop` — активная разработка.

Фичи — от `develop`: `feature/<name>`

Перед PR: `pre-commit run -a`, `pytest -q`.
