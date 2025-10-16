from datetime import datetime
from datetime import timezone as tz

from django.core.cache import cache
from django.db import connection, transaction
from django_redis import get_redis_connection
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import UserSecurityProfile
from core.serializers import DetailResponseSerializer, HealthResponseSerializer
from core.tasks import HEARTBEAT_KEY


@extend_schema(
    tags=["Ops"],
    summary="Health check",
    description="Проверка доступности DB, Redis и актуальности пульса Celery beat.",
    responses={200: HealthResponseSerializer, 503: HealthResponseSerializer},
)
@api_view(["GET"])
@permission_classes([])
def health(request):
    checks = {}
    ok = True

    # DB check
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1;")
            cursor.fetchone()
        checks["db"] = "ok"
    except Exception as e:
        checks["db"] = f"error: {e}"
        ok = False

    # Redis check
    try:
        r = get_redis_connection("default")
        r.ping()
        checks["redis"] = "ok"
    except Exception as e:
        checks["redis"] = f"error: {e}"
        ok = False

    # Celery beat heartbeat age (секунды или null)
    hb = cache.get(HEARTBEAT_KEY)
    if hb:
        try:
            ts = datetime.fromisoformat(hb)
            age = (datetime.now(tz.utc) - ts).total_seconds()
            checks["celery_beat_age_sec"] = float(age)
            if age > 180:  # >3 минут — плохой сигнал
                ok = False
        except Exception:
            checks["celery_beat_age_sec"] = None
            ok = False
    else:
        checks["celery_beat_age_sec"] = None
        ok = False

    code = status.HTTP_200_OK if ok else status.HTTP_503_SERVICE_UNAVAILABLE
    return Response({"status": "ok" if ok else "fail", "checks": checks}, status=code)


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
