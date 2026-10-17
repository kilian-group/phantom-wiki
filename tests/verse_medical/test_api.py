from datetime import date, timedelta

from fastapi.testclient import TestClient

from verse_medical.app import app
from verse_medical.db import Base, SessionLocal, engine
from verse_medical.models import PatientOrder, SupplySchedule


client = TestClient(app)


def setup_function() -> None:
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with SessionLocal() as session:
        session.add(PatientOrder(patient_id="p1", product_category="catheter", quantity=30, patient_friendly_status="Shipped", delivery_tracking_id="trk123", created_by="provider_1"))
        session.add(SupplySchedule(patient_id="p1", product_id="catheter", quantity_per_period=30, period_days=30, next_order_date=date.today() + timedelta(days=1), auto_reorder=True, provider_preapproved=True, created_by="provider_1"))
        session.commit()


def test_patient_portal_flow() -> None:
    assert client.post("/api/v1/patient/auth/register", json={"patient_id": "p1", "email": "p@example.com", "preferred_language": "es"}).status_code == 200

    r = client.get("/api/v1/patient/orders", headers={"x-patient-id": "p1"})
    assert r.status_code == 200
    assert len(r.json()) == 1

    order_id = r.json()[0]["id"]
    assert client.get(f"/api/v1/patient/orders/{order_id}/track", headers={"x-patient-id": "p1"}).status_code == 200
    assert client.post(f"/api/v1/patient/orders/{order_id}/reorder", headers={"x-patient-id": "p1"}, json={"reason": "low supplies"}).status_code == 200

    r = client.get("/api/v1/patient/supplies", headers={"x-patient-id": "p1"})
    assert "12 more days" in r.json()[0]["countdown"]
    assert client.post("/api/v1/patient/support", headers={"x-patient-id": "p1"}, json={"subject": "Need help", "message": "box damaged"}).status_code == 200


def test_other_feature_endpoints() -> None:
    admin = {"x-provider-id": "admin_1"}
    provider = {"x-provider-id": "provider_1"}

    r = client.post("/api/v1/admin/payer-rules", headers=admin, json={"payer_id": "default_payer", "product_category": "catheter", "requires_cmn": True, "requires_face_to_face": True, "requires_prior_auth": False, "frequency_limit_days": 0, "max_quantity_per_period": 60})
    assert r.status_code == 200

    r = client.get("/api/v1/patients/p1/schedules", headers=provider)
    assert r.status_code == 200
    schedule_id = r.json()[0]["id"]

    assert client.put(f"/api/v1/patients/p1/schedules/{schedule_id}", headers=provider, json={"period_days": 25}).status_code == 200
    assert client.post(f"/api/v1/patients/p1/schedules/{schedule_id}/pause", headers=provider).status_code == 200

    r = client.post("/api/v1/eligibility/check", headers=provider, json={"patient_id": "p1", "payer_id": "default_payer", "products": [{"product_category": "catheter", "quantity": 30}]})
    assert r.status_code == 200

    r = client.get("/api/v1/eligibility/history/p1", headers=provider)
    assert r.status_code == 200 and len(r.json()) >= 1

    r = client.post("/api/v1/orders/1/documents/generate", headers=provider)
    assert r.status_code == 200
    doc_id = r.json()[0]["id"]

    assert client.post(f"/api/v1/documents/{doc_id}/sign", headers=provider, json={"signature": "provider-sign"}).status_code == 200
    assert client.get(f"/api/v1/documents/{doc_id}/pdf", headers=provider).status_code == 200

    assert client.get("/api/v1/analytics/orders", headers=provider).status_code == 200
    assert client.get("/api/v1/analytics/patients/p1", headers=provider).status_code == 200
    assert client.get("/api/v1/analytics/compliance", headers=provider).status_code == 200
    assert client.get("/api/v1/analytics/export", headers=provider).status_code == 200

    assert client.post("/api/v1/fhir/connect", headers=provider, json={"server_url": "https://ehr.example.com/fhir", "client_id": "abc", "client_secret": "xyz"}).status_code == 200
    assert client.post("/api/v1/fhir/sync/patient/p1", headers=provider).status_code == 200
    assert client.get("/api/v1/fhir/subscriptions", headers=provider).status_code == 200
    assert client.post("/api/v1/fhir/launch", headers=provider, json={"iss": "ehr", "launch": "token"}).status_code == 200


def test_reorder_worker_endpoint() -> None:
    r = client.post("/api/v1/internal/reorder/run", headers={"x-provider-id": "provider_1"})
    assert r.status_code == 200
