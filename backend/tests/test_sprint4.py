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
