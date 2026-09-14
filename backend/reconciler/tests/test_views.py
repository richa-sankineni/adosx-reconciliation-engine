import pytest
from django.test import Client

from reconciler.models import Location, SystemARecord, SystemBEntry


@pytest.fixture
def two_tenant_data(db):
    
    Location.objects.create(location_id="LOC-A1", org_id="ORG-A", location_name="A1")
    Location.objects.create(location_id="LOC-B1", org_id="ORG-B", location_name="B1")

    SystemARecord.objects.create(
        record_id="REC-A1",
        record_id_normalized="1",
        location_id_raw="LOC-A1",
        total_value_raw="100.00",
        raw_row={},
    )
    SystemARecord.objects.create(
        record_id="REC-B1",
        record_id_normalized="2",
        location_id_raw="LOC-B1",
        total_value_raw="200.00",
        raw_row={},
    )


def test_tenant_boundary_isolation(two_tenant_data):
   
    client = Client()

    resp_a = client.get("/api/discrepancies/?org_id=ORG-A").json()
    resp_b = client.get("/api/discrepancies/?org_id=ORG-B").json()

    assert resp_a["count"] == 1
    assert resp_a["results"][0]["record_ref"] == "REC-A1"
    assert all(d["org_id"] == "ORG-A" for d in resp_a["results"])

    assert resp_b["count"] == 1
    assert resp_b["results"][0]["record_ref"] == "REC-B1"
    assert all(d["org_id"] == "ORG-B" for d in resp_b["results"])

    assert "REC-B1" not in [d["record_ref"] for d in resp_a["results"]]
    assert "REC-A1" not in [d["record_ref"] for d in resp_b["results"]]


def test_org_id_is_mandatory(two_tenant_data):
    client = Client()
    resp = client.get("/api/discrepancies/")
    assert resp.status_code == 400


def test_unknown_org_id_is_rejected(two_tenant_data):
    client = Client()
    resp = client.get("/api/discrepancies/?org_id=NOT-A-REAL-ORG")
    assert resp.status_code == 404
