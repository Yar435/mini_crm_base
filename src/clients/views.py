from rest_framework.viewsets import ModelViewSet

from .models import Client
from .serializers import ClientSerializer


class ClientViewSet(ModelViewSet):
    queryset = Client.objects.all().order_by("-id")
    serializer_class = ClientSerializer

    # точные поля для filter=? (django-filter)
    filterset_fields = ["name", "email"]

    # полнотекстовый поиск: ?search=...
    search_fields = ["name", "email"]

    # сортировка: ?ordering=... (поддерживает - поле)
    ordering_fields = ["id", "name", "created_at"]
    ordering = ["-id"]  # значение по умолчанию
