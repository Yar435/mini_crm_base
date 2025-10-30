# Coverage & CI — mini_crm_base

## Coverage
- Pytest + pytest-cov → coverage.xml (93%)
- Порог установлен через pytest.ini (fail_under=70)
- Форматы отчётов:
  - term-missing
  - xml: coverage.xml (используется CI)
- Генерация:
  ```bash
  pytest --cov=src --cov-report=term-missing --cov-report=xml:coverage.xml
```


## CI (GitHub Actions)

- Файл: `.github/workflows/ci.yml`
- Проверки:
    1. spectacular --validate --fail-on-warn
    2. pytest (с coverage)
    3. upload artifacts → schema.yaml, coverage.xml
- Python 3.11, Ubuntu latest
- Дополнительно: можно добавить pre-commit check, docker build, smoke test
- Badge coverage можно добавить позже через Codecov
