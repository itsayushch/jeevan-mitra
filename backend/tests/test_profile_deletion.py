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
    temp_dir = tempfile.TemporaryDirectory()
    settings.DATABASE_PATH = os.path.join(temp_dir.name, "test_deletion.db")
    init_database()

    with TestClient(app) as c:
        yield c

    settings.DATABASE_PATH = orig_db
    temp_dir.cleanup()

def test_full_profile_erasure_dpdp_compliance(client):
    # 1. Create permanent beneficiary with consent and interview data
    create_ben = client.post("/api/v1/beneficiaries", json={
        "name": "Suresh Paswan",
        "phone": "+919876500000",
        "district": "Moradabad",
        "block": "Chhajlet",
        "category": "SC"
    })
    assert create_ben.status_code == 201
    ben_id = create_ben.json()["id"]

    ben_headers = {"X-Beneficiary-ID": ben_id}

    # Record consent
    client.post("/api/v1/consents", json={
        "beneficiary_id": ben_id,
        "consent_type": "ai_processing",
        "granted": True
    }, headers=ben_headers)

    # Start interview
    int_start = client.post("/api/v1/interviews/start", json={
        "beneficiary_id": ben_id
    }, headers=ben_headers)
    assert int_start.status_code == 201
    int_id = int_start.json()["interview_id"]

    # Confirm profile fields
    client.post(f"/api/v1/interviews/{int_id}/confirm-profile", json={
        "beneficiary_id": ben_id,
        "confirmed_fields": {"education": "Class 10", "mobility": 5.0}
    }, headers=ben_headers)

    # Generate recommendations
    client.post("/api/v1/recommendations/generate", json={
        "interview_id": int_id,
        "beneficiary_id": ben_id
    }, headers=ben_headers)

    # Verify data exists before deletion
    with get_db() as conn:
        assert conn.execute("SELECT COUNT(*) as c FROM interview_turns WHERE interview_id = ?;", (int_id,)).fetchone()["c"] > 0
        assert conn.execute("SELECT COUNT(*) as c FROM profile_field_values WHERE interview_id = ?;", (int_id,)).fetchone()["c"] > 0
        assert conn.execute("SELECT COUNT(*) as c FROM recommendations WHERE beneficiary_id = ?;", (ben_id,)).fetchone()["c"] > 0

    # 2. Execute Full Profile Erasure via DELETE /api/v1/beneficiaries/me
    del_res = client.delete("/api/v1/beneficiaries/me", headers=ben_headers)
    assert del_res.status_code == 200
    assert "permanently purged" in del_res.json()["message"]

    # 3. Confirm all dependent entities are purged from the database
    with get_db() as conn:
        assert conn.execute("SELECT COUNT(*) as c FROM beneficiaries WHERE id = ?;", (ben_id,)).fetchone()["c"] == 0
        assert conn.execute("SELECT COUNT(*) as c FROM interview_sessions WHERE beneficiary_id = ?;", (ben_id,)).fetchone()["c"] == 0
        assert conn.execute("SELECT COUNT(*) as c FROM interview_turns WHERE interview_id = ?;", (int_id,)).fetchone()["c"] == 0
        assert conn.execute("SELECT COUNT(*) as c FROM profile_field_values WHERE interview_id = ?;", (int_id,)).fetchone()["c"] == 0
        assert conn.execute("SELECT COUNT(*) as c FROM recommendations WHERE beneficiary_id = ?;", (ben_id,)).fetchone()["c"] == 0
        assert conn.execute("SELECT COUNT(*) as c FROM consent_records WHERE beneficiary_id = ?;", (ben_id,)).fetchone()["c"] == 0

        # Verify minimal non-identifying audit event is retained
        audit_row = conn.execute("""
            SELECT * FROM audit_events
            WHERE action = 'PROFILE_DELETED_RIGHT_TO_ERASURE'
              AND entity_id = ?;
        """, (ben_id,)).fetchone()
        assert audit_row is not None
        assert audit_row["actor_role"] == "beneficiary"
