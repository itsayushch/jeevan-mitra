import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.metrics import record_cell_suppression, get_operational_metrics

client = TestClient(app)


def test_metrics_prometheus_exposition():
    # Trigger a request first
    client.get("/health/live")

    response = client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]
    body = response.text

    assert "jeevanmitra_uptime_seconds" in body
    assert "jeevanmitra_db_connected" in body
    assert "jeevanmitra_http_requests_total" in body
    assert "jeevanmitra_planning_suppressed_cells_total" in body
    assert "jeevanmitra_active_opportunities_expiring_soon" in body


def test_metrics_json_format():
    response = client.get("/metrics?format=json")
    assert response.status_code == 200
    assert "application/json" in response.headers["content-type"]
    data = response.json()

    assert "uptime_seconds" in data
    assert "database_connected" in data
    assert "total_requests" in data
    assert "cell_suppression_events" in data
    assert data["database_connected"] in (0, 1)


def test_metrics_summary_endpoint():
    response = client.get("/metrics/summary")
    assert response.status_code == 200
    data = response.json()
    assert "active_opportunities_expiring_14d" in data
    assert "overdue_referrals_count" in data
    assert "pending_outcome_verifications_count" in data


def test_metrics_cell_suppression_recording():
    initial = get_operational_metrics()["cell_suppression_events"]
    record_cell_suppression()
    record_cell_suppression()
    updated = get_operational_metrics()["cell_suppression_events"]
    assert updated == initial + 2
