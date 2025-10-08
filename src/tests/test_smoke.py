import pytest

from clients.models import Client


@pytest.mark.django_db
def test_create_client():
    c = Client.objects.create(name="Test", email="t@example.com")
    assert Client.objects.filter(id=c.id).exists()
