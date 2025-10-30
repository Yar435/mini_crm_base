# GitHub Actions — mini_crm_base

- Цель: валидация схемы OpenAPI, прогоны тестов и сбор артефактов (coverage.xml, schema.yaml)
- Файл: .github/workflows/ci.yml
- Точки контроля:
  - ✅ spectacular --validate --fail-on-warn
  - ✅ pytest (порог fail_under=70% через .coveragerc)
  - ✅ upload-artifact: coverage.xml, src/schema.yaml
- Расширения (позже):
  - Бейдж покрытия
  - Линтер (pre-commit.ci или шаг flake8/black --check)
  - Docker build & push
