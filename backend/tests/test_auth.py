import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db, init_database
import os
import tempfile
from app.config import settings
from app.core.security import hasher

@pytest.fixture(scope="module")
def client():
    orig_db = settings.DATABASE_PATH
    temp_dir = tempfile.TemporaryDirectory()
    settings.DATABASE_PATH = os.path.join(temp_dir.name, "test_auth.db")
    init_database()

    # Create a test user via DB
    with get_db() as conn:
        pw_hash = hasher.hash("SecurePassword123!")
        conn.execute("""
            INSERT INTO users (id, email, password_hash, display_name, is_active, is_superuser, created_at, updated_at)
            VALUES ('usr_test1', 'test@example.com', ?, 'Test User', 1, 0, '2026-09-30T00:00:00Z', '2026-09-30T00:00:00Z')
        """, (pw_hash,))
        
        # Give beneficiary role
        role = conn.execute("SELECT id FROM roles WHERE key = 'beneficiary'").fetchone()
        conn.execute("INSERT INTO user_roles (user_id, role_id, assigned_at) VALUES ('usr_test1', ?, '2026-09-30T00:00:00Z')", (role["id"],))

    with TestClient(app) as c:
        yield c

    settings.DATABASE_PATH = orig_db
    temp_dir.cleanup()

def test_login_success(client):
    res = client.post("/api/v1/auth/login", json={
        "email_or_phone": "test@example.com",
        "password": "SecurePassword123!"
    })
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert "refresh_token" in res.cookies

def test_login_invalid_password(client):
    res = client.post("/api/v1/auth/login", json={
        "email_or_phone": "test@example.com",
        "password": "WrongPassword!"
    })
    assert res.status_code == 401
    assert "Invalid credentials" in res.json()["detail"]

def test_login_invalid_email(client):
    res = client.post("/api/v1/auth/login", json={
        "email_or_phone": "nonexistent@example.com",
        "password": "SecurePassword123!"
    })
    assert res.status_code == 401
    assert "Invalid credentials" in res.json()["detail"]

def test_me_endpoint_requires_auth(client):
    res = client.get("/api/v1/auth/me")
    assert res.status_code == 401

def test_me_endpoint_with_auth(client):
    login = client.post("/api/v1/auth/login", json={
        "email_or_phone": "test@example.com",
        "password": "SecurePassword123!"
    })
    token = login.json()["access_token"]
    
    res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == "test@example.com"
    assert "beneficiary" in data["roles"]

def test_refresh_token_rotation(client):
    login = client.post("/api/v1/auth/login", json={
        "email_or_phone": "test@example.com",
        "password": "SecurePassword123!"
    })
    
    refresh_token = login.cookies.get("refresh_token")
    assert refresh_token
    
    # Refresh
    refresh_res = client.post("/api/v1/auth/refresh", cookies={"refresh_token": refresh_token})
    assert refresh_res.status_code == 200
    new_token = refresh_res.json()["access_token"]
    new_refresh = refresh_res.cookies.get("refresh_token")
    
    assert new_token != login.json()["access_token"]
    assert new_refresh != refresh_token
    
    # Clear client cookies to avoid auto-sending the new one
    client.cookies.clear()
    
    # Replay old token -> should fail and revoke
    replay_res = client.post("/api/v1/auth/refresh", cookies={"refresh_token": refresh_token})
    assert replay_res.status_code == 401
    
    client.cookies.clear()
    
    # Now try to use the newly generated one -> it should have been revoked too!
    revoked_res = client.post("/api/v1/auth/refresh", cookies={"refresh_token": new_refresh})
    assert revoked_res.status_code == 401

def test_training_progress_requires_auth(client):
    res = client.get("/api/v1/learning/me/courses")
    assert res.status_code == 401

def test_training_progress_with_auth(client):
    login = client.post("/api/v1/auth/login", json={
        "email_or_phone": "test@example.com",
        "password": "SecurePassword123!"
    })
    token = login.json()["access_token"]
    
    res = client.get("/api/v1/learning/me/courses", headers={"Authorization": f"Bearer {token}"})
    # Might be empty array since no courses started, but it shouldn't be 401
    assert res.status_code == 200
