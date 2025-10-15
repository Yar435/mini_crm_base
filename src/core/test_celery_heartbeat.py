import pytest


@pytest.mark.unit
def test_heartbeat_eager(settings):
    settings.CELERY_TASK_ALWAYS_EAGER = True
    from core.tasks import heartbeat

    assert heartbeat.delay().get(timeout=2) == "ok"
