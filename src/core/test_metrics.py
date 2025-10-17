import pytest
from django.test import Client


@pytest.mark.api
def test_metrics_endpoint_available(db):
    """
    Smoketest: /metrics отвечает 200 OK и отдаёт Prometheus-текст.
    Не требует запущенного сервера — используем Django test client.
    """
    c = Client()
    resp = c.get("/metrics")
    assert resp.status_code == 200
    # формат — text/plain; version=0.0.4 (Prometheus exposition format)
    assert resp["Content-Type"].startswith("text/plain")
    # базовые метки prometheus_client всегда есть
    assert b"# HELP python_info Python platform information" in resp.content
