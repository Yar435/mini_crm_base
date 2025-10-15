import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient


@pytest.mark.api
def test_logout_revokes_tokens(db):
    user = User.objects.create_user(username="u", password="p")
    c = APIClient()

    tokens = c.post(
        "/api/auth/token/",
        {
            "username": user.username,
            "password": "p",
        },
    ).data
    access = tokens["access"]

    c.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
    assert c.get("/health/").status_code == 200

    assert c.post("/api/auth/logout/").status_code == 200

    # старый токен больше не валиден
    assert c.get("/api/clients/").status_code in (401, 403)
