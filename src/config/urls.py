from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.utils import extend_schema
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

from clients.views import ClientViewSet
from core.views import health
from deals.views import DealViewSet, ManagerViewSet


class TokenObtainPairPatchedView(TokenObtainPairView):
    @extend_schema(
        tags=["Auth"],
        summary="Получить JWT-пару",
        description="Возвращает пару токенов (access/refresh) по валидным учетным данным.",
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class TokenRefreshPatchedView(TokenRefreshView):
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


router = DefaultRouter()
router.register("clients", ClientViewSet, basename="client")
router.register("deals", DealViewSet, basename="deal")
router.register("managers", ManagerViewSet, basename="manager")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include(router.urls)),
    path("api/auth/token/", TokenObtainPairPatchedView.as_view(), name="token_obtain_pair"),
    path("api/auth/token/refresh/", TokenRefreshPatchedView.as_view(), name="token_refresh"),
    path("api/auth/token/verify/", TokenVerifyPatchedView.as_view(), name="token_verify"),
    # схема и UI
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    path("health/", health),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns += [path("__debug__/", include(debug_toolbar.urls))]
