import re

from rest_framework.test import APIClient


def test_request_id_echo():
    c = APIClient()
    resp = c.get("/health/")
    assert resp.status_code == 200
    assert "X-Request-ID" in resp  # заголовок
    rid = resp["X-Request-ID"]
    assert re.fullmatch(r"[0-9a-f]{32}", rid)  # uuid4.hex
    assert resp.data.get("request_id") == rid  # тело тоже эхо для удобства
