import uuid
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timezone, timedelta
import json
from app.config import settings
from app.main import app
from app.database import get_db, init_database

@pytest.fixture(autouse=True)
def setup_test_db():
    original_admin_key = settings.ADMIN_API_KEY
    settings.ADMIN_API_KEY = "admin-key-01"
    init_database()
    yield
    settings.ADMIN_API_KEY = original_admin_key

client = TestClient(app)

def create_guest_session():
    res = client.post("/api/v1/sessions", json={})
    assert res.status_code in [200, 201]
    data = res.json()
    return data["session_token"], data["session_id"]

def setup_consents(session_id: str, session_token: str):
    headers = {"X-Session-Token": session_token}
    for c_type in ["ai_processing", "profile_storage", "counselor_referral", "export_summary"]:
        client.post(
            "/api/v1/consents",
            json={
                "session_id": session_id,
                "consent_type": c_type,
                "granted": True,
                "user_language": "hi",
            },
            headers=headers,
        )

# ============================================================================
# Scenario Matrix (16 Diverse Operational Scenarios)
# ============================================================================

def test_scenario_01_hindi_interview_self_employment_moradabad():
    """Scenario 1: Hindi speaker, Class 8 pass, self-employment interest in Moradabad."""
    token, session_id = create_guest_session()
    setup_consents(session_id, token)
    headers = {"X-Session-Token": token}

    start_res = client.post(
        "/api/v1/interviews/start",
        json={"session_id": session_id, "channel": "web_app", "language": "hi"},
        headers=headers,
    )
    assert start_res.status_code in [200, 201]
    interview_id = start_res.json()["interview_id"]

    # Submit turn in Hindi
    turn_res = client.post(
        f"/api/v1/interviews/{interview_id}/turns",
        json={"text": "मुझे मशरूम की खेती और खाद का काम शुरू करना है।", "speaker": "user"},
        headers=headers,
    )
    assert turn_res.status_code == 200

    # Confirm profile
    conf_res = client.post(
        f"/api/v1/interviews/{interview_id}/confirm-profile",
        json={
            "confirmed_fields": {
                "district": "Moradabad",
                "language": "hi",
                "education": "Class 8",
                "interests": ["Mushroom Cultivation", "Agriculture"],
                "mobility": "local_only",
                "self_employment_or_wage_preference": "self_employment",
            }
        },
        headers=headers,
    )
    assert conf_res.status_code == 200

    # Generate recommendations
    rec_res = client.post(
        "/api/v1/recommendations/generate",
        json={"interview_id": interview_id},
        headers=headers,
    )
    assert rec_res.status_code == 200
    recs = rec_res.json()["recommendations"]
    assert len(recs) > 0
    # Top rec should be self-employment oriented (Mushroom or Food processing)
    top_rec = recs[0]
    assert top_rec["qualification"]["id"] in ["qual_mushroom_07", "qual_food_04", "AGR/Q7803", "FIC/Q9001"]
    assert top_rec["local_availability"]["status"] in ["verified_open", "unknown"]


def test_scenario_02_english_interview_wage_moradabad():
    """Scenario 2: English speaker, Class 10 pass, wage preference in Moradabad."""
    token, session_id = create_guest_session()
    setup_consents(session_id, token)
    headers = {"X-Session-Token": token}

    start_res = client.post(
        "/api/v1/interviews/start",
        json={"session_id": session_id, "channel": "web_app", "language": "en"},
        headers=headers,
    )
    interview_id = start_res.json()["interview_id"]

    client.post(
        f"/api/v1/interviews/{interview_id}/confirm-profile",
        json={
            "confirmed_fields": {
                "district": "Moradabad",
                "language": "en",
                "education": "Class 10",
                "interests": ["Solar PV Installation", "Electrical"],
                "mobility": "district_wide",
                "self_employment_or_wage_preference": "wage",
            }
        },
        headers=headers,
    )

    rec_res = client.post(
        "/api/v1/recommendations/generate",
        json={"interview_id": interview_id},
        headers=headers,
    )
    assert rec_res.status_code == 200
    recs = rec_res.json()["recommendations"]
    solar_rec = next((r for r in recs if r["qualification"]["id"] in ["qual_solar_01", "SGJ/Q0101"]), None)
    assert solar_rec is not None
    assert solar_rec["local_availability"]["status"] == "verified_open"
    assert "Govt ITI Moradabad" in solar_rec["local_availability"]["centre_name"]


def test_scenario_03_hinglish_mixed_language_extraction():
    """Scenario 3: Hinglish text handles extraction without failure."""
    token, session_id = create_guest_session()
    setup_consents(session_id, token)
    headers = {"X-Session-Token": token}

    start_res = client.post(
        "/api/v1/interviews/start",
        json={"session_id": session_id, "channel": "web_app", "language": "hi"},
        headers=headers,
    )
    interview_id = start_res.json()["interview_id"]

    turn_res = client.post(
        f"/api/v1/interviews/{interview_id}/turns",
        json={"text": "Mera qualification 10th pass hai aur mujhe data entry computer job pasand hai.", "speaker": "user"},
        headers=headers,
    )
    assert turn_res.status_code == 200
    assert turn_res.json()["mode"] in ["standard", "guided_fallback", "clarification"]


def test_scenario_04_limited_mobility_filters_far_batches():
    """Scenario 4: Limited mobility prefers local opportunities and restricts out-of-district."""
    token, session_id = create_guest_session()
    setup_consents(session_id, token)
    headers = {"X-Session-Token": token}

    start_res = client.post("/api/v1/interviews/start", json={"session_id": session_id}, headers=headers)
    interview_id = start_res.json()["interview_id"]

    client.post(
        f"/api/v1/interviews/{interview_id}/confirm-profile",
        json={
            "confirmed_fields": {
                "district": "Moradabad",
                "education": "Class 8",
                "interests": ["Sewing", "Garment Stitching"],
                "mobility": "local_only",
                "self_employment_or_wage_preference": "both",
            }
        },
        headers=headers,
    )

    rec_res = client.post("/api/v1/recommendations/generate", json={"interview_id": interview_id}, headers=headers)
    assert rec_res.status_code == 200
    recs = rec_res.json()["recommendations"]
    assert any("mobility" in r["why_recommended"][1].lower() or "mobility" in r["why_recommended"][0].lower() for r in recs)


def test_scenario_05_unknown_low_education_blocks_higher_nsqf():
    """Scenario 5: Below Class 5 education strictly blocks Class 10 requirements."""
    token, session_id = create_guest_session()
    setup_consents(session_id, token)
    headers = {"X-Session-Token": token}

    start_res = client.post("/api/v1/interviews/start", json={"session_id": session_id}, headers=headers)
    interview_id = start_res.json()["interview_id"]

    client.post(
        f"/api/v1/interviews/{interview_id}/confirm-profile",
        json={
            "confirmed_fields": {
                "district": "Moradabad",
                "education": "Class 5",
                "interests": ["Retail", "Solar", "Sewing"],
                "mobility": "local_only",
                "self_employment_or_wage_preference": "both",
            }
        },
        headers=headers,
    )

    rec_res = client.post("/api/v1/recommendations/generate", json={"interview_id": interview_id}, headers=headers)
    assert rec_res.status_code == 200
    recs = rec_res.json()["recommendations"]
    # Solar and Retail require Class 10; they must NOT be in the recommendations
    for r in recs:
        assert r["qualification"]["id"] not in ["qual_solar_01", "SGJ/Q0101"]
        assert r["qualification"]["id"] not in ["qual_retail_06", "RAS/Q0104"]


def test_scenario_06_no_local_option_returns_status_unknown_without_hallucination():
    """Scenario 6: User in district without local batches gets status unknown and counselor referral CTA."""
    token, session_id = create_guest_session()
    setup_consents(session_id, token)
    headers = {"X-Session-Token": token}

    start_res = client.post("/api/v1/interviews/start", json={"session_id": session_id}, headers=headers)
    interview_id = start_res.json()["interview_id"]

    client.post(
        f"/api/v1/interviews/{interview_id}/confirm-profile",
        json={
            "confirmed_fields": {
                "district": "Varanasi", # No local batches seeded for Varanasi
                "education": "Class 10",
                "interests": ["Solar PV Installation"],
                "mobility": "local_only",
                "self_employment_or_wage_preference": "wage",
            }
        },
        headers=headers,
    )

    rec_res = client.post("/api/v1/recommendations/generate", json={"interview_id": interview_id}, headers=headers)
    assert rec_res.status_code == 200
    recs = rec_res.json()["recommendations"]
    assert len(recs) > 0
    top_rec = recs[0]
    assert top_rec["local_availability"]["status"] == "unknown"
    assert top_rec["local_availability"]["district"] == "Varanasi"
    assert "guidance recommendation" in top_rec["caveat"].lower()


def test_scenario_07_no_result_scenario_returns_counselor_handoff():
    """Scenario 7: When all qualifications are blocked, safe counselor handoff is returned."""
    token, session_id = create_guest_session()
    setup_consents(session_id, token)
    headers = {"X-Session-Token": token}

    start_res = client.post("/api/v1/interviews/start", json={"session_id": session_id}, headers=headers)
    interview_id = start_res.json()["interview_id"]

    client.post(
        f"/api/v1/interviews/{interview_id}/confirm-profile",
        json={
            "confirmed_fields": {
                "district": "Moradabad",
                "education": "No Formal Education", # rank 0 blocks everything requiring Class 5+
                "interests": ["Advanced Robotics"],
                "mobility": "local_only",
                "self_employment_or_wage_preference": "wage",
            }
        },
        headers=headers,
    )

    rec_res = client.post("/api/v1/recommendations/generate", json={"interview_id": interview_id}, headers=headers)
    assert rec_res.status_code == 200
    data = rec_res.json()
    assert data["count"] == 0
    assert data.get("counselor_handoff_recommended") is True


def test_scenario_08_stale_opportunity_returns_unknown_status():
    """Scenario 8: Batches verified > 90 days ago return unknown/expired."""
    with get_db() as conn:
        stale_date = (datetime.now(timezone.utc) - timedelta(days=120)).isoformat()
        conn.execute("UPDATE local_opportunities SET verified_at = ? WHERE id = 'opp_solar_moradabad_01';", (stale_date,))

    res = client.get("/api/v1/catalogue/opportunities?district=Moradabad")
    assert res.status_code == 200
    opps = res.json()["opportunities"]
    solar_opp = next((o for o in opps if o["id"] == "opp_solar_moradabad_01"), None)
    assert solar_opp is not None
    assert solar_opp["availability"] == "unknown"

    # Restore
    with get_db() as conn:
        now_date = datetime.now(timezone.utc).isoformat()
        conn.execute("UPDATE local_opportunities SET verified_at = ? WHERE id = 'opp_solar_moradabad_01';", (now_date,))


def test_scenario_09_user_profile_correction_updates_recommendations():
    """Scenario 9: Editing education from Class 8 to Class 10 expands recommendations."""
    token, session_id = create_guest_session()
    setup_consents(session_id, token)
    headers = {"X-Session-Token": token}

    start_res = client.post("/api/v1/interviews/start", json={"session_id": session_id}, headers=headers)
    interview_id = start_res.json()["interview_id"]

    # Initial profile: Class 8
    client.post(
        f"/api/v1/interviews/{interview_id}/confirm-profile",
        json={
            "confirmed_fields": {
                "district": "Moradabad",
                "education": "Class 8",
                "interests": ["Solar", "Repair"],
                "mobility": "district_wide",
                "self_employment_or_wage_preference": "wage",
            }
        },
        headers=headers,
    )
    rec1 = client.post("/api/v1/recommendations/generate", json={"interview_id": interview_id}, headers=headers).json()
    assert not any(r["qualification"]["id"] in ["qual_solar_01", "SGJ/Q0101"] for r in rec1["recommendations"])

    # User updates education to Class 10
    client.patch(
        f"/api/v1/interviews/{interview_id}/fields/education",
        json={"value": "Class 10"},
        headers=headers,
    )
    # Re-confirm profile
    client.post(
        f"/api/v1/interviews/{interview_id}/confirm-profile",
        json={
            "confirmed_fields": {
                "district": "Moradabad",
                "education": "Class 10",
                "interests": ["Solar", "Repair"],
                "mobility": "district_wide",
                "self_employment_or_wage_preference": "wage",
            }
        },
        headers=headers,
    )
    rec2 = client.post("/api/v1/recommendations/generate", json={"interview_id": interview_id}, headers=headers).json()
    assert any(r["qualification"]["id"] in ["qual_solar_01", "SGJ/Q0101"] for r in rec2["recommendations"])


def test_scenario_10_traditional_skills_declared_soft_ranks_higher():
    """Scenario 10: Declared traditional skill enhances relevance score."""
    token, session_id = create_guest_session()
    setup_consents(session_id, token)
    headers = {"X-Session-Token": token}

    start_res = client.post("/api/v1/interviews/start", json={"session_id": session_id}, headers=headers)
    interview_id = start_res.json()["interview_id"]

    client.post(
        f"/api/v1/interviews/{interview_id}/confirm-profile",
        json={
            "confirmed_fields": {
                "district": "Moradabad",
                "education": "Class 8",
                "interests": ["Craft"],
                "traditional_or_existing_skills": ["Garment Stitching", "Sewing"],
                "mobility": "local_only",
                "self_employment_or_wage_preference": "both",
            }
        },
        headers=headers,
    )
    rec = client.post("/api/v1/recommendations/generate", json={"interview_id": interview_id}, headers=headers).json()
    top_rec = rec["recommendations"][0]
    assert top_rec["qualification"]["id"] in ["qual_sewing_02", "AMH/Q0301"]
    assert any("traditional" in f.lower() or "skill" in f.lower() for f in top_rec["ranking_factors"])


def test_scenario_11_wage_only_preference_filtering():
    """Scenario 11: Wage-only preference deprioritizes or filters self-employment pathways."""
    token, session_id = create_guest_session()
    setup_consents(session_id, token)
    headers = {"X-Session-Token": token}

    start_res = client.post("/api/v1/interviews/start", json={"session_id": session_id}, headers=headers)
    interview_id = start_res.json()["interview_id"]

    client.post(
        f"/api/v1/interviews/{interview_id}/confirm-profile",
        json={
            "confirmed_fields": {
                "district": "Moradabad",
                "education": "Class 10",
                "interests": ["Sales", "Customer Assistance"],
                "mobility": "district_wide",
                "self_employment_or_wage_preference": "wage",
            }
        },
        headers=headers,
    )
    rec = client.post("/api/v1/recommendations/generate", json={"interview_id": interview_id}, headers=headers).json()
    for r in rec["recommendations"]:
        assert r["qualification"]["id"] not in ["qual_mushroom_07", "AGR/Q7803"]


def test_scenario_12_self_employment_only_preference_filtering():
    """Scenario 12: Self-employment preference filters out wage-only pathways."""
    token, session_id = create_guest_session()
    setup_consents(session_id, token)
    headers = {"X-Session-Token": token}

    start_res = client.post("/api/v1/interviews/start", json={"session_id": session_id}, headers=headers)
    interview_id = start_res.json()["interview_id"]

    client.post(
        f"/api/v1/interviews/{interview_id}/confirm-profile",
        json={
            "confirmed_fields": {
                "district": "Moradabad",
                "education": "Class 10",
                "interests": ["Agriculture", "Produce"],
                "mobility": "district_wide",
                "self_employment_or_wage_preference": "self_employment",
            }
        },
        headers=headers,
    )
    rec = client.post("/api/v1/recommendations/generate", json={"interview_id": interview_id}, headers=headers).json()
    for r in rec["recommendations"]:
        assert r["qualification"]["id"] not in ["qual_solar_01", "SGJ/Q0101"] # Solar is wage-only


def test_scenario_13_revoking_ai_consent_triggers_guided_fallback():
    """Scenario 13: Revoking ai_processing causes turn submissions to operate in guided mode."""
    token, session_id = create_guest_session()
    setup_consents(session_id, token)
    headers = {"X-Session-Token": token}

    start_res = client.post("/api/v1/interviews/start", json={"session_id": session_id}, headers=headers)
    interview_id = start_res.json()["interview_id"]

    # Revoke ai_processing
    consents_res = client.get(f"/api/v1/consents/{session_id}", headers=headers)
    c_list = consents_res.json().get("consents", consents_res.json()) if isinstance(consents_res.json(), dict) else consents_res.json()
    ai_consent = next(c for c in c_list if c["consent_type"] == "ai_processing")
    c_id = ai_consent.get("consent_id") or ai_consent.get("id")
    client.post(f"/api/v1/consents/{c_id}/revoke", json={}, headers=headers)

    # 1. Standard AI turn is blocked with 403 CONSENT_REVOKED
    turn_res = client.post(
        f"/api/v1/interviews/{interview_id}/turns",
        json={"text": "Hello, I want to learn skills", "speaker": "user"},
        headers=headers,
    )
    assert turn_res.status_code == 403
    assert turn_res.json()["error"]["code"] == "CONSENT_REVOKED"

    # 2. Guided fallback turn operates without AI processing
    fallback_res = client.post(
        f"/api/v1/interviews/{interview_id}/turns",
        json={"text": "Hello, I want to learn skills", "speaker": "user", "mode": "guided_fallback"},
        headers=headers,
    )
    assert fallback_res.status_code == 200
    assert fallback_res.json()["mode"] == "guided_fallback"


def test_scenario_14_revoking_counselor_consent_pauses_referral():
    """Scenario 14: Revoking counselor_referral consent pauses/closes active referral cases."""
    token, session_id = create_guest_session()
    setup_consents(session_id, token)
    headers = {"X-Session-Token": token}

    start_res = client.post("/api/v1/interviews/start", json={"session_id": session_id}, headers=headers)
    interview_id = start_res.json()["interview_id"]

    ref_res = client.post(
        "/api/v1/referrals",
        json={"interview_id": interview_id, "referral_reason": "user_requested_human_help"},
        headers=headers,
    )
    assert ref_res.status_code in [200, 201]
    referral_id = ref_res.json().get("id", ref_res.json().get("referral_id"))

    # Revoke counselor_referral consent
    consents_res = client.get(f"/api/v1/consents/{session_id}", headers=headers)
    c_list = consents_res.json().get("consents", consents_res.json()) if isinstance(consents_res.json(), dict) else consents_res.json()
    counselor_consent = next(c for c in c_list if c["consent_type"] == "counselor_referral")
    c_id = counselor_consent.get("consent_id") or counselor_consent.get("id")
    client.post(f"/api/v1/consents/{c_id}/revoke", json={}, headers=headers)

    # Referral status in DB should be paused/closed
    with get_db() as conn:
        row = conn.execute("SELECT status FROM referral_cases WHERE id = ?;", (referral_id,)).fetchone()
        assert row["status"] in ["closed", "paused"]


def test_scenario_15_full_dpdp_right_to_erasure():
    """Scenario 15: DELETE /beneficiaries/me completely wipes profile and session data."""
    token, session_id = create_guest_session()
    setup_consents(session_id, token)
    headers = {"X-Session-Token": token}

    start_res = client.post("/api/v1/interviews/start", json={"session_id": session_id}, headers=headers)
    print(start_res.json())
    interview_id = start_res.json()["interview_id"]

    client.post(
        f"/api/v1/interviews/{interview_id}/confirm-profile",
        json={"confirmed_fields": {"district": "Moradabad", "education": "Class 10"}},
        headers=headers,
    )

    del_res = client.delete("/api/v1/beneficiaries/me", headers=headers)
    assert del_res.status_code == 200
    assert del_res.json()["status"] in ["deleted", "success"]

    # Verification: interview_sessions and profile_field_values must be gone
    with get_db() as conn:
        assert conn.execute("SELECT count(*) FROM interview_sessions WHERE session_id = ?;", (session_id,)).fetchone()[0] == 0
        assert conn.execute("SELECT count(*) FROM profile_field_values WHERE interview_id = ?;", (interview_id,)).fetchone()[0] == 0


def test_scenario_16_controlled_admin_catalog_workflow():
    """Scenario 16: Admin creates, updates, and archives catalog items with audit coverage."""
    admin_headers = {"X-Worker-API-Key": "admin-key-01"}

    # 1. Admin creates new official qualification
    q_res = client.post(
        "/api/v1/admin/catalogue/qualifications",
        json={
            "nqr_code": f"TEST/Q{uuid.uuid4().hex[:6].upper()}",
            "title": "Smart Village Technician",
            "sector": "Electronics",
            "nsqf_level": 4,
            "duration_hours": 300,
            "min_education": "Class 10",
            "min_education_rank": 3,
            "work_type": "both",
            "physical_intensity": "medium",
            "skills_acquired": ["IoT Sensors", "Solar Batteries"],
            "curriculum_summary": "IoT sensor maintenance in rural utility nodes.",
            "entry_criteria": "Class 10th standard pass",
            "certification_body": "Electronics Sector Skills Council of India",
            "official_source_url": "https://nqr.gov.in/qualifications/TEST-Q9999",
        },
        headers=admin_headers,
    )
    assert q_res.status_code in [200, 201]
    q_id = q_res.json()["id"]

    # 2. Admin creates new local opportunity
    o_res = client.post(
        "/api/v1/admin/catalogue/opportunities",
        json={
            "qualification_id": q_id,
            "district": "Moradabad",
            "block": "Moradabad Urban",
            "state": "Uttar Pradesh",
            "centre_or_employer_name": "Moradabad IoT Training Center",
            "type": "training_centre",
            "address": "RDC Raj Nagar, Moradabad, UP",
            "latitude": 28.8350,
            "longitude": 78.7800,
            "availability": "verified_open",
            "source_url": "https://up.gov.in/iot-batches",
            "batch_start_date": "2026-11-01",
            "batch_end_date": "2027-02-01",
        },
        headers=admin_headers,
    )
    assert o_res.status_code in [200, 201]
    o_id = o_res.json()["id"]

    # 3. Verify public search finds it
    public_res = client.get("/api/v1/catalogue/opportunities?district=Moradabad")
    assert any(o["id"] == o_id for o in public_res.json()["opportunities"])

    # 4. Admin archives opportunity
    arch_res = client.post(f"/api/v1/admin/catalogue/opportunities/{o_id}/archive", headers=admin_headers)
    assert arch_res.status_code == 200

    # 5. Public search no longer returns archived opportunity
    after_arch_res = client.get("/api/v1/catalogue/opportunities?district=Moradabad")
    assert not any(o["id"] == o_id for o in after_arch_res.json()["opportunities"])
