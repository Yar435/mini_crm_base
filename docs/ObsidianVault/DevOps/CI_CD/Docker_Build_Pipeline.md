# Docker Build Pipeline (план)

- Сборка prod-образа
- Прогон manage.py check + spectacular --validate внутри контейнера
- smoke-тест контейнера (curl /health)
- Push в registry (GitHub Container Registry / Docker Hub)
