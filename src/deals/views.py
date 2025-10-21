from drf_spectacular.utils import OpenApiExample, extend_schema, extend_schema_view
from rest_framework.viewsets import ModelViewSet

from core.permissions import HasModelPermission

from .models import Deal, Manager
from .serializers import DealSerializer, ManagerSerializer


@extend_schema_view(
    list=extend_schema(
        summary="Список сделок",
        description="Возвращает список сделок с фильтрацией и пагинацией.",
        tags=["Deals"],
        examples=[
            OpenApiExample(
                "Пример ответа",
                value={"count": 1, "results": [{"id": 1, "title": "Deal #1", "status": "new"}]},
            )
        ],
    ),
    retrieve=extend_schema(summary="Детали сделки", tags=["Deals"]),
    create=extend_schema(summary="Создать сделку", tags=["Deals"]),
    update=extend_schema(summary="Обновить сделку", tags=["Deals"]),
    partial_update=extend_schema(summary="Частично обновить сделку", tags=["Deals"]),
    destroy=extend_schema(summary="Удалить сделку", tags=["Deals"]),
)
class DealViewSet(ModelViewSet):
    queryset = (
        Deal.objects.select_related(
            "client",
            "manager",
        )
        .all()
        .order_by("-id")
    )
    serializer_class = DealSerializer
    permission_classes = [HasModelPermission]
    permission_model = Deal

    filterset_fields = ["status", "client", "manager"]
    search_fields = ["title", "client__name", "manager__name"]
    ordering_fields = ["id", "amount", "created_at", "status"]
    ordering = ["-id"]


@extend_schema_view(
    list=extend_schema(
        summary="Список менеджеров",
        description="Возвращает список менеджеров с фильтрацией и пагинацией.",
        tags=["Managers"],
        examples=[
            OpenApiExample(
                "Пример ответа (пагинация)",
                value={
                    "count": 1,
                    "next": None,
                    "previous": None,
                    "results": [
                        {
                            "id": 2,
                            "name": "Grisha",
                            "email": "griphone@rambler.ru",
                            "phone": "+76778765432",
                        }
                    ],
                },
            )
        ],
    ),
    retrieve=extend_schema(summary="Детали по менеджеру", tags=["Managers"]),
    create=extend_schema(
        summary="Создать менеджера",
        tags=["Managers"],
        examples=[
            OpenApiExample(
                "Пример запроса",
                value={"name": "Grisha", "email": "griphone@rambler.ru", "phone": "+7926..."},
            )
        ],
    ),
    update=extend_schema(summary="Обновить данные менеджера", tags=["Managers"]),
    partial_update=extend_schema(summary="Частично обновить данные менеджера", tags=["Managers"]),
    destroy=extend_schema(summary="Удалить менеджера", tags=["Managers"]),
)
class ManagerViewSet(ModelViewSet):
    queryset = Manager.objects.all().order_by("-id")
    serializer_class = ManagerSerializer
    permission_classes = [HasModelPermission]
    permission_model = Manager

    filterset_fields = ["name", "email"]
    search_fields = ["name", "email"]
    ordering_fields = ["id", "name", "created_at"]
    ordering = ["-id"]
