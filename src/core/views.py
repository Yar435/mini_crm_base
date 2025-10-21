from __future__ import annotations

import logging
from types import ModuleType
from typing import Optional

from django.db import transaction
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.metrics import health_hits_total
from core.models import UserSecurityProfile
from core.serializers import DetailResponseSerializer

from .request_id import get_request_id

try:
    import redis as _redis  # type: ignore[import-not-found]
except Exception:
    _redis = None

redis: Optional[ModuleType] = _redis

logger = logging.getLogger(__name__)


class HealthResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
    request_id = serializers.CharField(required=False, allow_null=True, allow_blank=True)


class ReadyChecksSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=["ok", "fail"])
    checks = serializers.DictField(child=serializers.CharField())


@extend_schema(
    methods=["GET"],
    tags=["System"],
    summary="Простой health-check",
    auth=None,
    responses={200: HealthResponseSerializer},
)
@api_view(["GET"])
@permission_classes([AllowAny])
def health(request):
    data = {
        "status": "ok",
        "request_id": get_request_id(),
    }
    return Response(data, status=status.HTTP_200_OK)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Auth"],
        summary="Выйти (инвалидировать токены)",
        description=(
            "Инкрементирует `token_version` и делает все старые токены недействительными."
        ),
        request=None,
        responses={200: DetailResponseSerializer},
    )
    def post(self, request):
        sec = getattr(request.user, "security", None)
        if sec is None:
            sec = UserSecurityProfile.objects.create(user=request.user)

        with transaction.atomic():
            sec.token_version += 1
            sec.save(update_fields=["token_version"])

        return Response({"detail": "logged out"})


class HealthView(APIView):
    authentication_classes = []
    permission_classes = []

    @extend_schema(
        tags=["System"],
        summary="Health (классическая вью)",
        auth=None,
        responses=OpenApiResponse(response=HealthResponseSerializer),
    )
    def get(self, request):
        health_hits_total.inc()
        return Response({"status": "ok"}, status=200)
