import os
import tempfile
import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.config import settings
from app.database import get_db, init_database
from app.main import app

@pytest.fixture
def client():
    orig_db = settings.DATABASE_PATH
    orig_key = settings.WORKER_API_KEY
    temp_dir = tempfile.TemporaryDirectory()
    settings.DATABASE_PATH = os.path.join(temp_dir.name, "test_catalogue.db")
    settings.WORKER_API_KEY = "test-worker-key"
    init_database()

    with TestClient(app, headers={"X-Worker-API-Key": settings.WORKER_API_KEY}) as c:
        yield c

    settings.DATABASE_PATH = orig_db
    settings.WORKER_API_KEY = orig_key
    temp_dir.cleanup()

def test_qualification_creation_and_retrieval(client):
    qual_payload = {
        "nqr_code": "TEST/Q9901",
        "title": "Drone Agriculture Spraying Specialist",
        "sector": "Agriculture",
        "nsqf_level": 4,
        "duration_hours": 200,
        "min_education": "Class 10",
        "min_education_rank": 3,
        "work_type": "wage",
        "physical_intensity": "medium",
        "skills_acquired": ["Drone Piloting", "Pesticide Spray Calibration", "Battery Safety"],
        "curriculum_summary": "Comprehensive drone piloting for agricultural crop spray operations.",
        "entry_criteria": "Class 10 pass with valid remote pilot license.",
        "certification_body": "Agriculture Skill Council of India (ASCI)",
        "official_source_url": "https://nqr.gov.in/qualifications/TEST-Q9901"
    }

    res = client.post("/api/v1/admin/catalogue/qualifications", json=qual_payload)
    assert res.status_code == 201
    created = res.json()
    assert created["nqr_code"] == "TEST/Q9901"
    assert created["official_source_url"] == qual_payload["official_source_url"]

    # Public listing
    list_res = client.get("/api/v1/catalogue/qualifications?sector=Agriculture")
    assert list_res.status_code == 200
    quals = list_res.json()["qualifications"]
    assert any(q["nqr_code"] == "TEST/Q9901" for q in quals)

def test_opportunity_requires_valid_linked_qualification(client):
    invalid_opp = {
        "qualification_id": "non_existent_qual_id",
        "centre_or_employer_name": "Test Centre",
        "district": "Moradabad",
        "block": "Chhajlet",
        "address": "Main Road, Chhajlet",
        "latitude": 28.98,
        "longitude": 78.68,
        "batch_start_date": "2026-10-01",
        "batch_end_date": "2026-12-01"
    }
    res = client.post("/api/v1/admin/catalogue/opportunities", json=invalid_opp)
    assert res.status_code == 422
    assert "does not exist" in res.json()["error"]["message"]

def test_stale_opportunity_returns_status_unknown(client):
    # Insert an opportunity with verified_at > 120 days ago
    stale_date = (datetime.now(timezone.utc) - timedelta(days=120)).isoformat()
    with get_db() as conn:
        conn.execute("""
            INSERT INTO local_opportunities (
                id, qualification_id, centre_or_employer_name, type, district, block, state,
                address, latitude, longitude, batch_start_date, batch_end_date, total_seats,
                available_seats, sc_reserved_seats, batch_status, availability, verified_at, created_at
            ) VALUES (
                'opp_stale_99', 'qual_solar_01', 'Old Solar Centre', 'training_centre',
                'Moradabad', 'Chhajlet', 'Uttar Pradesh', 'Old Road', 28.98, 78.68,
                '2026-05-01', '2026-08-01', 30, 10, 5, 'active', 'verified_open', ?, ?
            );
        """, (stale_date, stale_date))

    # Query opportunities for district
    res = client.get("/api/v1/catalogue/opportunities?district=Moradabad")
    assert res.status_code == 200
    opps = res.json()["opportunities"]
    stale_opp = next((o for o in opps if o["id"] == "opp_stale_99"), None)
    assert stale_opp is not None
    # Stale rule applied: availability must be unknown
    assert stale_opp["availability"] == "unknown"

def test_archived_opportunity_excluded_from_normal_searches(client):
    # First create opportunity
    opp_payload = {
        "qualification_id": "qual_solar_01",
        "centre_or_employer_name": "Temporary Solar Camp",
        "district": "Moradabad",
        "block": "Chhajlet",
        "address": "Camp Ground",
        "latitude": 28.98,
        "longitude": 78.68,
        "batch_start_date": "2026-10-15",
        "batch_end_date": "2027-01-15"
    }
    create_res = client.post("/api/v1/admin/catalogue/opportunities", json=opp_payload)
    assert create_res.status_code == 201
    opp_id = create_res.json()["id"]

    # Archive it
    arc_res = client.post(f"/api/v1/admin/catalogue/opportunities/{opp_id}/archive")
    assert arc_res.status_code == 200
    assert arc_res.json()["status"] == "archived"

    # Search should no longer return archived opportunity
    search_res = client.get("/api/v1/catalogue/opportunities?district=Moradabad")
    assert search_res.status_code == 200
    opp_ids = [o["id"] for o in search_res.json()["opportunities"]]
    assert opp_id not in opp_ids
