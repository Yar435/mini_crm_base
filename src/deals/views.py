from rest_framework.viewsets import ModelViewSet

from .models import Deal, Manager
from .serializers import DealSerializer, ManagerSerializer


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

    filterset_fields = ["status", "client", "manager"]
    search_fields = ["title", "client__name", "manager__name"]
    ordering_fields = ["id", "amount", "created_at", "status"]
    ordering = ["-id"]


class ManagerViewSet(ModelViewSet):
    queryset = Manager.objects.all().order_by("-id")
    serializer_class = ManagerSerializer
    filterset_fields = ["name", "email"]
    search_fields = ["name", "email"]
    ordering_fields = ["id", "name", "created_at"]
    ordering = ["-id"]
