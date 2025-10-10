import pytest
from django.urls import reverse

from clients.models import Client
from deals.models import Deal, Manager


@pytest.mark.api
@pytest.mark.django_db
def test_deals_list_ok(api_client):
    m = Manager.objects.create(name="Alice", email="alice@example.com", phone="+71111111111")
    c = Client.objects.create(name="Beta", email="beta@example.com", phone="+72222222222")
    Deal.objects.create(title="D1", amount=100, status="new", client=c, manager=m)
    Deal.objects.create(title="D2", amount=200, status="won", client=c, manager=m)

    url = reverse("deal-list")  # basename="deal" → deal-list
    resp = api_client.get(url)

    assert resp.status_code == 200
    assert resp.data["count"] == 2
    titles = [d["title"] for d in resp.data["results"]]
    assert {"D1", "D2"} <= set(titles)


@pytest.mark.api
@pytest.mark.django_db
def test_deals_filter_by_status(api_client):
    m = Manager.objects.create(name="Alice", email="alice@example.com", phone="+71111111111")
    c = Client.objects.create(name="Beta", email="beta@example.com", phone="+72222222222")
    Deal.objects.create(title="N1", amount=100, status="new", client=c, manager=m)
    Deal.objects.create(title="W1", amount=200, status="won", client=c, manager=m)

    url = reverse("deal-list")
    resp = api_client.get(url, {"status": "won"})

    assert resp.status_code == 200
    assert resp.data["count"] == 1
    assert resp.data["results"][0]["status"] == "won"
