import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient


@pytest.mark.api
def test_logout_revokes_tokens(db):
    User.objects.create_user(username="u", password="p")
    c = APIClient()

    resp = c.post("/api/auth/token/", {"username": "u", "password": "p"}, format="json")
    assert resp.status_code == 200, resp.data  # покажет ошибку, если не 200
    assert "access" in resp.data and "refresh" in resp.data, resp.data

    access = resp.data["access"]

    c.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
    assert c.get("/health/").status_code == 200

    assert c.post("/api/auth/logout/").status_code == 200

    # старый токен теперь не проходит
    assert c.get("/api/clients/").status_code in (401, 403)
