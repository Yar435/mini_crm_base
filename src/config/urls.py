from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from clients.views import ClientViewSet
from deals.views import DealViewSet, ManagerViewSet

router = DefaultRouter()
router.register("clients", ClientViewSet, basename="client")
router.register("deals", DealViewSet, basename="deal")
router.register("managers", ManagerViewSet, basename="manager")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include(router.urls)),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns += [path("__debug__/", include(debug_toolbar.urls))]
