# Проект: amo_backup

## Цель
Резервное копирование данных amoCRM и длительное хранение с метаданными для аналитики.

## Технологии
- Python, Django, Celery, PostgreSQL, Redis, Docker
- OAuth2 для доступа к amoCRM API

## Основные задачи
- [ ] Авторизация по OAuth2
- [ ] Сбор данных (leads, contacts, companies)
- [ ] Хранение и обновление данных в PostgreSQL
- [ ] Планировщик (Celery beat)
- [ ] Экспорт для аналитики (CSV/Parquet)

## Примечания
Использовать проект как площадку для практики Celery, Redis и ORM оптимизации.
