# PyCharm Setup — 07.10.2025

## 1) Интерпретатор и venv
1. File → Settings → Project → Python Interpreter → Add → Existing → выбери `./.venv` (или создай там же).
2. Открой терминал PyCharm и выполни:
   ```powershell
   .\scripts\init_venv.ps1
   ```

## 2) Форматирование и линтинг
- File → Settings → Tools → Actions on Save:
  - ✅ Run Black
  - ✅ Optimize imports (isort)
- File → Settings → Python Integrated Tools:
  - Default test runner: **pytest**
- File → Settings → Editor → Code Style → Python:
  - Hard wrap at 100

## 3) Pre-commit
- В терминале:
  ```powershell
  pre-commit install
  pre-commit run --all-files
  ```

## 4) Конфигурации запуска (Run/Debug)
### Django (если проект Django)
- Run/Debug Configurations → + → Django Server →
  - Host: 127.0.0.1
  - Port: 8000
  - Environment variables: загрузить из `.env` (через плагин EnvFile) или выставить вручную.

### Pytest
- Run/Debug Configurations → + → pytest →
  - Working directory: корень проекта
  - Additional Arguments: `-q`
  - Environment: `PYTHONPATH=.`

## 5) Docker (БД и Redis)
- В отдельном терминале:
  ```powershell
  docker compose up -d
  ```
- Проверь доступность:
  - Postgres: localhost:5432
  - Redis: localhost:6379

## 6) Полезные плагины PyCharm
- .env files support (или EnvFile)
- Rainbow Brackets
- String Manipulation
- Key Promoter X
