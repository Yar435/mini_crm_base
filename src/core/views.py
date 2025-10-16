import logging
from datetime import datetime
from datetime import timezone as tz

from django.conf import settings
from django.core.cache import cache
from django.db import connection, transaction
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import UserSecurityProfile
from core.serializers import DetailResponseSerializer, HealthResponseSerializer
from core.tasks import HEARTBEAT_KEY

logger = logging.getLogger(__name__)


@extend_schema(
    tags=["Ops"],
    summary="Health check",
    description="Проверка DB, кеша/Redis и пульса Celery beat (в тестах beat необязателен).",
    responses={200: HealthResponseSerializer, 503: HealthResponseSerializer},
)
@api_view(["GET"])
@permission_classes([AllowAny])
def health(request):
    checks = {}
    ok = True

    # --- DB check ---
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1;")
            cursor.fetchone()
        checks["db"] = "ok"
    except Exception as e:
        checks["db"] = f"error: {e}"
        ok = False

    # --- Cache/Redis check ---
    # Если backend — django-redis, пингуем Redis; иначе (LocMem, Dummy и т.п.) — считаем ОК.
    backend = settings.CACHES.get("default", {}).get("BACKEND", "")
    if "django_redis" in backend:
        try:
            from django_redis import (  # импорт локально, чтобы не падать без пакета
                get_redis_connection,
            )

            rc = get_redis_connection("default")
            rc.ping()
            checks["redis"] = "ok"
        except Exception as e:
            checks["redis"] = f"error: {e}"
            ok = False
    else:
        # В тестах у нас LocMemCache — это ожидаемо.
        checks["redis"] = "ok (non-redis backend)"

    # --- Celery beat heartbeat ---
    require_beat = getattr(settings, "HEALTH_REQUIRE_BEAT", True)
    hb = cache.get(HEARTBEAT_KEY)
    if hb:
        try:
            ts = datetime.fromisoformat(hb)
            age = (datetime.now(tz.utc) - ts).total_seconds()
            checks["celery_beat_age_sec"] = float(age)
            if require_beat and age > 180:
                ok = False
        except Exception as e:
            checks["celery_beat_age_sec"] = None
            # Логируем, а фейлим только если строго требуем beat
            logger.warning("Bad heartbeat timestamp: %s", e)
            if require_beat:
                ok = False
    else:
        checks["celery_beat_age_sec"] = None
        if require_beat:
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
