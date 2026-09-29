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
    settings.DATABASE_PATH = os.path.join(temp_dir.name, "test_interviews.db")
    init_database()

    with TestClient(app) as c:
        yield c

    settings.DATABASE_PATH = orig_db
    temp_dir.cleanup()

def test_interview_lifecycle_and_provenance(client):
    # 1. Start anonymous session & consent
    sess_res = client.post("/api/v1/sessions")
    assert sess_res.status_code == 201
    session_id = sess_res.json()["session_id"]

    client.post("/api/v1/consents", json={
        "session_id": session_id,
        "consent_type": "ai_processing",
        "granted": True
    })

    # 2. Start interview
    start_res = client.post("/api/v1/interviews/start", json={
        "session_id": session_id,
        "language": "hi"
    })
    assert start_res.status_code == 201
    start_data = start_res.json()
    interview_id = start_data["interview_id"]
    assert start_data["status"] == "collecting"

    # 3. User message extracting multiple fields (education + interest + mobility)
    turn_res = client.post(f"/api/v1/interviews/{interview_id}/turns", json={
        "message": "मैंने 10वीं पास की है और मुझे सोलर व बिजली रिपेयर में रुचि है। मैं 3 किमी तक जा सकता हूँ।"
    }, headers={"X-Session-ID": session_id})
    assert turn_res.status_code == 200
    turn_data = turn_res.json()
    assert turn_data["status"] == "collecting"

    # 4. Verify AI-inferred fields exist but are unconfirmed
    int_detail = client.get(f"/api/v1/interviews/{interview_id}", headers={"X-Session-ID": session_id})
    assert int_detail.status_code == 200
    fields = int_detail.json()["fields"]
    assert "education" in fields
    assert fields["education"]["source"] == "ai_inferred"
    assert fields["education"]["user_confirmed"] is False

    # 5. User confirmation changes fields to confirmed & status to ready_for_matching
    confirm_res = client.post(f"/api/v1/interviews/{interview_id}/confirm-profile", json={
        "session_id": session_id,
        "confirmed_fields": {
            "education": "Class 10",
            "interests": ["Solar PV Installation"],
            "mobility": 5.0,
            "district": "Moradabad",
            "block": "Chhajlet"
        }
    }, headers={"X-Session-ID": session_id})
    assert confirm_res.status_code == 200
    assert confirm_res.json()["status"] == "ready_for_matching"

    # 6. Verify confirmed fields updated to user-confirmed
    int_after = client.get(f"/api/v1/interviews/{interview_id}", headers={"X-Session-ID": session_id})
    confirmed_fields = int_after.json()["fields"]
    assert confirmed_fields["education"]["user_confirmed"] is True
    assert confirmed_fields["education"]["source"] == "user"

    # 7. User edits mobility field individually
    patch_res = client.patch(
        f"/api/v1/interviews/{interview_id}/fields/mobility",
        json={"value": 10.0, "source": "user"},
        headers={"X-Session-ID": session_id}
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["new_value"] == 10.0

    # 8. Resume incomplete interview check
    resume_get = client.get(f"/api/v1/interviews/{interview_id}", headers={"X-Session-ID": session_id})
    assert resume_get.status_code == 200
    assert resume_get.json()["fields"]["mobility"]["value"] == 10.0
