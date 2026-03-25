import pytest

from analytics.models import AmoLead, AmoLeadTransition, AmoPipeline, AmoStatus
from analytics.services.graph_builder import build_process_graph_from_params


@pytest.mark.api
@pytest.mark.django_db
def test_graph_builder_replay_speed_counts_and_pfinal():
    pipeline = AmoPipeline.objects.create(id=1, name="Main", sort=1, is_main=True)
    s_new = AmoStatus.objects.create(id=10, pipeline=pipeline, name="New", is_final=False)
    s_mid = AmoStatus.objects.create(
        id=11, pipeline=pipeline, name="Mid", is_final=False
    )
    s_final = AmoStatus.objects.create(
        id=12, pipeline=pipeline, name="Final", is_final=True
    )

    # lead 100: New -> Mid -> Final
    AmoLeadTransition.objects.create(
        event_id="e1",
        lead_id=100,
        at=100,
        by_user=None,
        from_status=s_new,
        to_status=s_mid,
    )
    AmoLeadTransition.objects.create(
        event_id="e2",
        lead_id=100,
        at=120,
        by_user=None,
        from_status=s_mid,
        to_status=s_final,
    )

    # lead 101: New -> Mid
    AmoLeadTransition.objects.create(
        event_id="e3",
        lead_id=101,
        at=110,
        by_user=None,
        from_status=s_new,
        to_status=s_mid,
    )

    graph = build_process_graph_from_params(
        pipeline_id=1,
        as_of=200,
        mode="replay_speed",
        window_minutes=None,
        top_k=2,
        from_status_id=None,
    )

    edges = {(e["from_status_id"], e["to_status_id"]): e for e in graph["edges"]}

    assert (10, 11) in edges
    assert (11, 12) in edges
    assert edges[(10, 11)]["weight"] == 2
    assert edges[(10, 11)]["p_final"] == 0.0
    assert edges[(10, 11)]["avg_time_sec"] is None

    assert edges[(11, 12)]["weight"] == 1
    assert edges[(11, 12)]["p_final"] == 1.0
    assert edges[(11, 12)]["avg_time_sec"] == 20.0


@pytest.mark.api
@pytest.mark.django_db
def test_process_graph_api_replay_speed(auth_client):
    pipeline = AmoPipeline.objects.create(id=1, name="Main", sort=1, is_main=True)
    s_new = AmoStatus.objects.create(id=10, pipeline=pipeline, name="New", is_final=False)
    s_mid = AmoStatus.objects.create(
        id=11, pipeline=pipeline, name="Mid", is_final=False
    )
    s_final = AmoStatus.objects.create(
        id=12, pipeline=pipeline, name="Final", is_final=True
    )

    AmoLeadTransition.objects.create(
        event_id="e1",
        lead_id=100,
        at=100,
        by_user=None,
        from_status=s_new,
        to_status=s_mid,
    )
    AmoLeadTransition.objects.create(
        event_id="e2",
        lead_id=100,
        at=120,
        by_user=None,
        from_status=s_mid,
        to_status=s_final,
    )
    AmoLeadTransition.objects.create(
        event_id="e3",
        lead_id=101,
        at=110,
        by_user=None,
        from_status=s_new,
        to_status=s_mid,
    )

    url = "/api/analytics/process-graph/"
    resp = auth_client.get(
        url,
        {
            "pipeline_id": "1",
            "as_of": "200",
            "mode": "replay_speed",
            "top_k": "2",
        },
    )
    assert resp.status_code == 200

    edges = {(e["from_status_id"], e["to_status_id"]): e for e in resp.data["edges"]}
    assert edges[(10, 11)]["weight"] == 2
    assert edges[(11, 12)]["weight"] == 1


@pytest.mark.api
@pytest.mark.django_db
def test_process_graph_api_rolling_window(auth_client):
    pipeline = AmoPipeline.objects.create(id=1, name="Main", sort=1, is_main=True)
    s_new = AmoStatus.objects.create(id=10, pipeline=pipeline, name="New", is_final=False)
    s_mid = AmoStatus.objects.create(
        id=11, pipeline=pipeline, name="Mid", is_final=False
    )
    s_final = AmoStatus.objects.create(
        id=12, pipeline=pipeline, name="Final", is_final=True
    )

    AmoLeadTransition.objects.create(
        event_id="e1",
        lead_id=100,
        at=100,
        by_user=None,
        from_status=s_new,
        to_status=s_mid,
    )
    AmoLeadTransition.objects.create(
        event_id="e2",
        lead_id=100,
        at=120,
        by_user=None,
        from_status=s_mid,
        to_status=s_final,
    )

    url = "/api/analytics/process-graph/"
    resp = auth_client.get(
        url,
        {
            "pipeline_id": "1",
            "as_of": "200",
            "mode": "rolling_window",
            "window_minutes": "5",
            "top_k": "2",
        },
    )
    assert resp.status_code == 200
    edges = {(e["from_status_id"], e["to_status_id"]): e for e in resp.data["edges"]}
    assert edges[(10, 11)]["weight"] == 1
    assert edges[(11, 12)]["weight"] == 1


@pytest.mark.api
@pytest.mark.django_db
def test_graph_builder_price_filter_limits_leads():
    pipeline = AmoPipeline.objects.create(id=1, name="Main", sort=1, is_main=True)
    s_new = AmoStatus.objects.create(id=10, pipeline=pipeline, name="New", is_final=False)
    s_mid = AmoStatus.objects.create(
        id=11, pipeline=pipeline, name="Mid", is_final=False
    )

    AmoLead.objects.create(
        id=100,
        pipeline=pipeline,
        status=s_mid,
        name="A",
        price=1000,
        is_deleted=False,
    )
    AmoLead.objects.create(
        id=101,
        pipeline=pipeline,
        status=s_mid,
        name="B",
        price=5000,
        is_deleted=False,
    )

    AmoLeadTransition.objects.create(
        event_id="e1",
        lead_id=100,
        at=100,
        by_user=None,
        from_status=s_new,
        to_status=s_mid,
    )
    AmoLeadTransition.objects.create(
        event_id="e2",
        lead_id=101,
        at=110,
        by_user=None,
        from_status=s_new,
        to_status=s_mid,
    )

    graph = build_process_graph_from_params(
        pipeline_id=1,
        as_of=200,
        mode="replay_speed",
        window_minutes=None,
        top_k=10,
        from_status_id=None,
        min_price=4000,
        max_price=6000,
    )
    edges = {(e["from_status_id"], e["to_status_id"]): e for e in graph["edges"]}
    assert (10, 11) in edges
    assert edges[(10, 11)]["weight"] == 1

