import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app
from app.core.settings import settings


client = TestClient(app)


def test_health_legacy_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "operational"
    assert "service" in data
    assert "timestamp" in data


def test_health_live_endpoint():
    response = client.get("/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "live"
    assert data["service"] == "JeevanMitra 2.0 Backend Core"
    assert "timestamp" in data
    assert "environment" in data


def test_health_ready_success():
    response = client.get("/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["database"] == "healthy"
    assert "alembic_head" in data
    assert data["storage"] == "healthy"


def test_health_ready_db_failure():
    with patch("app.routers.health.get_db") as mock_get_db:
        mock_get_db.side_effect = Exception("Database connection refused")
        response = client.get("/health/ready")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "unavailable"
        assert "unhealthy" in data["database"]


def test_health_version():
    response = client.get("/health/version")
    assert response.status_code == 200
    data = response.json()
    assert "service" in data
    assert "release_version" in data
    assert "git_commit_sha" in data
    assert "environment" in data
    assert "alembic_head" in data


def test_health_config_safe_report():
    response = client.get("/health/config")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    config = data["config"]

    # Verify no raw secrets leaked
    assert "JWT_SECRET" not in config
    assert "GEMINI_API_KEY" not in config
    assert "WORKER_API_KEY" not in config
    assert "jwt_secret_configured" in config
    assert isinstance(config["jwt_secret_configured"], bool)
    assert config["planning_min_cell_count"] == 5
    assert "export_retention_days" in config
