import os
import tempfile
import pytest
from fastapi.testclient import TestClient
from app.config import settings
from app.database import get_db, init_database
from app.main import app

@pytest.fixture
def client():
    orig_db = settings.DATABASE_PATH
    orig_counselor_key = settings.COUNSELOR_API_KEY
    orig_admin_key = settings.ADMIN_API_KEY
    temp_dir = tempfile.TemporaryDirectory()
    settings.DATABASE_PATH = os.path.join(temp_dir.name, "test_referrals.db")
    settings.COUNSELOR_API_KEY = "test-counselor-key"
    settings.ADMIN_API_KEY = "test-admin-key"
    init_database()

    with TestClient(app) as c:
        yield c

    settings.DATABASE_PATH = orig_db
    settings.COUNSELOR_API_KEY = orig_counselor_key
    settings.ADMIN_API_KEY = orig_admin_key
    temp_dir.cleanup()

def test_referral_lifecycle_and_counselor_assignment(client):
    # 1. Create session and grant consent
    sess_res = client.post("/api/v1/sessions")
    session_id = sess_res.json()["session_id"]
    session_headers = {"X-Session-Token": sess_res.json()["session_token"]}

    client.post("/api/v1/consents", json={
        "session_id": session_id,
        "consent_type": "counselor_referral",
        "granted": True
    }, headers=session_headers)

    # 2. Beneficiary submits referral
    ref_res = client.post("/api/v1/referrals", json={
        "interview_id": session_id,
        "referral_reason": "complex_eligibility_query",
        "priority": "high",
        "notes": "Query regarding subsidy for SC entrepreneur"
    }, headers=session_headers)
    assert ref_res.status_code == 201
    ref_data = ref_res.json()
    case_id = ref_data["id"]
    assert ref_data["status"] == "new"
    assert "user_safe_message" in ref_data

    # 3. Unauthenticated / guest cannot view counselor queue -> 403
    unauth_queue = client.get("/api/v1/counselor/referrals")
    assert unauth_queue.status_code == 403

    # 4. Counselor views queue using counselor API key
    counselor_headers = {"X-Worker-API-Key": settings.COUNSELOR_API_KEY}
    counselor_queue = client.get("/api/v1/counselor/referrals", headers=counselor_headers)
    assert counselor_queue.status_code == 200
    cases = counselor_queue.json()
    assert any(c["id"] == case_id for c in cases)

    # 5. Admin assigns counselor
    admin_headers = {"X-Worker-API-Key": settings.ADMIN_API_KEY}
    assign_res = client.patch(
        f"/api/v1/counselor/referrals/{case_id}/assign",
        json={"counselor_id": "counselor"},
        headers=admin_headers
    )
    assert assign_res.status_code == 200
    assert assign_res.json()["status"] == "assigned"
    assert assign_res.json()["assigned_counselor_id"] == "counselor"

    # 6. Assigned counselor updates status to in_progress
    status_res = client.patch(
        f"/api/v1/counselor/referrals/{case_id}/status",
        json={"status": "in_progress", "notes": "Contacted beneficiary via phone"},
        headers=counselor_headers
    )
    assert status_res.status_code == 200
    assert status_res.json()["status"] == "in_progress"

    # 7. Add counselor case note
    note_res = client.post(
        f"/api/v1/counselor/referrals/{case_id}/notes",
        json={"note": "Beneficiary confirmed preference for KVK Chhajlet batch."},
        headers=counselor_headers
    )
    assert note_res.status_code == 201
    assert "id" in note_res.json()

    # 8. Check audit trail recorded for referral
    audit_res = client.get("/api/v1/audit-events?entity_type=referral_case", headers=admin_headers)
    assert audit_res.status_code == 200
    events = audit_res.json()
    assert len(events) >= 1
    assert any(e["action"] == "REFERRAL_CASE_CREATED" for e in events)
