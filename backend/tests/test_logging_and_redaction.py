import json
import logging
from fastapi.testclient import TestClient
from app.main import app
from app.core.logging import redact_text, redact_data, RedactingJsonFormatter

client = TestClient(app)


def test_request_id_generated_when_missing():
    response = client.get("/health/live")
    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    assert len(response.headers["X-Request-ID"]) >= 16


def test_request_id_preserved_when_provided():
    custom_id = "test-custom-request-id-12345"
    response = client.get("/health/live", headers={"X-Request-ID": custom_id})
    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == custom_id


def test_security_headers_present():
    response = client.get("/health/live")
    assert response.status_code == 200
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert "default-src 'self'" in response.headers["Content-Security-Policy"]


def test_sensitive_cache_control_headers():
    response = client.get("/api/v1/auth/me")
    # Even if 401 Unauthorized, sensitive routes should have no-store cache control
    assert "no-store" in response.headers.get("Cache-Control", "")


def test_redact_text_tokens_and_passwords():
    raw_jwt = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.doNotLeakThisSignature"
    redacted = redact_text(raw_jwt)
    assert "[REDACTED" in redacted
    assert "doNotLeakThisSignature" not in redacted

    raw_json = '{"user": "worker", "password": "supersecretpassword123", "secret": "shhh"}'
    redacted_json = redact_text(raw_json)
    assert "supersecretpassword123" not in redacted_json
    assert "[REDACTED]" in redacted_json


def test_redact_text_pii_phone_aadhaar_email():
    text = "Beneficiary phone is +91 9876543210, Aadhaar 1234 5678 9012, email test.user@example.com"
    redacted = redact_text(text)
    assert "9876543210" not in redacted
    assert "1234 5678 9012" not in redacted
    assert "test.user@example.com" not in redacted
    assert "[REDACTED_PHONE]" in redacted
    assert "[REDACTED_AADHAAR]" in redacted
    assert "[REDACTED_EMAIL]" in redacted


def test_redact_data_nested_dict():
    payload = {
        "user_id": "usr-123",
        "password": "mypassword",
        "profile": {
            "phone": "9876543210",
            "raw_transcript": "User wants training in Moradabad but has debt",
            "diary_notes": "Beneficiary expressed urgent livelihood distress",
            "qualification": "Solar Technician"
        }
    }
    cleaned = redact_data(payload)
    assert cleaned["password"] == "[REDACTED]"
    assert cleaned["profile"]["phone"] == "[REDACTED]"
    assert cleaned["profile"]["raw_transcript"] == "[REDACTED]"
    assert cleaned["profile"]["diary_notes"] == "[REDACTED]"
    assert cleaned["profile"]["qualification"] == "Solar Technician"
    assert cleaned["user_id"] == "usr-123"


def test_redacting_json_formatter():
    formatter = RedactingJsonFormatter()
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=10,
        msg="User authenticated with Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0In0.secretSig",
        args=(),
        exc_info=None
    )
    formatted = formatter.format(record)
    parsed = json.loads(formatted)
    assert parsed["level"] == "INFO"
    assert "secretSig" not in parsed["message"]
    assert "[REDACTED_JWT]" in parsed["message"]
