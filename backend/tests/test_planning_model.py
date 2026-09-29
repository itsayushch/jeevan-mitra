import os
import json
import sqlite3
import tempfile
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.database import get_db, init_database
from app.main import app
from app.ai_layers.layer5_planning.aggregation_service import AggregationService
from app.ai_layers.layer5_planning.narrative_engine import NarrativeEngine

OFFICER_KEY = "test-officer-secret"
ADMIN_KEY = "test-admin-secret"
WORKER_KEY = "test-worker-secret"


@pytest.fixture
def client():
    orig = {
        "db": settings.DATABASE_PATH,
        "officer_key": settings.OFFICER_API_KEY,
        "officer_district": settings.OFFICER_DISTRICT,
        "admin_key": settings.ADMIN_API_KEY,
        "worker_key": settings.WORKER_API_KEY,
        "ai_provider": settings.AI_PROVIDER,
    }
    temp_dir = tempfile.TemporaryDirectory()
    settings.DATABASE_PATH = os.path.join(temp_dir.name, "planning_test.db")
    settings.OFFICER_API_KEY = OFFICER_KEY
    settings.OFFICER_DISTRICT = "Moradabad"
    settings.ADMIN_API_KEY = ADMIN_KEY
    settings.WORKER_API_KEY = WORKER_KEY
    settings.AI_PROVIDER = "mock"
    init_database()

    with TestClient(app) as c:
        yield c

    settings.DATABASE_PATH = orig["db"]
    settings.OFFICER_API_KEY = orig["officer_key"]
    settings.OFFICER_DISTRICT = orig["officer_district"]
    settings.ADMIN_API_KEY = orig["admin_key"]
    settings.WORKER_API_KEY = orig["worker_key"]
    settings.AI_PROVIDER = orig["ai_provider"]
    temp_dir.cleanup()


@pytest.fixture
def fixture_db(client):
    """
    Fixture DB with known demand and supply:
    - qual_x: 10 demand in BlockA, 7 in BlockB, 3 in BlockC (suppressed)
    - qual_y: 4 demand in BlockA (suppressed)
    - Supply for BlockA/qual_x: one eligible batch (6 available / 10 total),
      plus unverified, stale, archived, zero-seat and expired batches that
      must all be excluded.
    """
    now = datetime.now(timezone.utc)
    with get_db() as conn:
        conn.executemany("""
            INSERT OR REPLACE INTO qualifications
            (id, nqr_code, title, sector, nsqf_level, duration_hours, min_education,
             min_education_rank, work_type, physical_intensity, skills_acquired,
             curriculum_summary, entry_criteria, certification_body, nqr_link,
             verification_status, verification_date)
            VALUES (?, ?, ?, 'Test Sector', 3, 200, 'Class 8', 2, 'both', 'medium', '[]',
                    'curriculum', 'criteria', 'body', 'https://nqr.gov.in/x',
                    'verified', '2026-01-01');
        """, [
            ("qual_x", "TST/Q0001", "Test Trade X"),
            ("qual_y", "TST/Q0002", "Test Trade Y"),
        ])

        def opp(id, qual, block, seats, verified=True, verified_days_ago=5,
                archived=False, end_date_offset=60, lat=28.8, lon=78.7):
            return (
                id, qual, f"Centre {id}", "training_centre", "Moradabad", block,
                "addr", lat, lon,
                (now - timedelta(days=20)).date().isoformat(),
                (now + timedelta(days=end_date_offset)).date().isoformat(),
                seats + 4, seats, 2, "active", 0, 1000, 1, "pm_ajay_portal",
                "worker_01" if verified else None,
                (now - timedelta(days=verified_days_ago)).isoformat(),
                now.isoformat(), archived,
            )

        conn.executemany("""
            INSERT OR REPLACE INTO local_opportunities
            (id, qualification_id, centre_or_employer_name, type, district, block,
             address, latitude, longitude, batch_start_date, batch_end_date,
             total_seats, available_seats, sc_reserved_seats, batch_status,
             hostel_available, stipend_amount_inr, free_toolkit_provided, source,
             verified_by_worker_id, verified_at, created_at, is_archived)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, [
            opp("opp_eligible", "qual_x", "BlockA", 6),                       # counted
            opp("opp_unverified", "qual_x", "BlockA", 50, verified=False),   # excluded
            opp("opp_stale", "qual_x", "BlockA", 50, verified_days_ago=40),  # excluded
            opp("opp_archived", "qual_x", "BlockA", 50, archived=True),      # excluded
            opp("opp_zero_seats", "qual_x", "BlockA", 0),                    # excluded
            opp("opp_expired", "qual_x", "BlockA", 50, end_date_offset=-5), # excluded
        ])

        def dem(id, qual, block, match=0):
            return (
                id, qual, "Moradabad", block, 10.0, "both", match, "FY 2026-27",
                now.isoformat(),
            )

        demand = []
        for i in range(10):
            demand.append(dem(f"dem_a_{i}", "qual_x", "BlockA", match=1))
        for i in range(7):
            demand.append(dem(f"dem_b_{i}", "qual_x", "BlockB"))
        for i in range(3):
            demand.append(dem(f"dem_c_{i}", "qual_x", "BlockC"))
        for i in range(4):
            demand.append(dem(f"dem_y_{i}", "qual_y", "BlockA"))
        conn.executemany("""
            INSERT OR REPLACE INTO demand_records
            (id, qualification_id, district, block, mobility_radius_km,
             work_preference, had_verified_match, period, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, demand)
    return client


def officer_headers():
    return {"X-Officer-API-Key": OFFICER_KEY}


def admin_headers():
    return {"X-Admin-API-Key": ADMIN_KEY}


def worker_headers():
    return {"X-Worker-API-Key": WORKER_KEY}


# ----------------------------------------------------------------------
# Aggregation
# ----------------------------------------------------------------------
def test_aggregation_counts_and_supply_filter(fixture_db):
    with get_db() as conn:
        result = AggregationService(conn).get_demand_supply_matrix("Moradabad", "FY 2026-27")

    assert result["status"] == "ok"
    cells = {(c["block"], c["qualification_id"]): c for c in result["matrix"]}

    cell_a = cells[("BlockA", "qual_x")]
    assert cell_a["demand_count"] == 10
    # Only the eligible batch counts: unverified/stale/archived/zero-seat/expired excluded
    assert cell_a["verified_seats"] == 6
    assert cell_a["total_seats"] == 10
    assert cell_a["gap"] == 4
    assert cell_a["suppressed"] is False
    assert cell_a["source"]["supply_batch_ids"] == ["opp_eligible"]
    assert len(cell_a["source"]["demand_row_ids"]) == 10

    cell_b = cells[("BlockB", "qual_x")]
    assert cell_b["demand_count"] == 7
    assert cell_b["verified_seats"] == 0
    assert cell_b["gap"] == 7
    assert cell_b["nearest_verified_centre_km"] is not None
    assert cell_b["nearest_verified_centre_name"] == "Centre opp_eligible"
    assert cell_b["share_of_demand_with_no_verified_batch"] == 1.0

    metrics = result["metrics"]
    assert metrics["total_demand_records"] == 24
    assert metrics["demand_with_verified_match_count"] == 10
    # 7 eligible seed batches in Moradabad + the 1 eligible fixture batch;
    # the 5 ineligible fixture batches (unverified/stale/archived/zero-seat/
    # expired) are excluded, proven by cell_a["verified_seats"] == 6 above.
    assert metrics["supply_batches_considered"] == 8
    assert metrics["total_unmet_demand"] == 4 + 7  # BlockA gap 4 + BlockB gap 7


def test_small_cell_suppression(fixture_db):
    with get_db() as conn:
        result = AggregationService(conn).get_demand_supply_matrix("Moradabad", "FY 2026-27")

    cells = {(c["block"], c["qualification_id"]): c for c in result["matrix"]}

    suppressed = cells[("BlockC", "qual_x")]
    assert suppressed["suppressed"] is True
    assert suppressed["demand_count"] is None
    assert suppressed["verified_seats"] is None
    assert suppressed["gap"] is None
    assert suppressed["severity_score"] is None
    assert "k-anonymity" in suppressed["suppression_reason"]
    assert suppressed["source"]["demand_row_ids"] == []

    suppressed_y = cells[("BlockA", "qual_y")]
    assert suppressed_y["suppressed"] is True

    # Suppressed cells are ranked after all reportable cells
    order = [c["block"] for c in result["matrix"] if not c["suppressed"]]
    assert order == ["BlockB", "BlockA"]  # severity-ranked
    assert result["metrics"]["suppressed_cell_count"] == 2


def test_gap_scoring_formula(fixture_db):
    with get_db() as conn:
        service = AggregationService(conn)
        result = service.get_demand_supply_matrix("Moradabad", "FY 2026-27")

    cells = {(c["block"], c["qualification_id"]): c for c in result["matrix"]}
    cell_b = cells[("BlockB", "qual_x")]

    # severity = demand_count * (1 - coverage) * distance_factor, recomputed
    # independently from the documented formula.
    from app.utils.distance import calculate_distance_km, get_block_coordinates
    coords = get_block_coordinates("BlockB")
    dist = calculate_distance_km(coords["lat"], coords["lon"], 28.8, 78.7)
    distance_factor = 1 + min(dist, 50.0) / 50.0
    assert cell_b["coverage"] == 0
    assert cell_b["distance_factor"] == round(distance_factor, 4)
    assert cell_b["severity_score"] == round(7 * (1 - 0) * distance_factor, 2)

    # Formula is exposed for audit
    assert "severity = demand_count * (1 - coverage)" in result["gap_scoring"]["formula"]
    assert result["gap_scoring"]["distance_cap_km"] == 50.0


def test_matrix_endpoint_requires_officer_auth(fixture_db):
    res = fixture_db.get("/api/v1/planning/matrix?district=Moradabad&period=FY 2026-27")
    assert res.status_code == 403

    res = fixture_db.get("/api/v1/planning/matrix?district=Moradabad&period=FY 2026-27",
                         headers=worker_headers())
    assert res.status_code == 403

    res = fixture_db.get("/api/v1/planning/matrix?district=Moradabad&period=FY 2026-27",
                         headers=officer_headers())
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_officer_cannot_read_other_district(fixture_db):
    res = fixture_db.get("/api/v1/planning/matrix?district=Ghaziabad&period=FY 2026-27",
                         headers=officer_headers())
    assert res.status_code == 403
    assert res.json()["detail"]["error"] == "DISTRICT_SCOPE_VIOLATION"

    # Admin is not district-scoped
    res = fixture_db.get("/api/v1/planning/matrix?district=Ghaziabad&period=FY 2026-27",
                         headers=admin_headers())
    assert res.status_code == 200
    assert res.json()["status"] == "insufficient_data"


def test_empty_district_returns_insufficient_data(fixture_db):
    with get_db() as conn:
        result = AggregationService(conn).get_demand_supply_matrix("Shamli", "FY 2026-27")
    assert result["status"] == "insufficient_data"
    assert "No anonymised demand records" in result["message"]
    assert result["matrix"] == []
    assert result["metrics"] == {}

    # Admin (not district-scoped) can query an empty district
    res = fixture_db.get("/api/v1/planning/matrix?district=Shamli", headers=admin_headers())
    assert res.status_code == 200
    assert res.json()["status"] == "insufficient_data"

    gen = fixture_db.post("/api/v1/planning/briefs/generate",
                          json={"district": "Shamli", "period": "FY 2026-27"},
                          headers=admin_headers())
    assert gen.status_code == 422
    assert gen.json()["detail"]["status"] == "insufficient_data"


# ----------------------------------------------------------------------
# Narrative engine
# ----------------------------------------------------------------------
def _sample_matrix():
    return {
        "district": "Moradabad",
        "period": "FY 2026-27",
        "generated_at": "2026-09-29T00:00:00+00:00",
        "query_id": "qry_abc123",
        "data_basis": {"k_anonymity_threshold": 5, "distance_cap_km": 50},
        "metrics": {
            "total_demand_records": 24,
            "demand_with_verified_match_count": 10,
            "demand_with_verified_match_share": 0.4167,
            "blocks_with_demand": 3,
            "suppressed_cell_count": 2,
            "supply_batches_considered": 1,
            "total_unmet_demand": 11,
        },
        "matrix": [
            {
                "block": "BlockB", "qualification_id": "qual_x",
                "qualification_title": "Test Trade X", "nqr_code": "TST/Q0001",
                "demand_count": 7, "verified_seats": 0, "total_seats": 0, "gap": 7,
                "nearest_verified_centre_km": 15.2, "nearest_verified_centre_name": "Centre opp_eligible",
                "share_of_demand_with_no_verified_batch": 1.0, "coverage": 0.0,
                "severity_score": 21.0, "suppressed": False,
                "source": {"query_id": "qry_cell1", "demand_row_ids": ["dem_b_0"], "supply_batch_ids": []},
            },
            {
                "block": "BlockA", "qualification_id": "qual_x",
                "qualification_title": "Test Trade X", "nqr_code": "TST/Q0001",
                "demand_count": 10, "verified_seats": 6, "total_seats": 10, "gap": 4,
                "nearest_verified_centre_km": 0.0, "nearest_verified_centre_name": "Centre opp_eligible",
                "share_of_demand_with_no_verified_batch": 0.0, "coverage": 0.6,
                "severity_score": 4.0, "suppressed": False,
                "source": {"query_id": "qry_cell2", "demand_row_ids": ["dem_a_0"], "supply_batch_ids": ["opp_eligible"]},
            },
        ],
    }


def test_narrative_validator_rejects_invented_number():
    matrix = _sample_matrix()
    brief_data = NarrativeEngine.build_brief_data(matrix)
    template = NarrativeEngine.TEMPLATE  # raw template, placeholders intact

    # Invented number -> rejected
    bad = template.replace("DEMAND OVERVIEW", "DEMAND OVERVIEW. We surveyed 999 people.")
    ok, reason = NarrativeEngine.validate_llm_output(bad, brief_data)
    assert ok is False
    assert reason == "invented_number:999"

    # Dropped placeholder -> rejected
    bad2 = template.replace("{demand_count}", "several")
    ok2, reason2 = NarrativeEngine.validate_llm_output(bad2, brief_data)
    assert ok2 is False
    assert reason2 == "missing_placeholder:demand_count"

    # Numbers present in the query result are allowed
    ok3, _ = NarrativeEngine.validate_llm_output(template, brief_data)
    assert ok3 is True


def test_generate_brief_falls_back_to_template_on_invented_number():
    matrix = _sample_matrix()

    def bad_llm(template):
        return template.replace("1. DEMAND OVERVIEW", "1. DEMAND OVERVIEW. Last year we helped 5000 youth.")

    result = NarrativeEngine.generate_brief(matrix, llm_rewrite=bad_llm)
    assert result["narrative_meta"]["rewritten_by_llm"] is False
    assert result["narrative_meta"]["validation"].startswith("fallback:invented_number:5000")
    assert "5000" not in result["narrative"]
    assert "24 anonymised demand records" in result["narrative"]
    assert "qry_abc123" in result["narrative"]


def test_generate_brief_accepts_valid_rewrite():
    matrix = _sample_matrix()

    def good_llm(template):
        return template.replace(
            "1. DEMAND OVERVIEW",
            "1. DEMAND OVERVIEW (rephrased by LLM; figures inserted by code)",
        )

    result = NarrativeEngine.generate_brief(matrix, llm_rewrite=good_llm)
    assert result["narrative_meta"]["rewritten_by_llm"] is True
    assert result["narrative_meta"]["validation"] == "passed"
    assert "rephrased by LLM" in result["narrative"]
    assert "24 anonymised demand records" in result["narrative"]


def test_brief_figures_carry_source_references():
    matrix = _sample_matrix()
    result = NarrativeEngine.generate_brief(matrix)
    figures = result["figures"]
    assert figures
    top = [f for f in figures if f["figure"] == "top_gap"][0]
    assert top["source_query_id"] == "qry_cell1"
    assert "dem_b_0" in top["source_row_ids"]
    assert top["value"]["demand_count"] == 7


# ----------------------------------------------------------------------
# Brief lifecycle: generate / sign-off / export
# ----------------------------------------------------------------------
def test_unsigned_brief_cannot_be_exported_and_signoff_writes_audit(fixture_db):
    gen = fixture_db.post("/api/v1/planning/briefs/generate",
                          json={"district": "Moradabad", "period": "FY 2026-27"},
                          headers=officer_headers())
    assert gen.status_code == 201
    brief_id = gen.json()["brief_id"]
    assert gen.json()["status"] == "draft"
    assert "24 anonymised demand records" in gen.json()["generated_narrative"]

    # Unsigned -> 409
    res = fixture_db.get(f"/api/v1/planning/briefs/{brief_id}/export", headers=officer_headers())
    assert res.status_code == 409
    assert res.json()["detail"]["error"] == "BRIEF_NOT_SIGNED_OFF"

    # Lifecycle: draft -> under_review -> signed_off
    res = fixture_db.post(f"/api/v1/planning/briefs/{brief_id}/sign-off",
                          json={"officer_name": "Officer A", "action": "submit_for_review"},
                          headers=officer_headers())
    assert res.status_code == 200
    assert res.json()["status"] == "under_review"

    # Still not exportable
    assert fixture_db.get(f"/api/v1/planning/briefs/{brief_id}/export",
                          headers=officer_headers()).status_code == 409

    res = fixture_db.post(f"/api/v1/planning/briefs/{brief_id}/sign-off",
                          json={"officer_name": "Officer A", "action": "sign_off"},
                          headers=officer_headers())
    assert res.status_code == 200
    assert res.json()["status"] == "signed_off"

    # Export now works
    res = fixture_db.get(f"/api/v1/planning/briefs/{brief_id}/export", headers=officer_headers())
    assert res.status_code == 200
    assert "block,qualification" in res.text

    res = fixture_db.get(f"/api/v1/planning/briefs/{brief_id}/export?format=json",
                         headers=officer_headers())
    assert res.status_code == 200
    assert res.json()["export_format"] == "pdf_ready_json"

    # Audit rows written for both transitions
    with get_db() as conn:
        rows = conn.execute(
            "SELECT action FROM audit_events WHERE entity_type = 'planning_brief' AND entity_id = ? ORDER BY timestamp;",
            (brief_id,),
        ).fetchall()
    actions = [r["action"] for r in rows]
    assert "BRIEF_GENERATED" in actions
    assert "BRIEF_UNDER_REVIEW" in actions
    assert "BRIEF_SIGNED_OFF" in actions

    # Invalid transition rejected
    res = fixture_db.post(f"/api/v1/planning/briefs/{brief_id}/sign-off",
                          json={"officer_name": "Officer A", "action": "sign_off"},
                          headers=officer_headers())
    assert res.status_code == 409


def test_brief_get_and_list_are_district_scoped(fixture_db):
    gen = fixture_db.post("/api/v1/planning/briefs/generate",
                          json={"district": "Moradabad", "period": "FY 2026-27"},
                          headers=officer_headers())
    brief_id = gen.json()["brief_id"]

    res = fixture_db.get(f"/api/v1/planning/briefs/{brief_id}", headers=officer_headers())
    assert res.status_code == 200
    body = res.json()
    assert body["reviewer_sign_off_status"] == "draft"
    assert body["aggregation_snapshot"]["query_id"]
    assert body["aggregation_snapshot"]["matrix"]

    # Admin can read it too
    assert fixture_db.get(f"/api/v1/planning/briefs/{brief_id}",
                          headers=admin_headers()).status_code == 200

    # Unknown brief -> 404
    assert fixture_db.get("/api/v1/planning/briefs/brief_nope",
                          headers=officer_headers()).status_code == 404


# ----------------------------------------------------------------------
# Demand record capture
# ----------------------------------------------------------------------
def _setup_interview(client, with_analytics_consent=True):
    ben = client.post("/api/v1/beneficiaries", json={
        "name": "Demand Test", "district": "Moradabad", "block": "Chhajlet",
    })
    ben_id = ben.json()["id"]

    client.post("/api/v1/consents", json={
        "beneficiary_id": ben_id, "consent_type": "ai_processing", "granted": True,
    })
    if with_analytics_consent:
        client.post("/api/v1/consents", json={
            "beneficiary_id": ben_id, "consent_type": "analytics", "granted": True,
        })

    sess = client.post("/api/v1/sessions").json()
    start = client.post("/api/v1/interviews/start", json={
        "beneficiary_id": ben_id, "session_id": sess["session_id"],
    }, headers={"X-Session-ID": sess["session_id"]})
    interview_id = start.json()["interview_id"]

    client.post(f"/api/v1/interviews/{interview_id}/confirm-profile", json={
        "beneficiary_id": ben_id,
        "confirmed_fields": {
            "education": "Class 10", "district": "Moradabad", "block": "Chhajlet",
            "mobility": 10.0, "self_employment_or_wage_preference": "both",
        },
    }, headers={"X-Session-ID": sess["session_id"]})
    return ben_id, sess["session_id"], interview_id


def test_demand_record_written_on_recommendation_with_consent(fixture_db):
    ben_id, session_id, interview_id = _setup_interview(fixture_db, with_analytics_consent=True)

    gen = fixture_db.post("/api/v1/recommendations/generate",
                          json={"interview_id": interview_id},
                          headers={"X-Session-ID": session_id})
    assert gen.status_code == 200

    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM demand_records WHERE district = 'Moradabad' AND block = 'Chhajlet';"
        ).fetchall()
    assert len(rows) == 1
    rec = dict(rows[0])
    with get_db() as conn:
        top_rec = conn.execute("""
            SELECT qualification_id FROM recommendations
            WHERE interview_id = ? ORDER BY rank ASC LIMIT 1;
        """, (interview_id,)).fetchone()
    assert rec["qualification_id"] == top_rec["qualification_id"]  # rank-1 trade interest
    assert rec["had_verified_match"] in (0, 1)
    assert rec["period"] == "FY 2026-27"
    # No PII columns
    assert "name" not in rec and "phone" not in rec and "text" not in rec


def test_no_demand_record_without_analytics_consent(fixture_db):
    ben_id, session_id, interview_id = _setup_interview(fixture_db, with_analytics_consent=False)

    gen = fixture_db.post("/api/v1/recommendations/generate",
                          json={"interview_id": interview_id},
                          headers={"X-Session-ID": session_id})
    assert gen.status_code == 200

    with get_db() as conn:
        count = conn.execute("SELECT COUNT(*) as c FROM demand_records;").fetchone()["c"]
    # Only the fixture demand records exist (24), none from this interview
    assert count == 24


def test_interview_completion_does_not_duplicate_demand(fixture_db):
    """One demand record per recommendation generation - completion must not double-count."""
    ben_id, session_id, interview_id = _setup_interview(fixture_db, with_analytics_consent=True)

    fixture_db.post("/api/v1/recommendations/generate",
                    json={"interview_id": interview_id},
                    headers={"X-Session-ID": session_id})
    with get_db() as conn:
        before = conn.execute("SELECT COUNT(*) as c FROM demand_records;").fetchone()["c"]

    res = fixture_db.post(f"/api/v1/interviews/{interview_id}/complete",
                          headers={"X-Session-ID": session_id})
    assert res.status_code == 200

    with get_db() as conn:
        after = conn.execute("SELECT COUNT(*) as c FROM demand_records;").fetchone()["c"]
    assert after == before


# ----------------------------------------------------------------------
# Legacy endpoint compatibility
# ----------------------------------------------------------------------
def test_legacy_supply_gap_matrix_alias(fixture_db):
    res = fixture_db.get("/api/v1/planning/supply-gap-matrix?district=Moradabad",
                         headers=officer_headers())
    assert res.status_code == 200
    data = res.json()
    assert "matrix" in data
    assert "metrics" in data
    assert data["metrics"]["total_demand_records"] > 0


def test_worker_verify_changes_brief_numbers(fixture_db):
    """Demo acceptance: changing seats via worker /verify changes the brief."""
    gen1 = fixture_db.post("/api/v1/planning/briefs/generate",
                           json={"district": "Moradabad", "period": "FY 2026-27"},
                           headers=officer_headers())
    brief1 = gen1.json()["generated_narrative"]

    # Worker verifies the eligible batch with more seats
    ver = fixture_db.post("/api/v1/worker/opportunities/opp_eligible/verify",
                          json={"available_seats": 10, "batch_status": "active", "notes": "More seats"},
                          headers=worker_headers())
    assert ver.status_code == 200

    gen2 = fixture_db.post("/api/v1/planning/briefs/generate",
                           json={"district": "Moradabad", "period": "FY 2026-27"},
                           headers=officer_headers())
    brief2 = gen2.json()["generated_narrative"]
    assert brief1 != brief2
    assert "verified seats (gap 0)" in brief2 or "gap 0" in brief2
