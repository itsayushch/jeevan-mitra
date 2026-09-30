import os
import tempfile
import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.config import settings
from app.database import get_db, init_database
from app.main import app
from app.services.auth_service import AuthService

@pytest.fixture
def test_db():
    temp_dir = tempfile.TemporaryDirectory()
    db_path = os.path.join(temp_dir.name, "test_sprint4.db")
    settings.DATABASE_PATH = db_path
    
    # We rely on Alembic for schema, but we can call init_database() if it handles alembic internally,
    # or just run alembic upgrade head programmatically.
    # For now, we assume tests run against the same DB or we just run alembic.
    import alembic.config
    alembicArgs = [
        '-c', os.path.join(os.path.dirname(os.path.dirname(__file__)), 'alembic.ini'),
        '--raiseerr',
        'upgrade', 'head',
    ]
    alembic.config.main(argv=alembicArgs)
    
    yield
    
    temp_dir.cleanup()

@pytest.fixture
def auth_headers(test_db):
    with get_db() as conn:
        import uuid
        import bcrypt
        from datetime import datetime, timezone
        
        user_id = f"usr_{uuid.uuid4().hex[:8]}"
        hashed = bcrypt.hashpw(b"password123", bcrypt.gensalt()).decode('utf-8')
        now = datetime.now(timezone.utc).isoformat()
        
        conn.execute("""
            INSERT INTO users (id, email, password_hash, display_name, is_active, is_superuser, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, "admin@example.com", hashed, "Admin User", 1, 0, now, now))
        
        # Give catalogue_manager role
        role = conn.execute("SELECT id FROM roles WHERE key = 'catalogue_manager'").fetchone()
        if role:
            conn.execute("INSERT INTO user_roles (user_id, role_id, assigned_at) VALUES (?, ?, ?)", (user_id, role["id"], now))
        conn.commit()

    client = TestClient(app)
    res = client.post("/api/v1/auth/login", json={"email_or_phone": "admin@example.com", "password": "password123"})
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def client():
    return TestClient(app)

def test_qualification_creation(client, auth_headers):
    payload = {
        "title": "Drone Specialist",
        "description": "Piloting for agriculture",
        "sector": "Agriculture",
        "nsqf_level": 4,
        "source_name": "NQR",
        "source_verified_at": datetime.now(timezone.utc).isoformat()
    }
    res = client.post("/api/v1/admin/qualifications", json=payload, headers=auth_headers)
    assert res.status_code == 201
    
    # List qualifications
    res = client.get("/api/v1/qualifications")
    assert res.status_code == 200
    # Should not be listed because it's DRAFT by default
    assert len(res.json()) == 0

    # Get the generated qual_id
    res = client.post("/api/v1/admin/qualifications", json={"title": "Test Qual", "sector": "Agriculture", "description": "Test", "source_name": "Test", "source_verified_at": payload["source_verified_at"]}, headers=auth_headers)
    qual_id = res.json()["id"]

    res = client.patch(f"/api/v1/admin/qualifications/{qual_id}", json={"verification_status": "VERIFIED"}, headers=auth_headers)
    assert res.status_code == 200

    res = client.get("/api/v1/qualifications")
    assert res.status_code == 200
    assert len(res.json()) >= 1

def test_scope_denial_leaves_business_data_unchanged_and_security_audit_logged(client, test_db):
    """
    Regression Test:
    Attempting an update on an opportunity outside the worker's geographic scope
    must be rejected with 403, leaving the business data in the database completely
    unchanged, while recording a SECURITY_ACCESS_DENIED audit event via the isolated audit path.
    """
    from tests.factories.auth_factories import (
        create_field_worker_alpha,
        create_field_worker_beta,
        get_auth_headers
    )
    from tests.factories.opportunity_factories import (
        create_provider_record,
        create_opportunity_record
    )

    with get_db() as conn:
        fw_alpha = create_field_worker_alpha(conn, user_id="fw_alpha_reg", email="fwa_reg@example.com", district_id="District Alpha")
        fw_beta = create_field_worker_beta(conn, user_id="fw_beta_reg", email="fwb_reg@example.com", district_id="District Beta")
        prov = create_provider_record(conn, provider_id="prov_reg_01", district_id="District Alpha")
        opp = create_opportunity_record(
            conn,
            opp_id="opp_reg_01",
            provider_id="prov_reg_01",
            district_id="District Alpha",
            status="ACTIVE",
            seats_available=20
        )
        # Ensure title is known
        conn.execute("UPDATE local_opportunities SET title = 'Alpha Original Opportunity' WHERE id = 'opp_reg_01'")
        conn.commit()

    headers_beta = get_auth_headers("fw_beta_reg")

    # Worker Beta attempts to PATCH Alpha opportunity
    patch_res = client.patch(
        "/api/v1/staff/opportunities/opp_reg_01",
        json={"title": "Hacked Title", "seats_available": 0},
        headers=headers_beta
    )
    assert patch_res.status_code == 403

    # Verify business data is completely untouched
    with get_db() as conn:
        opp_row = conn.execute("SELECT title, seats_available, status FROM local_opportunities WHERE id = 'opp_reg_01'").fetchone()
        assert opp_row["title"] == "Alpha Original Opportunity"
        assert opp_row["seats_available"] == 20
        assert opp_row["status"] == "ACTIVE"

        # Verify security denial audit event was committed via isolated audit session
        audit_events = conn.execute(
            "SELECT * FROM audit_events WHERE entity_id = 'opp_reg_01' AND action = 'SECURITY_ACCESS_DENIED' AND actor_user_id = 'fw_beta_reg'"
        ).fetchall()
        assert len(audit_events) >= 1
        assert audit_events[0]["actor_user_id"] == "fw_beta_reg"

