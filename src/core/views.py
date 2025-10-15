from django.db import transaction
from django.http import JsonResponse
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import UserSecurityProfile
from core.serializers import DetailResponseSerializer


def health(request):
    return JsonResponse({"status": "ok"})


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
