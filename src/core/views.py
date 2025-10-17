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

from core.metrics import health_hits_total
from core.models import UserSecurityProfile
from core.serializers import DetailResponseSerializer, HealthResponseSerializer
from core.tasks import HEARTBEAT_KEY

logger = logging.getLogger(__name__)


def _as_bool(v) -> bool:
    if isinstance(v, bool):
        return v
    if v is None:
        return False
    return str(v).strip().lower() in {"1", "true", "yes", "y", "on"}


@extend_schema(
    tags=["Ops"],
    summary="Health check",
    description="Проверка DB, Redis/кеша и пульса Celery beat. В тестах/CI мягкий режим.",
    responses={
        200: HealthResponseSerializer,
        503: HealthResponseSerializer,
    },
)
@api_view(["GET"])
@permission_classes([AllowAny])
def health(request):
    # Мягкий/строгий режим: ?strict=1 перекрывает настройку
    strict = _as_bool(request.query_params.get("strict"))
    if request.query_params.get("strict") is None:
        strict = getattr(settings, "HEALTH_STRICT_DEFAULT", True)

    checks = {}
    ok = True

    # Если режим мягкий — сразу 200 с минимальными проверками (под тесты/CI)
    if not strict:
        checks["mode"] = "lenient"
        checks["db"] = "skipped"
        checks["redis"] = "skipped"
        checks["celery_beat_age_sec"] = None
        return Response({"status": "ok", "checks": checks}, status=status.HTTP_200_OK)

    # --- STRICT MODE ниже ---
    # DB
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1;")
            cursor.fetchone()
        checks["db"] = "ok"
    except Exception as e:
        checks["db"] = f"error: {e}"
        ok = False

    # Redis / cache
    backend = settings.CACHES.get("default", {}).get("BACKEND", "")
    if "django_redis" in backend:
        try:
            from django_redis import get_redis_connection

            rc = get_redis_connection("default")
            rc.ping()
            checks["redis"] = "ok"
        except Exception as e:
            checks["redis"] = f"error: {e}"
            ok = False
    else:
        checks["redis"] = "ok (non-redis backend)"

    # Beat
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
            logger.warning("Bad heartbeat timestamp: %s", e)
            checks["celery_beat_age_sec"] = None
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


class HealthView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        health_hits_total.inc()
        return Response({"status": "ok"}, status=200)
