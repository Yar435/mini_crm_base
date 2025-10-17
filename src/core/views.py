from __future__ import annotations

from django.conf import settings
from django.db import connections, transaction
from django.http import JsonResponse
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.metrics import health_hits_total
from core.models import UserSecurityProfile
from core.serializers import DetailResponseSerializer

try:
    import redis  # type: ignore
except Exception:
    redis = None


def health(request):
    """
    Shallow health: всегда 200 OK, без внешних зависимостей.
    Нужен для тестов/балансировщиков типа "жив ли процесс".
    """
    return JsonResponse({"status": "ok"}, status=200)


def ready(request):
    """
    Deep health (включается по желанию в prod): проверяем БД, Redis.
    Отдаём 200/503 в зависимости от готовности.
    """
    strict = getattr(settings, "HEALTH_STRICT", False)
    if not strict:
        # Даже если дернули /ready без strict — считаем ок
        return JsonResponse({"status": "ok", "checks": {"note": "strict disabled"}}, status=200)

    checks = {}
    ok = True

    # DB
    try:
        connections["default"].cursor()
        checks["db"] = "ok"
    except Exception as e:
        ok = False
        checks["db"] = f"error: {e!s}"

    # Redis (если настроен)
    redis_url = getattr(settings, "CELERY_BROKER_URL", None) or getattr(settings, "REDIS_URL", None)
    if redis_url and redis:
        try:
            r = redis.Redis.from_url(redis_url)
            r.ping()
            checks["redis"] = "ok"
        except Exception as e:
            ok = False
            checks["redis"] = f"error: {e!s}"
    elif redis_url and not redis:
        # библиотека не установлена
        checks["redis"] = "skipped (redis lib not installed)"

    return JsonResponse(
        {"status": "ok" if ok else "fail", "checks": checks}, status=200 if ok else 503
    )


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


@extend_schema(exclude=True)
@api_view(["GET"])
@permission_classes([IsAdminUser])
def debug_sentry(request):
    1 / 0


class HealthView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        health_hits_total.inc()
        return Response({"status": "ok"}, status=200)
