import pytest

from clients.models import Client
from deals.models import Deal, Manager


@pytest.mark.unit
@pytest.mark.django_db
def test_client_str():
    client = Client.objects.create(name="Acme", email="acme@example.com", phone="+70000000000")
    assert str(client).lower().startswith("acme")


@pytest.mark.unit
@pytest.mark.django_db
def test_deal_str():
    m = Manager.objects.create(name="Alice", email="alice@example.com", phone="+71111111111")
    c = Client.objects.create(name="Beta", email="beta@example.com", phone="+72222222222")
    deal = Deal.objects.create(
        title="Beta Onboarding", amount="1000.00", status="new", client=c, manager=m
    )
    assert "Beta Onboarding" in str(deal)
