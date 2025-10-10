import pytest
from django.urls import reverse

from clients.models import Client


@pytest.mark.api
@pytest.mark.django_db
def test_clients_list_ok(api_client):
    # данные
    Client.objects.create(name="Boba", email="boba@example.com", phone="+79990000000")
    Client.objects.create(name="Kira", email="kira@example.com", phone="+79991111111")

    url = reverse("client-list")  # basename="client" → client-list
    resp = api_client.get(url)

    assert resp.status_code == 200
    assert resp.data["count"] == 2
    assert isinstance(resp.data["results"], list)
    # минимальная проверка структуры
    assert {"id", "name", "email", "phone"} <= set(resp.data["results"][0].keys())


@pytest.mark.api
@pytest.mark.django_db
def test_clients_create_requires_auth(api_client):
    url = reverse("client-list")
    payload = {"name": "Zed", "email": "zed@example.com", "phone": "+79992223344"}

    resp = api_client.post(url, payload, format="json")
    assert resp.status_code in (401, 403)  # зависит от настроек, обычно 401


@pytest.mark.api
@pytest.mark.django_db
def test_clients_create_ok_with_auth(auth_client):
    url = reverse("client-list")
    payload = {"name": "Zed", "email": "zed@example.com", "phone": "+79992223344"}

    resp = auth_client.post(url, payload, format="json")
    assert resp.status_code in (201, 200)
