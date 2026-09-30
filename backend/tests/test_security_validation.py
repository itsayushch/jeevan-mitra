import pytest
import uuid
import jwt
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db
from app.core.settings import settings
from app.core.security import create_access_token

client = TestClient(app)


@pytest.fixture(scope="module")
def setup_security_fixtures():
    """Seeds test beneficiaries, workers, and cases for security validation."""
    now_iso = datetime.now(timezone.utc).isoformat()
    with get_db() as conn:
        # Beneficiary A (Moradabad)
        conn.execute("""
            INSERT OR REPLACE INTO users (id, email, phone, display_name, is_active, preferred_language, created_at, updated_at)
            VALUES ('usr_sec_ben_a', 'ben.a@example.com', '9811111111', 'Beneficiary A', 1, 'hi', ?, ?);
        """, (now_iso, now_iso))
        conn.execute("INSERT OR REPLACE INTO user_roles (user_id, role_id, assigned_at) VALUES ('usr_sec_ben_a', 'role_beneficiary', ?);", (now_iso,))
        conn.execute("""
            INSERT OR REPLACE INTO beneficiaries (id, name, phone, district, block, preferred_language, created_at, updated_at)
            VALUES ('ben_sec_a', 'Beneficiary A', '9811111111', 'Moradabad', 'Chhajlet', 'hi', ?, ?);
        """, (now_iso, now_iso))

        # Beneficiary B (Moradabad)
        conn.execute("""
            INSERT OR REPLACE INTO users (id, email, phone, display_name, is_active, preferred_language, created_at, updated_at)
            VALUES ('usr_sec_ben_b', 'ben.b@example.com', '9822222222', 'Beneficiary B', 1, 'hi', ?, ?);
        """, (now_iso, now_iso))
        conn.execute("INSERT OR REPLACE INTO user_roles (user_id, role_id, assigned_at) VALUES ('usr_sec_ben_b', 'role_beneficiary', ?);", (now_iso,))
        conn.execute("""
            INSERT OR REPLACE INTO beneficiaries (id, name, phone, district, block, preferred_language, created_at, updated_at)
            VALUES ('ben_sec_b', 'Beneficiary B', '9822222222', 'Moradabad', 'Chhajlet', 'hi', ?, ?);
        """, (now_iso, now_iso))

        # Case for Beneficiary B
        conn.execute("""
            INSERT OR REPLACE INTO beneficiary_cases (
                id, beneficiary_id, district_id, block_id, case_status, priority, intake_source, created_at, updated_at
            ) VALUES ('case_sec_b', 'ben_sec_b', 'Moradabad', 'Chhajlet', 'OPEN', 'NORMAL', 'WEB', ?, ?);
        """, (now_iso, now_iso))

        # Moradabad District Admin
        conn.execute("""
            INSERT OR REPLACE INTO users (id, email, phone, display_name, is_active, preferred_language, created_at, updated_at)
            VALUES ('usr_sec_admin_mbd', 'admin.sec.mbd@up.gov.in', '9833333333', 'Moradabad Admin Sec', 1, 'hi', ?, ?);
        """, (now_iso, now_iso))
        conn.execute("INSERT OR REPLACE INTO user_roles (user_id, role_id, assigned_at) VALUES ('usr_sec_admin_mbd', 'role_district_admin', ?);", (now_iso,))
        conn.execute("""
            INSERT OR REPLACE INTO user_scopes (id, user_id, district_id, scope_type, assigned_at)
            VALUES ('scope_sec_admin_mbd', 'usr_sec_admin_mbd', 'Moradabad', 'district', ?);
        """, (now_iso,))

        # Field Worker (Moradabad)
        conn.execute("""
            INSERT OR REPLACE INTO users (id, email, phone, display_name, is_active, preferred_language, created_at, updated_at)
            VALUES ('usr_sec_worker_mbd', 'worker.sec.mbd@up.gov.in', '9844444444', 'Moradabad Worker Sec', 1, 'hi', ?, ?);
        """, (now_iso, now_iso))
        conn.execute("INSERT OR REPLACE INTO user_roles (user_id, role_id, assigned_at) VALUES ('usr_sec_worker_mbd', 'role_field_worker', ?);", (now_iso,))
        conn.execute("""
            INSERT OR REPLACE INTO user_scopes (id, user_id, district_id, scope_type, assigned_at)
            VALUES ('scope_sec_worker_mbd', 'usr_sec_worker_mbd', 'Moradabad', 'district', ?);
        """, (now_iso,))


def _token_for(user_id: str) -> str:
    return create_access_token(
        subject=user_id,
        session_id=f"sess_{uuid.uuid4().hex[:8]}",
        expires_delta=timedelta(hours=1)
    )


def test_idor_beneficiary_cannot_read_another_beneficiary_case(setup_security_fixtures):
    """Verifies Beneficiary A cannot view Beneficiary B's case detail."""
    token_a = _token_for("usr_sec_ben_a")
    headers = {"Authorization": f"Bearer {token_a}"}

    # Case B belongs to Beneficiary B
    response = client.get("/api/v1/me/cases/case_sec_b", headers=headers)
    assert response.status_code == 404
    assert "not found" in response.json().get("detail", "").lower()


def test_cross_district_isolation_for_district_admin(setup_security_fixtures):
    """Verifies Moradabad district admin cannot access Varanasi planning data."""
    token = _token_for("usr_sec_admin_mbd")
    headers = {"Authorization": f"Bearer {token}"}

    # Attempt cross-district planning access for Varanasi
    response = client.get("/api/v1/planning/overview?district_id=Varanasi", headers=headers)
    assert response.status_code == 403
    assert "access denied" in response.json().get("detail", "").lower()
    assert "varanasi" in response.json().get("detail", "").lower()


def test_role_escalation_worker_cannot_create_planning_snapshot(setup_security_fixtures):
    """Verifies field worker cannot trigger immutable snapshot creation."""
    token = _token_for("usr_sec_worker_mbd")
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "district_id": "Moradabad",
        "period_start": "2026-01-01",
        "period_end": "2026-12-31"
    }
    response = client.post("/api/v1/planning/snapshots", json=payload, headers=headers)
    assert response.status_code == 403


def test_role_escalation_beneficiary_cannot_access_staff_cases(setup_security_fixtures):
    """Verifies beneficiary cannot access staff inbox."""
    token = _token_for("usr_sec_ben_a")
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/api/v1/staff/cases", headers=headers)
    assert response.status_code == 403


def test_jwt_forged_signature_rejected():
    """Verifies token signed with attacker secret is rejected."""
    tampered_token = jwt.encode(
        {"sub": "usr_sec_admin_mbd", "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
        "attacker_fake_jwt_secret_key_12345",
        algorithm="HS256"
    )
    headers = {"Authorization": f"Bearer {tampered_token}"}
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 401


def test_jwt_expired_token_rejected():
    """Verifies expired token is rejected."""
    expired_token = jwt.encode(
        {"sub": "usr_sec_admin_mbd", "exp": datetime.now(timezone.utc) - timedelta(hours=2)},
        settings.JWT_SECRET,
        algorithm="HS256"
    )
    headers = {"Authorization": f"Bearer {expired_token}"}
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 401


def test_jwt_garbage_token_rejected():
    """Verifies malformed string token is rejected."""
    headers = {"Authorization": "Bearer this.is.garbage"}
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 401


def test_sql_injection_resilience_in_district_parameter(setup_security_fixtures):
    """Verifies SQL injection payload is safely parameterized without crashing database."""
    token = _token_for("usr_sec_admin_mbd")
    headers = {"Authorization": f"Bearer {token}"}

    sqli_payload = "Moradabad' OR '1'='1' --"
    response = client.get(f"/api/v1/planning/overview?district_id={sqli_payload}", headers=headers)
    # Should be rejected by scope check or return 403 / safe 404, never a 500 SQL syntax error
    assert response.status_code in (403, 404, 422)


def test_xss_payload_in_submission_stored_safely(setup_security_fixtures):
    """Verifies XSS payload in text submission is safely accepted without execution."""
    token = _token_for("usr_sec_admin_mbd")
    headers = {"Authorization": f"Bearer {token}"}

    xss_payload = {
        "input_mode": "text",
        "text": "<script>alert('xss')</script> Workshop near mandi",
        "locale": "en"
    }
    response = client.post("/api/v1/opportunity-submissions", json=xss_payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "SUBMITTED"
    assert "<script>" in data["normalized_text"]  # Stored verbatim, not executed
