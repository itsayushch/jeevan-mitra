import os
import tempfile
import pytest
from fastapi.testclient import TestClient
from app.config import settings
from app.database import init_database
from app.main import app


@pytest.fixture
def client():
    orig_db = settings.DATABASE_PATH
    temp_dir = tempfile.TemporaryDirectory()
    settings.DATABASE_PATH = os.path.join(temp_dir.name, "test_ivr_api.db")
    settings.IVR_SIMULATOR_ENABLED = True
    init_database()

    with TestClient(app) as c:
        yield c

    settings.DATABASE_PATH = orig_db
    temp_dir.cleanup()


def test_api_full_journey(client):
    # 1. Start session
    start_res = client.post(
        "/api/v1/ivr/simulate/start",
        json={"simulated_caller_reference": "9876543210", "language": "hi-IN"},
    )
    assert start_res.status_code == 201
    data = start_res.json()
    session_id = data["session_id"]
    assert data["state"] == "welcome"
    assert data["status"] == "active"
    assert "नमस्ते" in data["prompt_text"]
    assert "9876543210" not in str(data)  # Redaction check

    # 2. Press 1 -> Consent
    r1 = client.post(f"/api/v1/ivr/simulate/{session_id}/input", json={"digit": "1"})
    assert r1.status_code == 200
    d1 = r1.json()
    assert d1["state"] == "consent"
    assert d1["previous_state"] == "welcome"

    # 3. Press 1 -> Identity (Consent granted)
    r2 = client.post(f"/api/v1/ivr/simulate/{session_id}/input", json={"digit": "1"})
    assert r2.status_code == 200
    d2 = r2.json()
    assert d2["state"] == "identity"

    # 4. Press 1 -> Main Menu
    r3 = client.post(f"/api/v1/ivr/simulate/{session_id}/input", json={"digit": "1"})
    assert r3.status_code == 200
    d3 = r3.json()
    assert d3["state"] == "main_menu"

    # 5. Press 1 -> Training
    r4 = client.post(f"/api/v1/ivr/simulate/{session_id}/input", json={"digit": "1"})
    assert r4.status_code == 200
    d4 = r4.json()
    assert d4["state"] == "training"

    # 6. Press 0 -> Callback Request (training_support)
    r5 = client.post(f"/api/v1/ivr/simulate/{session_id}/input", json={"digit": "0"})
    assert r5.status_code == 200
    d5 = r5.json()
    assert d5["state"] == "callback_request"
    assert d5["callback_request"] is not None
    assert d5["callback_request"]["callback_reason"] == "training_support"

    # 7. Press 2 -> Goodbye
    r6 = client.post(f"/api/v1/ivr/simulate/{session_id}/input", json={"digit": "2"})
    assert r6.status_code == 200
    d6 = r6.json()
    assert d6["state"] == "goodbye"
    assert d6["status"] == "completed"

    # 8. View Session detail
    sess_res = client.get(f"/api/v1/ivr/simulate/{session_id}")
    assert sess_res.status_code == 200
    sess_data = sess_res.json()
    assert sess_data["state"] == "goodbye"
    assert sess_data["status"] == "completed"
    assert "9876543210" not in str(sess_data)

    # 9. View Session Events
    events_res = client.get(f"/api/v1/ivr/simulate/{session_id}/events")
    assert events_res.status_code == 200
    events = events_res.json()
    assert len(events) >= 6
    assert events[0]["event_type"] == "session_started"
    assert "9876543210" not in str(events)


def test_api_invalid_session_id(client):
    res = client.get("/api/v1/ivr/simulate/ivrs_nonexistent999")
    assert res.status_code == 404
    err = res.json()
    assert "not found" in str(err).lower()


def test_api_invalid_digit_validation_error(client):
    start_res = client.post("/api/v1/ivr/simulate/start", json={})
    session_id = start_res.json()["session_id"]

    # Invalid DTMF digit 'xyz' should trigger 422 Unprocessable Entity
    res = client.post(f"/api/v1/ivr/simulate/{session_id}/input", json={"digit": "xyz"})
    assert res.status_code == 422


def test_api_route_prefix_compatibility(client):
    # Verify both /api/v1/ivr/... and /api/ivr/... work
    r1 = client.post("/api/v1/ivr/simulate/start", json={})
    assert r1.status_code == 201

    r2 = client.post("/api/ivr/simulate/start", json={})
    assert r2.status_code == 201


def test_api_force_expire_endpoint(client):
    start_res = client.post("/api/v1/ivr/simulate/start", json={})
    session_id = start_res.json()["session_id"]

    exp_res = client.post(f"/api/v1/ivr/simulate/{session_id}/expire")
    assert exp_res.status_code == 200
    exp_data = exp_res.json()
    assert exp_data["state"] == "expired"
    assert exp_data["status"] == "expired"

    # Input after expiry must not alter state
    inp_res = client.post(
        f"/api/v1/ivr/simulate/{session_id}/input", json={"digit": "1"}
    )
    assert inp_res.status_code == 200
    inp_data = inp_res.json()
    assert inp_data["state"] == "expired"
    assert inp_data["status"] == "expired"


def test_api_disabled_simulator(client):
    settings.IVR_SIMULATOR_ENABLED = False
    res = client.post("/api/v1/ivr/simulate/start", json={})
    assert res.status_code == 403
    settings.IVR_SIMULATOR_ENABLED = True


def test_api_consent_refusal_terminated(client):
    start_res = client.post("/api/v1/ivr/simulate/start", json={})
    sess_id = start_res.json()["session_id"]

    # Press 1 -> Consent
    r1 = client.post(f"/api/v1/ivr/simulate/{sess_id}/input", json={"digit": "1"})
    assert r1.status_code == 200
    assert r1.json()["state"] == "consent"

    # Press 2 -> Refuse consent -> Goodbye (terminated)
    r2 = client.post(f"/api/v1/ivr/simulate/{sess_id}/input", json={"digit": "2"})
    assert r2.status_code == 200
    d2 = r2.json()
    assert d2["state"] == "goodbye"
    assert d2["status"] == "terminated"


def test_privacy_ivr_001_symbolic_caller_reference_exclusion(client):
    """
    PRIVACY-IVR-001:
    Start a session with symbolic reference 'TEST_CALLER_A'.
    Assert raw reference is completely absent from all API responses,
    session responses, callback data, and event history.
    """
    raw_ref = "TEST_CALLER_A"

    # 1. Start session
    start_res = client.post(
        "/api/v1/ivr/simulate/start",
        json={"simulated_caller_reference": raw_ref, "language": "hi-IN"},
    )
    assert start_res.status_code == 201
    start_json = start_res.json()
    assert raw_ref not in str(start_json)
    sess_id = start_json["session_id"]

    # 2. Advance through welcome -> consent -> identity -> main_menu -> training -> callback
    for digit in ["1", "1", "1", "1"]:
        step_res = client.post(
            f"/api/v1/ivr/simulate/{sess_id}/input", json={"digit": digit}
        )
        assert step_res.status_code == 200
        assert raw_ref not in str(step_res.json())

    # 3. Request callback (digit 0)
    cb_res = client.post(
        f"/api/v1/ivr/simulate/{sess_id}/input", json={"digit": "0"}
    )
    assert cb_res.status_code == 200
    cb_json = cb_res.json()
    assert raw_ref not in str(cb_json)
    assert cb_json["callback_request"] is not None
    assert raw_ref not in str(cb_json["callback_request"])

    # 4. GET /simulate/{sess_id}
    detail_res = client.get(f"/api/v1/ivr/simulate/{sess_id}")
    assert detail_res.status_code == 200
    assert raw_ref not in str(detail_res.json())

    # 5. GET /simulate/{sess_id}/events
    events_res = client.get(f"/api/v1/ivr/simulate/{sess_id}/events")
    assert events_res.status_code == 200
    assert raw_ref not in str(events_res.json())


def test_privacy_ivr_002_numeric_caller_reference_exclusion(client):
    """
    PRIVACY-IVR-002:
    Start a session using synthetic numeric reference '9811000001'.
    Assert every response body, callback response, session response,
    and event response completely excludes '9811000001'.
    """
    raw_phone = "9811000001"

    start_res = client.post(
        "/api/v1/ivr/simulate/start",
        json={"simulated_caller_reference": raw_phone, "language": "hi-IN"},
    )
    assert start_res.status_code == 201
    assert raw_phone not in str(start_res.json())
    sess_id = start_res.json()["session_id"]

    # Welcome -> Consent -> Identity -> Main Menu -> Training -> Callback
    for digit in ["1", "1", "1", "1"]:
        inp_res = client.post(
            f"/api/v1/ivr/simulate/{sess_id}/input", json={"digit": digit}
        )
        assert raw_phone not in str(inp_res.json())

    cb_res = client.post(
        f"/api/v1/ivr/simulate/{sess_id}/input", json={"digit": "0"}
    )
    cb_json = cb_res.json()
    assert raw_phone not in str(cb_json)

    # Ensure callback_request contains only safe schema fields
    cb_obj = cb_json["callback_request"]
    assert "caller_phone" not in cb_obj
    assert "caller_reference" not in cb_obj
    assert set(cb_obj.keys()).issubset(
        {"id", "session_id", "beneficiary_id", "callback_reason", "status", "created_at"}
    )

    detail_res = client.get(f"/api/v1/ivr/simulate/{sess_id}")
    assert raw_phone not in str(detail_res.json())

    events_res = client.get(f"/api/v1/ivr/simulate/{sess_id}/events")
    assert raw_phone not in str(events_res.json())


def test_privacy_ivr_004_masking_rule_compliance():
    """
    PRIVACY-IVR-004:
    Verify phone number masking utility preserves only trailing 4 digits
    and sanitizes payloads for logging.
    """
    from app.ivr.security import mask_phone_number, sanitize_payload_for_logging

    masked = mask_phone_number("9811000001")
    assert masked == "******0001"
    assert "981100" not in masked

    sanitized = sanitize_payload_for_logging({
        "phone": "9811000001",
        "secret": "super_secret_token",
        "nested": {"caller_reference": "9876543210"}
    })
    assert sanitized["phone"] == "******0001"
    assert sanitized["secret"] == "[REDACTED]"
    assert sanitized["nested"]["caller_reference"] == "[REDACTED]"
