import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from rest_framework.test import APIClient


@pytest.fixture(autouse=True, scope="session")
def _ensure_rbac_groups(django_db_setup, django_db_blocker):
    """Перед стартом сьюта создаём группы admin/manager/readonly и выдаём права."""
    with django_db_blocker.unblock():
        call_command("setup_rbac")


@pytest.fixture
def user(db):
    User = get_user_model()
    return User.objects.create_user(
        username="tester",
        email="tester@example.com",
        password="secret123",
        is_staff=True,
    )


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def auth_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client
