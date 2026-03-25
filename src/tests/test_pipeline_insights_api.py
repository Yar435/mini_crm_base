import pytest
from unittest.mock import patch

from analytics.models import AmoLead, AmoPipeline, AmoStatus, AmoLeadTransition, AmoSyncState
from analytics.services.incremental_leads_sync import SYNC_KEY_LEADS, run_incremental_leads_sync
from analytics.tasks import incremental_sync_leads


@pytest.mark.api
@pytest.mark.django_db
def test_pipeline_funnel_api(auth_client):
    pipeline = AmoPipeline.objects.create(id=1, name="Main", sort=1, is_main=True)
    s10 = AmoStatus.objects.create(id=10, pipeline=pipeline, name="New", is_final=False)
    s11 = AmoStatus.objects.create(id=11, pipeline=pipeline, name="Mid", is_final=False)
    AmoLead.objects.create(
        id=1,
        pipeline=pipeline,
        status=s10,
        name="a",
        is_deleted=False,
    )
    AmoLead.objects.create(
        id=2,
        pipeline=pipeline,
        status=s11,
        name="b",
        is_deleted=False,
    )

    r = auth_client.get("/api/analytics/pipeline-funnel/", {"pipeline_id": "1"})
    assert r.status_code == 200
    assert r.data["meta"]["total_leads"] == 2
    by_id = {x["status_id"]: x["count"] for x in r.data["statuses"] if x["status_id"] is not None}
    assert by_id[10] == 1
    assert by_id[11] == 1


@pytest.mark.api
@pytest.mark.django_db
def test_transitions_by_user_api(auth_client):
    pipeline = AmoPipeline.objects.create(id=1, name="Main", sort=1, is_main=True)
    s10 = AmoStatus.objects.create(id=10, pipeline=pipeline, name="New", is_final=False)
    s11 = AmoStatus.objects.create(id=11, pipeline=pipeline, name="Mid", is_final=False)
    AmoLeadTransition.objects.create(
        event_id="e1",
        lead_id=1,
        at=100,
        by_user=5,
        from_status=s10,
        to_status=s11,
    )
    AmoLeadTransition.objects.create(
        event_id="e2",
        lead_id=2,
        at=150,
        by_user=5,
        from_status=s10,
        to_status=s11,
    )
    AmoLeadTransition.objects.create(
        event_id="e3",
        lead_id=3,
        at=120,
        by_user=7,
        from_status=s10,
        to_status=s11,
    )

    r = auth_client.get(
        "/api/analytics/transitions-by-user/",
        {"pipeline_id": "1", "from_ts": "50", "to_ts": "200", "top_k": "10"},
    )
    assert r.status_code == 200
    users = {x["user_id"]: x["transitions"] for x in r.data["by_user"]}
    assert users[5] == 2
    assert users[7] == 1


@pytest.mark.django_db
def test_incremental_leads_sync_mocked():
    pipeline = AmoPipeline.objects.create(id=1, name="Main", sort=1, is_main=True)
    AmoStatus.objects.create(id=10, pipeline=pipeline, name="New", is_final=False)

    lead_payload = {
        "id": 999,
        "name": "API Lead",
        "pipeline_id": 1,
        "status_id": 10,
        "price": 100,
        "created_at": 1000,
        "updated_at": 2000,
        "is_deleted": False,
    }

    def _fake_iter(*args, **kwargs):
        yield lead_payload

    with patch(
        "analytics.services.incremental_leads_sync.iter_leads_updated_since",
        side_effect=_fake_iter,
    ):
        out = run_incremental_leads_sync(subdomain="sub", token="tok")

    assert out["ok"] is True
    assert out["processed"] == 1
    assert AmoLead.objects.filter(id=999).exists()
    st = AmoSyncState.objects.get(key=SYNC_KEY_LEADS)
    assert int(st.watermark_updated_at) >= 2000


@pytest.mark.django_db
def test_incremental_sync_leads_task_skipped_without_env(settings):
    settings.AMOCRM_SUBDOMAIN = ""
    settings.AMOCRM_ACCESS_TOKEN = ""
    assert incremental_sync_leads() == "skipped:no-credentials"
