import pytest
import uuid
import jwt
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db
from app.core.settings import settings
from app.core.security import create_access_token
from app.core.logging import redact_text, redact_data
from app.schemas.locale import resolve_locale, SupportedLocale
from app.services.opportunity_verification_service import OpportunityVerificationService
from app.services.planning_export_service import PlanningExportService

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
        conn.commit()

    yield

    with get_db() as conn:
        conn.execute("DELETE FROM beneficiary_cases WHERE id = 'case_sec_b';")
        conn.execute("DELETE FROM beneficiaries WHERE id IN ('ben_sec_a', 'ben_sec_b');")
        conn.execute("DELETE FROM user_scopes WHERE id IN ('scope_sec_admin_mbd', 'scope_sec_worker_mbd');")
        conn.execute("DELETE FROM user_roles WHERE user_id IN ('usr_sec_ben_a', 'usr_sec_ben_b', 'usr_sec_admin_mbd', 'usr_sec_worker_mbd');")
        conn.execute("DELETE FROM users WHERE id IN ('usr_sec_ben_a', 'usr_sec_ben_b', 'usr_sec_admin_mbd', 'usr_sec_worker_mbd');")
        conn.commit()


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
    assert response.json()["detail"]["error"] == "DISTRICT_SCOPE_VIOLATION"
    assert response.json()["detail"]["attempted_district"] == "Varanasi"


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
    # Clean up submission
    if "id" in data:
        with get_db() as conn:
            conn.execute("DELETE FROM opportunity_submissions WHERE id = ?", (data["id"],))
            conn.commit()


def test_refresh_token_missing_or_invalid_rejected():
    """Verifies refresh endpoint rejects missing/invalid refresh token cookie."""
    response = client.post("/api/v1/auth/refresh")
    assert response.status_code == 401


def test_scope_revocation_prevents_export_download(setup_security_fixtures):
    """If user's district scope is revoked after export is created, download must be rejected."""
    token = _token_for("usr_sec_admin_mbd")
    headers = {"Authorization": f"Bearer {token}"}
    now = datetime.now(timezone.utc).isoformat()

    # 1. Seed snapshot and export for Moradabad
    with get_db() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO planning_snapshots (
                id, district_id, period_start, period_end, generated_by_user_id,
                generated_at, metric_version, data_freshness_at, status
            ) VALUES ('snap_sec_rev', 'Moradabad', '2026-07-01', '2026-09-30', 'usr_sec_admin_mbd', ?, 'v1', ?, 'APPROVED');
        """, (now, now))
        conn.execute("""
            INSERT OR REPLACE INTO planning_exports (
                id, snapshot_id, export_type, export_scope, requested_by_user_id,
                generated_at, expires_at, status, storage_key, checksum, download_count, created_at
            ) VALUES (
                'exp_sec_rev', 'snap_sec_rev', 'CSV', 'FULL_REPORT', 'usr_sec_admin_mbd',
                ?, '2026-10-07T00:00:00Z', 'AVAILABLE', 'evidence/exports/sec_rev.csv',
                'dummy_checksum', 0, ?
            );
        """, (now, now))
        conn.commit()

    # 2. Revoke admin's district scope
    with get_db() as conn:
        conn.execute("DELETE FROM user_scopes WHERE user_id = 'usr_sec_admin_mbd';")
        conn.commit()

    try:
        # 3. Attempt download after revocation
        res = client.get("/api/v1/planning/exports/exp_sec_rev/download", headers=headers)
        assert res.status_code == 403
    finally:
        # Restore scope and cleanup snapshot & export
        with get_db() as conn:
            conn.execute("DELETE FROM planning_exports WHERE id = 'exp_sec_rev';")
            conn.execute("DELETE FROM planning_snapshots WHERE id = 'snap_sec_rev';")
            conn.execute("""
                INSERT OR REPLACE INTO user_scopes (id, user_id, district_id, scope_type, assigned_at)
                VALUES ('scope_sec_admin_mbd', 'usr_sec_admin_mbd', 'Moradabad', 'district', ?);
            """, (now,))
            conn.commit()


def test_csv_formula_injection_and_xss_neutralization():
    """Verifies CSV cells neutralize formula injection prefixes and escape script tags."""
    dangerous_inputs = [
        "=cmd|'/C calc'!A0",
        "+cmd|'/C calc'!A0",
        "@SUM(A1:A10)",
        "-2+3*cmd",
        "<script>alert('xss')</script>",
        "Safe Standard Value"
    ]
    for val in dangerous_inputs:
        cleaned = PlanningExportService._sanitize_csv_cell(val)
        if val.startswith(("=", "+", "@", "-")):
            assert cleaned.startswith("'")
        assert "<script>" not in cleaned


def test_file_upload_abuse_prevention_for_evidence(setup_security_fixtures):
    """Path traversal filenames and executable extensions must be rejected for evidence uploads."""
    now = datetime.now(timezone.utc).isoformat()
    with get_db() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO qualifications (id, title, description, sector, nsqf_level, min_education_rank, verification_status, created_at, updated_at)
            VALUES ('q_sec_upload', 'Test Course', 'Description', 'Electronics', 4, 3, 'VERIFIED', ?, ?);
        """, (now, now))
        conn.execute("""
            INSERT OR REPLACE INTO local_opportunities (
                id, qualification_id, title, summary, district_id, block_id,
                seats_total, seats_available, status, verification_expires_at, created_at, updated_at
            ) VALUES (
                'opp_sec_upload', 'q_sec_upload', 'Batch', 'Summary', 'Moradabad', 'Chhajlet',
                10, 5, 'DRAFT', '2026-12-31T00:00:00Z', ?, ?
            );
        """, (now, now))
        conn.commit()

    try:
        with get_db() as conn:
            # Path traversal rejection
            with pytest.raises(ValueError, match="path traversal"):
                OpportunityVerificationService.submit_evidence(
                    conn=conn,
                    opp_id="opp_sec_upload",
                    data={"evidence_type": "DOCUMENT", "storage_key": "../../etc/passwd"},
                    user_id="usr_sec_worker_mbd"
                )

            # Executable file rejection
            with pytest.raises(ValueError, match="prohibited"):
                OpportunityVerificationService.submit_evidence(
                    conn=conn,
                    opp_id="opp_sec_upload",
                    data={"evidence_type": "DOCUMENT", "storage_key": "uploads/malicious_payload.exe"},
                    user_id="usr_sec_worker_mbd"
                )
    finally:
        with get_db() as conn:
            conn.execute("DELETE FROM opportunity_evidence WHERE opportunity_id = 'opp_sec_upload';")
            conn.execute("DELETE FROM local_opportunities WHERE id = 'opp_sec_upload';")
            conn.execute("DELETE FROM qualifications WHERE id = 'q_sec_upload';")
            conn.commit()


def test_locale_code_abuse_sanitization():
    """Malicious or oversized locale strings must resolve safely to default fallback locale."""
    abusive_locales = [
        "../../en",
        "<script>alert(1)</script>",
        "' OR 1=1 --",
        "x" * 500,
        "INVALID_LOCALE_XYZ"
    ]
    for loc in abusive_locales:
        resolved = resolve_locale(explicit_locale=loc)
        assert resolved in [SupportedLocale.EN, SupportedLocale.HI]
        assert resolved == SupportedLocale.EN


def test_state_machine_bypass_prevention(setup_security_fixtures):
    """Attempting invalid opportunity verification or direct referral on draft opportunity must be rejected."""
    token = _token_for("usr_sec_worker_mbd")
    headers = {"Authorization": f"Bearer {token}"}

    # Verify invalid action is rejected
    res = client.post(
        "/api/v1/staff/opportunities/opp_nonexistent_or_draft/INVALID_ACTION",
        json={"action": "HACK_ACTIVE"},
        headers=headers
    )
    assert res.status_code in (400, 422, 404)


def test_sensitive_logging_leakage_redaction():
    """Structured log formatters must redact passwords, JWTs, phone numbers, and Aadhaar numbers."""
    raw_text = (
        "User logged in with password='SuperSecretPassword123' "
        "and Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.doNotLeakSignature "
        "mobile=9876543210 and aadhaar=1234 5678 9012"
    )

    sanitized = redact_text(raw_text)
    assert "SuperSecretPassword123" not in sanitized
    assert "doNotLeakSignature" not in sanitized
    assert "9876543210" not in sanitized
    assert "1234 5678 9012" not in sanitized

    # Check dictionary redaction
    payload = {
        "password": "my_secret_password",
        "access_token": "token_abc123",
        "phone": "9876543210",
        "notes": "Caseworker internal diary confidential text",
        "normal_field": "public_data"
    }
    redacted = redact_data(payload)
    assert redacted["password"] == "[REDACTED]"
    assert redacted["access_token"] == "[REDACTED]"
    assert redacted["phone"] == "[REDACTED]"
    assert redacted["notes"] == "[REDACTED]"
    assert redacted["normal_field"] == "public_data"
