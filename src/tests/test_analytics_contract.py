"""Тесты контракта аналитики: кэш-ключи, валидация query-параметров."""

import pytest

from analytics.blondon_paths import blondon_memory_dir
from analytics.cache_keys import make_process_graph_cache_key
from analytics.models import AmoLead, AmoLeadTransition, AmoPipeline, AmoStatus


@pytest.mark.unit
def test_blondon_memory_dir_name():
    assert blondon_memory_dir().name == "Blondon_memory"


@pytest.mark.unit
def test_make_process_graph_cache_key_includes_price_segment():
    k1 = make_process_graph_cache_key(
        pipeline_id=1,
        mode="replay_speed",
        as_of_ts=120,
        window_minutes=None,
        top_k=20,
        from_status_id=None,
    )
    assert "price=none" in k1
    k2 = make_process_graph_cache_key(
        pipeline_id=1,
        mode="replay_speed",
        as_of_ts=120,
        window_minutes=None,
        top_k=20,
        from_status_id=None,
        min_price=10.5,
        max_price=None,
    )
    assert "10.5-" in k2


@pytest.mark.api
@pytest.mark.django_db
def test_process_graph_api_400_bad_top_k(auth_client):
    url = "/api/analytics/process-graph/"
    resp = auth_client.get(
        url,
        {"pipeline_id": "1", "as_of": "100", "top_k": "99999"},
    )
    assert resp.status_code == 400
    assert "detail" in resp.data


@pytest.mark.api
@pytest.mark.django_db
def test_process_graph_api_400_rolling_without_window(auth_client):
    url = "/api/analytics/process-graph/"
    resp = auth_client.get(
        url,
        {"pipeline_id": "1", "as_of": "100", "mode": "rolling_window"},
    )
    assert resp.status_code == 400


@pytest.mark.api
@pytest.mark.django_db
def test_process_graph_api_400_bad_price_range(auth_client):
    url = "/api/analytics/process-graph/"
    resp = auth_client.get(
        url,
        {
            "pipeline_id": "1",
            "as_of": "100",
            "min_price": "100",
            "max_price": "50",
        },
    )
    assert resp.status_code == 400


@pytest.mark.api
@pytest.mark.django_db
def test_process_graph_api_price_query_params(auth_client):
    pipeline = AmoPipeline.objects.create(id=1, name="Main", sort=1, is_main=True)
    s_new = AmoStatus.objects.create(id=10, pipeline=pipeline, name="New", is_final=False)
    s_mid = AmoStatus.objects.create(
        id=11, pipeline=pipeline, name="Mid", is_final=False
    )
    AmoLead.objects.create(
        id=200,
        pipeline=pipeline,
        status=s_mid,
        name="X",
        price=5000,
        is_deleted=False,
    )
    AmoLeadTransition.objects.create(
        event_id="pe1",
        lead_id=200,
        at=50,
        by_user=None,
        from_status=s_new,
        to_status=s_mid,
    )
    url = "/api/analytics/process-graph/"
    resp = auth_client.get(
        url,
        {
            "pipeline_id": "1",
            "as_of": "100",
            "mode": "replay_speed",
            "top_k": "5",
            "min_price": "4000",
            "max_price": "6000",
        },
    )
    assert resp.status_code == 200
    assert resp.data["meta"]["min_price"] in (4000, 4000.0)
    assert resp.data["meta"]["max_price"] in (6000, 6000.0)


@pytest.mark.unit
@pytest.mark.django_db
def test_rebuild_graph_snapshots_runs():
    from analytics.tasks import rebuild_graph_snapshots

    assert rebuild_graph_snapshots() == "no-pipelines"
    AmoPipeline.objects.create(id=1, name="Main", sort=1, is_main=True)
    out = rebuild_graph_snapshots()
    assert out.startswith("ok:")
