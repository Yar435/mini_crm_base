from drf_spectacular.utils import (
    OpenApiExample,
    extend_schema,
    extend_schema_view,
)
from rest_framework.viewsets import ModelViewSet

from .models import Client
from .serializers import ClientSerializer


@extend_schema_view(
    list=extend_schema(
        summary="Список клиентов",
        description="Возвращает список клиентов с фильтрацией и пагинацией.",
        tags=["Clients"],
        examples=[
            OpenApiExample(
                "Пример ответа (пагинация)",
                value={
                    "count": 1,
                    "next": None,
                    "previous": None,
                    "results": [
                        {
                            "id": 1,
                            "name": "Boba",
                            "email": "boba@example.com",
                            "phone": "+79264444731",
                            "created_at": "2025-10-08T08:28:27.764444Z",
                        }
                    ],
                },
            )
        ],
    ),
    retrieve=extend_schema(summary="Детали клиента", tags=["Clients"]),
    create=extend_schema(
        summary="Создать клиента",
        tags=["Clients"],
        examples=[
            OpenApiExample(
                "Пример запроса",
                value={
                    "name": "Boba",
                    "email": "boba@example.com",
                    "phone": "+7926...",
                },
            )
        ],
    ),
    update=extend_schema(summary="Обновить данные клиента", tags=["Clients"]),
    partial_update=extend_schema(
        summary="Частично обновить данные клиента",
        tags=["Clients"],
    ),
    destroy=extend_schema(summary="Удалить клиента", tags=["Clients"]),
)
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
