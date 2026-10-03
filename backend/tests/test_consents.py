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
    orig_key = settings.WORKER_API_KEY
    orig_counselor_key = settings.COUNSELOR_API_KEY
    orig_admin_key = settings.ADMIN_API_KEY
    temp_dir = tempfile.TemporaryDirectory()
    settings.DATABASE_PATH = os.path.join(temp_dir.name, "test_consent.db")
    settings.WORKER_API_KEY = "test-worker-key"
    settings.COUNSELOR_API_KEY = "test-counselor-key"
    settings.ADMIN_API_KEY = "test-admin-key"
    init_database()

    with TestClient(app) as c:
        yield c

    settings.DATABASE_PATH = orig_db
    settings.WORKER_API_KEY = orig_key
    settings.COUNSELOR_API_KEY = orig_counselor_key
    settings.ADMIN_API_KEY = orig_admin_key
    temp_dir.cleanup()

def test_consent_recording_and_versioning(client):
    # Create session
    sess_res = client.post("/api/v1/sessions", json={"owner_type": "anonymous"})
    assert sess_res.status_code == 201
    session_id = sess_res.json()["session_id"]
    session_headers = {"X-Session-Token": sess_res.json()["session_token"]}

    # Record versioned consent
    consent_res = client.post("/api/v1/consents", json={
        "session_id": session_id,
        "consent_type": "ai_processing",
        "policy_version": "1.0",
        "user_language": "hi",
        "capture_channel": "web_app",
        "granted": True
    }, headers=session_headers)
    assert consent_res.status_code == 201
    consent_data = consent_res.json()
    assert consent_data["consent_type"] == "ai_processing"
    assert consent_data["policy_version"] == "1.0"
    assert consent_data["status"] == "granted"

    # Query consents for session
    get_res = client.get(f"/api/v1/consents/{session_id}", headers=session_headers)
    assert get_res.status_code == 200
    records = get_res.json()
    assert len(records) >= 1
    assert records[0]["session_id"] == session_id

def test_ai_processing_blocked_without_consent(client):
    sess_res = client.post("/api/v1/sessions")
    session_id = sess_res.json()["session_id"]
    session_headers = {"X-Session-Token": sess_res.json()["session_token"]}

    # Starting interview without ai_processing consent should fail with 403
    start_res = client.post("/api/v1/interviews/start", json={
        "session_id": session_id,
        "language": "hi"
    }, headers=session_headers)
    assert start_res.status_code == 403
    err = start_res.json()
    assert err["error"]["code"] == "CONSENT_REQUIRED"

def test_consent_revocation_blocks_subsequent_actions(client):
    sess_res = client.post("/api/v1/sessions")
    session_id = sess_res.json()["session_id"]
    session_headers = {"X-Session-Token": sess_res.json()["session_token"]}

    # Grant consent
    consent_res = client.post("/api/v1/consents", json={
        "session_id": session_id,
        "consent_type": "ai_processing",
        "granted": True
    }, headers=session_headers)
    assert consent_res.status_code == 201
    consent_id = consent_res.json()["id"]

    # Start interview succeeds
    start_res = client.post("/api/v1/interviews/start", json={
        "session_id": session_id,
        "language": "hi"
    }, headers=session_headers)
    assert start_res.status_code == 201
    interview_id = start_res.json()["interview_id"]

    # Revoke consent
    revoke_res = client.post(f"/api/v1/consents/{consent_id}/revoke", json={
        "reason": "Beneficiary decided to stop processing"
    }, headers=session_headers)
    assert revoke_res.status_code == 200
    assert revoke_res.json()["status"] == "revoked"

    # Future interview turns must be blocked with 403 CONSENT_REVOKED
    turn_res = client.post(f"/api/v1/interviews/{interview_id}/turns", json={
        "message": "I know basic wiring"
    }, headers=session_headers)
    assert turn_res.status_code == 403
    assert turn_res.json()["error"]["code"] == "CONSENT_REVOKED"

def test_counselor_referral_consent_required_and_revocation(client):
    sess_res = client.post("/api/v1/sessions")
    session_id = sess_res.json()["session_id"]
    session_headers = {"X-Session-Token": sess_res.json()["session_token"]}

    # Try creating referral without counselor_referral consent -> 403
    ref_fail = client.post("/api/v1/referrals", json={
        "interview_id": session_id,
        "referral_reason": "no_verified_local_option",
        "notes": "Needs human assistance"
    }, headers=session_headers)
    assert ref_fail.status_code == 403

    # Grant counselor_referral consent
    c_res = client.post("/api/v1/consents", json={
        "session_id": session_id,
        "consent_type": "counselor_referral",
        "granted": True
    }, headers=session_headers)
    assert c_res.status_code == 201
    c_id = c_res.json()["id"]

    # Now referral creation succeeds
    ref_ok = client.post("/api/v1/referrals", json={
        "interview_id": session_id,
        "referral_reason": "no_verified_local_option",
        "notes": "Needs human assistance"
    }, headers=session_headers)
    assert ref_ok.status_code == 201
    assert ref_ok.json()["status"] == "new"

    # Revoke counselor_referral consent
    client.post(f"/api/v1/consents/{c_id}/revoke", json={"reason": "Revoked consent"}, headers=session_headers)

    # Post-revocation: active referral case should be closed automatically
    my_refs = client.get("/api/v1/referrals/me", headers=session_headers)
    assert my_refs.status_code == 200
    cases = my_refs.json()
    assert len(cases) > 0
    assert cases[0]["status"] == "closed"

def test_anonymous_session_consent_with_dual_headers(client):
    # Create anonymous session
    sess_res = client.post("/api/v1/sessions", json={"owner_type": "anonymous"})
    assert sess_res.status_code == 201
    session_id = sess_res.json()["session_id"]
    session_token = sess_res.json()["session_token"]
    
    headers = {
        "X-Session-ID": session_id,
        "X-Session-Token": session_token
    }

    # Record consent with standard anonymous payload
    consent_res = client.post("/api/v1/consents", json={
        "session_id": session_id,
        "consent_type": "ai_processing",
        "granted": True
    }, headers=headers)
    assert consent_res.status_code == 201
    consent_data = consent_res.json()
    assert consent_data["session_id"] == session_id
    assert consent_data["consent_type"] == "ai_processing"
    assert consent_data["status"] == "granted"

    # Start interview should succeed now
    start_res = client.post("/api/v1/interviews/start", json={
        "session_id": session_id,
        "language": "hi"
    }, headers=headers)
    assert start_res.status_code == 201
    assert start_res.json()["status"] == "collecting"

def test_anonymous_session_consent_inferred_from_headers(client):
    sess_res = client.post("/api/v1/sessions")
    session_id = sess_res.json()["session_id"]
    session_token = sess_res.json()["session_token"]
    headers = {
        "X-Session-ID": session_id,
        "X-Session-Token": session_token
    }

    # Record consent without session_id in the json body
    consent_res = client.post("/api/v1/consents", json={
        "consent_type": "ai_processing",
        "granted": True
    }, headers=headers)
    assert consent_res.status_code == 201
    assert consent_res.json()["session_id"] == session_id

def test_legacy_consent_payload_with_session(client):
    sess_res = client.post("/api/v1/sessions")
    session_id = sess_res.json()["session_id"]
    session_token = sess_res.json()["session_token"]
    headers = {
        "X-Session-ID": session_id,
        "X-Session-Token": session_token
    }

    # Legacy format consent with session_id
    consent_res = client.post("/api/v1/consents", json={
        "session_id": session_id,
        "dpdp_affirmative_consent": True
    }, headers=headers)
    assert consent_res.status_code == 201
    assert consent_res.json()["session_id"] == session_id
    assert consent_res.json()["status"] == "granted"

def test_legacy_consent_with_beneficiary(client):
    # Record legacy consent for an existing beneficiary via field worker
    worker_headers = {"X-Worker-API-Key": settings.WORKER_API_KEY}
    consent_res = client.post("/api/v1/consents", json={
        "beneficiary_id": "ben_rajesh_kumar",
        "purpose": "PM-AJAY livelihood guidance",
        "dpdp_affirmative_consent": True
    }, headers=worker_headers)
    assert consent_res.status_code == 201
    assert consent_res.json()["beneficiary_id"] == "ben_rajesh_kumar"
    assert consent_res.json()["status"] == "granted"

def test_consent_security_mismatched_session_rejected(client):
    sess_res = client.post("/api/v1/sessions")
    session_token = sess_res.json()["session_token"]
    headers = {"X-Session-Token": session_token}

    # Attempt to record consent for a different session_id -> 403 Forbidden
    consent_res = client.post("/api/v1/consents", json={
        "session_id": "sess_another_session_123",
        "consent_type": "ai_processing",
        "granted": True
    }, headers=headers)
    assert consent_res.status_code == 403

