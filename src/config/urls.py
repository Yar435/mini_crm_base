from django.conf import settings
from django.contrib import admin
from django.db import transaction
from django.urls import include, path
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from drf_spectacular.utils import extend_schema
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView

from clients.views import ClientViewSet

# наш сериалайзер, добавляющий claim token_version
from core.auth import TokenObtainPairWithVersionSerializer
from core.serializers import DetailResponseSerializer
from core.views import LogoutView, debug_sentry, health, ready
from deals.views import DealViewSet, ManagerViewSet

# --- Auth views (с описаниями для Swagger) ---

rl = method_decorator(ratelimit(key="ip", rate="5/m", block=True), name="post")


class TokenObtainPairPatchedView(TokenObtainPairView):
    serializer_class = TokenObtainPairWithVersionSerializer

    @rl
    @extend_schema(  # как было у тебя
        tags=["Auth"],
        summary="Получить JWT-пару",
        description="Возвращает пару токенов (access/refresh) по валидным учетным данным.",
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class TokenRefreshPatchedView(TokenRefreshView):
    @rl
    @extend_schema(
        tags=["Auth"],
        summary="Обновить access-токен",
        description="Возвращает новый access-токен по refresh.",
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class TokenVerifyPatchedView(TokenVerifyView):
    @extend_schema(
        tags=["Auth"],
        summary="Верифицировать токен",
        description="Проверяет валидность access/refresh токена.",
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


@extend_schema(
    tags=["Auth"],
    summary="Выйти (инвалидировать токены)",
    description=(
        "Инкрементирует `token_version` у пользователя "
        "и делает невалидными все выданные ранее токены. "
        "Требуется аутентификация действующим access-токеном."
    ),
    request=None,
    responses={200: DetailResponseSerializer},
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_view(request):
    sec = getattr(request.user, "security", None)
    if sec is None:
        from core.models import UserSecurityProfile

        sec = UserSecurityProfile.objects.create(user=request.user)

    with transaction.atomic():
        sec.token_version = sec.token_version + 1
        sec.save(update_fields=["token_version"])
    return Response({"detail": "logged out"})


# --- Routers ---

router = DefaultRouter()
router.register("clients", ClientViewSet, basename="client")
router.register("deals", DealViewSet, basename="deal")
router.register("managers", ManagerViewSet, basename="manager")


# --- URL patterns ---

urlpatterns = [
    path("", include("django_prometheus.urls")),
    path("admin/", admin.site.urls),
    # API
    path("api/", include(router.urls)),
    # Auth
    path("api/auth/token/", TokenObtainPairPatchedView.as_view(), name="token_obtain_pair"),
    path("api/auth/token/refresh/", TokenRefreshPatchedView.as_view(), name="token_refresh"),
    path("api/auth/token/verify/", TokenVerifyPatchedView.as_view(), name="token_verify"),
    path("api/auth/logout/", logout_view, name="logout"),
    # OpenAPI + UI
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    # health
    path("health/", health),
    path("ready/", ready),
    path("api/auth/logout/", LogoutView.as_view(), name="logout"),
    path("debug/sentry/", debug_sentry),
]

# if settings.METRICS_ENABLED:
#     urlpatterns = [path("", include("django_prometheus.urls"))] + urlpatterns


if settings.DEBUG:
    import debug_toolbar

    urlpatterns += [path("__debug__/", include(debug_toolbar.urls))]
