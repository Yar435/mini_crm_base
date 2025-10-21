import pytest
from django.contrib.auth.models import Group, User
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_readonly_cannot_create_client():
    # user в группе readonly
    u = User.objects.create_user("ro", password="p")
    u.groups.add(Group.objects.get(name="readonly"))

    c = APIClient()
    # получаем токен
    resp = c.post("/api/auth/token/", {"username": "ro", "password": "p"}, format="json")
    assert resp.status_code == 200
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.data['access']}")

    # попытка создать клиента
    resp = c.post("/api/clients/", {"name": "A", "email": "a@a.com"}, format="json")
    assert resp.status_code in (403, 401)


@pytest.mark.django_db
def test_manager_can_create_client():
    u = User.objects.create_user("m", password="p")
    u.groups.add(Group.objects.get(name="manager"))

    c = APIClient()
    resp = c.post("/api/auth/token/", {"username": "m", "password": "p"}, format="json")
    assert resp.status_code == 200
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.data['access']}")

    resp = c.post("/api/clients/", {"name": "B", "email": "b@b.com"}, format="json")
    assert resp.status_code == 201
