import os
import json
import uuid
import tempfile
import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

from app.main import app
from app.config import settings
from app.database import get_db, init_database
from tests.factories.auth_factories import (
    create_catalogue_manager,
    create_beneficiary_actor,
    create_field_worker_alpha,
    create_field_worker_beta,
    create_auditor_alpha,
    create_super_admin,
    get_auth_headers
)
from tests.factories.opportunity_factories import (
    create_qualification_record,
    create_provider_record,
    create_opportunity_record
)

@pytest.fixture(scope="module")
def env():
    orig_db = settings.DATABASE_PATH
    temp_dir = tempfile.TemporaryDirectory()
    settings.DATABASE_PATH = os.path.join(temp_dir.name, "test_cases_referrals.db")
    init_database()

    with get_db() as conn:
        now = datetime.now(timezone.utc).isoformat()
        roles = [
            ("super_admin", "Super Administrator"),
            ("catalogue_manager", "Catalogue Manager"),
            ("field_worker", "Field Worker"),
            ("auditor", "Auditor"),
            ("beneficiary", "Beneficiary")
        ]
        for key, name in roles:
            conn.execute("INSERT OR IGNORE INTO roles (id, key, display_name, description, created_at) VALUES (?, ?, ?, ?, ?)",
                         (f"role_{key}", key, name, f"{key} role", now))

    with TestClient(app) as client:
        yield client

    settings.DATABASE_PATH = orig_db
    temp_dir.cleanup()

def test_sprint5_full_case_and_referral_lifecycle(env):
    client = env
    now = datetime.now(timezone.utc)
    now_iso = now.isoformat()
    future_expiry = (now + timedelta(days=30)).isoformat()
    past_expiry = (now - timedelta(days=1)).isoformat()

    # 1. Setup actors
    with get_db() as conn:
        # Worker Alpha in District Alpha / Block Alpha-1
        worker_alpha = create_field_worker_alpha(conn, user_id="usr_fw_a", email="worker_a@test.com")
        # Worker Beta in District Beta / Block Beta-1
        worker_beta = create_field_worker_beta(conn, user_id="usr_fw_b", email="worker_b@test.com")
        # Auditor Alpha in District Alpha
        auditor_alpha = create_auditor_alpha(conn, user_id="usr_aud_a", email="auditor_a@test.com")
        # Beneficiary in District Alpha / Block Alpha-1
        ben_user = create_beneficiary_actor(conn, user_id="usr_ben_1", email="ben_1@test.com",
                                           district_id="District Alpha", block_id="Block Alpha-1")
        # Catalogue items
        qual = create_qualification_record(conn, qual_id="qual_solar_tech",
                                           title="Solar Technician Level 4", sector="Renewable Energy")
        provider = create_provider_record(conn, provider_id="prov_apex", name="Apex Skill Institute",
                                          district_id="District Alpha", block_id="Block Alpha-1")
        # Valid Opportunity (active, capacity 20, verified)
        opp_valid = create_opportunity_record(
            conn,
            opp_id="opp_solar_moradabad",
            qualification_id="qual_solar_tech",
            provider_id="prov_apex",
            title="Solar Technician Batch 2026-A",
            district_id="District Alpha",
            block_id="Block Alpha-1",
            status="ACTIVE",
            expiry_days_ahead=30,
            seats_available=20
        )
        # Expired Opportunity
        opp_expired = create_opportunity_record(
            conn,
            opp_id="opp_solar_expired",
            qualification_id="qual_solar_tech",
            provider_id="prov_apex",
            title="Solar Technician Batch Expired",
            district_id="District Alpha",
            block_id="Block Alpha-1",
            status="ACTIVE",
            expiry_days_ahead=-1,
            seats_available=15
        )
        # Zero capacity Opportunity
        opp_full = create_opportunity_record(
            conn,
            opp_id="opp_solar_full",
            qualification_id="qual_solar_tech",
            provider_id="prov_apex",
            title="Solar Technician Batch Full",
            district_id="District Alpha",
            block_id="Block Alpha-1",
            status="ACTIVE",
            expiry_days_ahead=30,
            seats_available=0
        )

        # Recommendation linked to valid opportunity
        conn.execute("""
            INSERT INTO recommendations (
                id, beneficiary_id, qualification_id, local_opportunity_id,
                rank, score, score_breakdown, match_state, explanation_text,
                audio_explanation_script, tradeoff_summary, skill_gap_summary,
                data_snapshot, created_at, updated_at
            ) VALUES (?, ?, ?, ?, 1, 0.95, '{}', 'Verified Match', 'High suitability for solar training',
                     'script', 'tradeoff', 'gap', '{}', ?, ?);
        """, ("rec_solar_valid", "usr_ben_1", "qual_solar_tech", "opp_solar_moradabad", now_iso, now_iso))

        # Recommendation linked to expired opportunity
        conn.execute("""
            INSERT INTO recommendations (
                id, beneficiary_id, qualification_id, local_opportunity_id,
                rank, score, score_breakdown, match_state, explanation_text,
                audio_explanation_script, tradeoff_summary, skill_gap_summary,
                data_snapshot, created_at, updated_at
            ) VALUES (?, ?, ?, ?, 2, 0.90, '{}', 'Verified Match', 'High suitability',
                     'script', 'tradeoff', 'gap', '{}', ?, ?);
        """, ("rec_solar_expired", "usr_ben_1", "qual_solar_tech", "opp_solar_expired", now_iso, now_iso))

        # Recommendation linked to full capacity opportunity
        conn.execute("""
            INSERT INTO recommendations (
                id, beneficiary_id, qualification_id, local_opportunity_id,
                rank, score, score_breakdown, match_state, explanation_text,
                audio_explanation_script, tradeoff_summary, skill_gap_summary,
                data_snapshot, created_at, updated_at
            ) VALUES (?, ?, ?, ?, 3, 0.88, '{}', 'Verified Match', 'High suitability',
                     'script', 'tradeoff', 'gap', '{}', ?, ?);
        """, ("rec_solar_full", "usr_ben_1", "qual_solar_tech", "opp_solar_full", now_iso, now_iso))

    headers_alpha = get_auth_headers(worker_alpha["id"])
    headers_beta = get_auth_headers(worker_beta["id"])
    headers_auditor = get_auth_headers(auditor_alpha["id"])
    headers_ben = get_auth_headers(ben_user["id"])

    # ------------------------------------------------------------------------
    # STEP 1: Case Management & Geographic Scope Enforcement
    # ------------------------------------------------------------------------
    # Worker Beta (District Beta) attempts to create case for Beneficiary in District Alpha -> 403
    res_deny = client.post("/staff/cases", json={
        "beneficiary_id": "usr_ben_1",
        "district_id": "District Alpha",
        "block_id": "Block Alpha-1"
    }, headers=headers_beta)
    assert res_deny.status_code == 403
    assert "outside your assigned scope" in res_deny.json()["detail"]

    # Verify isolated security audit event was logged without business changes
    with get_db() as conn:
        sec_event = conn.execute("SELECT * FROM audit_events WHERE action = 'SECURITY_ACCESS_DENIED';").fetchone()
        assert sec_event is not None
        assert sec_event["actor_user_id"] == "usr_fw_b"
        # No case created
        case_cnt = conn.execute("SELECT COUNT(*) as c FROM beneficiary_cases;").fetchone()["c"]
        assert case_cnt == 0

    # Worker Alpha (District Alpha) creates case -> 201
    res_create_case = client.post("/staff/cases", json={
        "beneficiary_id": "usr_ben_1",
        "district_id": "District Alpha",
        "block_id": "Block Alpha-1",
        "intake_source": "COUNSELLING_CAMP"
    }, headers=headers_alpha)
    assert res_create_case.status_code == 201
    case_data = res_create_case.json()
    case_id = case_data["id"]
    assert case_data["case_status"] == "NEW"
    assert case_data["beneficiary_id"] == "usr_ben_1"

    # Worker Alpha adds internal staff note
    res_staff_note = client.post(f"/staff/cases/{case_id}/notes", json={
        "note_text": "Beneficiary prefers morning batch due to transport constraints.",
        "note_type": "COUNSELLING",
        "visibility": "STAFF_ONLY"
    }, headers=headers_alpha)
    assert res_staff_note.status_code == 201

    # Worker Alpha adds beneficiary-safe note
    res_safe_note = client.post(f"/staff/cases/{case_id}/notes", json={
        "note_text": "Your preliminary eligibility has been verified. Reviewing solar technician batch options.",
        "note_type": "GENERAL",
        "visibility": "BENEFICIARY_SAFE"
    }, headers=headers_alpha)
    assert res_safe_note.status_code == 201

    # Worker Alpha schedules follow-up
    res_followup = client.post(f"/staff/cases/{case_id}/follow-up", json={
        "next_follow_up_at": (now + timedelta(days=2)).isoformat(),
        "note": "Follow up on batch enrolment confirmation"
    }, headers=headers_alpha)
    assert res_followup.status_code == 200
    assert res_followup.json()["next_follow_up_at"] is not None

    # Worker Beta attempts to read Worker Alpha's case -> 403
    res_read_deny = client.get(f"/staff/cases/{case_id}", headers=headers_beta)
    assert res_read_deny.status_code == 403

    # Auditor Alpha reads case -> 200 (read-only allowed)
    res_auditor = client.get(f"/staff/cases/{case_id}", headers=headers_auditor)
    assert res_auditor.status_code == 200
    assert len(res_auditor.json()["notes"]) == 3 # 2 notes + 1 auto follow-up note

    # ------------------------------------------------------------------------
    # STEP 2: Atomic 11-Step Referral Eligibility Validation
    # ------------------------------------------------------------------------
    # Attempt 1: Referral to Expired Opportunity -> 400
    res_expired = client.post(f"/staff/cases/{case_id}/referrals", json={
        "recommendationId": "rec_solar_expired",
        "note": "Testing expired opp"
    }, headers=headers_alpha)
    assert res_expired.status_code == 400
    assert "Referral eligibility check failed" in res_expired.json()["detail"] or "expired" in res_expired.json()["detail"].lower()

    # Attempt 2: Referral to Zero-Capacity Opportunity -> 400
    res_full = client.post(f"/staff/cases/{case_id}/referrals", json={
        "recommendationId": "rec_solar_full",
        "note": "Testing full capacity opp"
    }, headers=headers_alpha)
    assert res_full.status_code == 400
    assert "Referral eligibility check failed" in res_full.json()["detail"] or "capacity" in res_full.json()["detail"].lower()

    # Attempt 3: Worker Beta attempts to create referral on Worker Alpha's case -> 403
    res_ref_deny = client.post(f"/staff/cases/{case_id}/referrals", json={
        "recommendationId": "rec_solar_valid",
        "note": "Out of scope worker"
    }, headers=headers_beta)
    assert res_ref_deny.status_code == 403

    # Attempt 4: Valid referral creation by Worker Alpha -> 201
    res_ref_valid = client.post(f"/staff/cases/{case_id}/referrals", json={
        "recommendationId": "rec_solar_valid",
        "note": "Beneficiary expressed strong interest in solar installation."
    }, headers=headers_alpha)
    assert res_ref_valid.status_code == 201
    ref_data = res_ref_valid.json()
    ref_id = ref_data["id"]
    assert ref_data["referral_status"] == "READY_TO_SEND"
    assert ref_data["eligibility_snapshot_json"]["match_state_at_referral"] == "VERIFIED_MATCH"
    assert ref_data["eligibility_snapshot_json"]["opportunity_seats_available_at_referral"] == 20

    # Attempt 5: Duplicate active referral creation for same beneficiary & opportunity -> 409
    res_dup = client.post(f"/staff/cases/{case_id}/referrals", json={
        "recommendationId": "rec_solar_valid",
        "note": "Duplicate attempt"
    }, headers=headers_alpha)
    assert res_dup.status_code == 409
    assert "already exists" in res_dup.json()["detail"].lower()

    # Verify Case updated to REFERRAL_IN_PROGRESS
    with get_db() as conn:
        updated_case = conn.execute("SELECT case_status, latest_referral_id FROM beneficiary_cases WHERE id = ?", (case_id,)).fetchone()
        assert updated_case["case_status"] == "REFERRAL_IN_PROGRESS"
        assert updated_case["latest_referral_id"] == ref_id

    # ------------------------------------------------------------------------
    # STEP 3: State Machine Validation & Transition History
    # ------------------------------------------------------------------------
    # Invalid transition: READY_TO_SEND directly to COMPLETED -> 400
    res_invalid_trans = client.post(f"/staff/referrals/{ref_id}/transition", json={
        "to_status": "COMPLETED",
        "note": "Skipping steps"
    }, headers=headers_alpha)
    assert res_invalid_trans.status_code == 400
    assert "Invalid referral transition" in res_invalid_trans.json()["detail"]

    # Valid transition sequence: READY_TO_SEND -> REFERRED -> CONTACTED -> ENROLLED
    for next_st, reason in [
        ("REFERRED", "Dispatched to training provider"),
        ("CONTACTED", "Reached beneficiary via phone"),
        ("ENROLLED", "Batch admission confirmed by institute")
    ]:
        res_trans = client.post(f"/staff/referrals/{ref_id}/transition", json={
            "to_status": next_st,
            "reason": reason
        }, headers=headers_alpha)
        assert res_trans.status_code == 200
        assert res_trans.json()["referral_status"] == next_st

    # Log contact attempt
    res_catt = client.post(f"/staff/referrals/{ref_id}/contact-attempts", json={
        "channel": "PHONE",
        "attempt_outcome": "CONNECTED",
        "summary": "Called candidate to remind about batch start date on Monday.",
        "next_follow_up_at": (now + timedelta(days=3)).isoformat()
    }, headers=headers_alpha)
    assert res_catt.status_code == 201

    # Verify history records exist
    res_hist = client.get(f"/staff/referrals/{ref_id}/history", headers=headers_alpha)
    assert res_hist.status_code == 200
    histories = res_hist.json()
    assert len(histories) >= 4 # Initial + 3 transitions

    # ------------------------------------------------------------------------
    # STEP 4: Outcomes Lifecycle
    # ------------------------------------------------------------------------
    # Record outcome: ENROLMENT
    res_rec_out = client.post(f"/staff/referrals/{ref_id}/outcomes", json={
        "outcome_type": "ENROLMENT",
        "evidence_summary": "Institute admission slip #APEX-2026-99",
        "occurred_at": now_iso
    }, headers=headers_alpha)
    assert res_rec_out.status_code == 201
    outcome_data = res_rec_out.json()
    outcome_id = outcome_data["id"]
    assert outcome_data["outcome_status"] == "REPORTED"

    # Verify outcome by supervisor / staff
    res_verify_out = client.post(f"/staff/referrals/outcomes/{outcome_id}/verify", json={
        "outcome_status": "VERIFIED",
        "evidence_summary": "Verified against institute physical register"
    }, headers=headers_alpha)
    assert res_verify_out.status_code == 200
    assert res_verify_out.json()["outcome_status"] == "VERIFIED"

    # Complete referral: ENROLLED -> TRAINING_STARTED -> COMPLETED
    client.post(f"/staff/referrals/{ref_id}/transition", json={"to_status": "TRAINING_STARTED"}, headers=headers_alpha)
    res_complete = client.post(f"/staff/referrals/{ref_id}/transition", json={
        "to_status": "COMPLETED",
        "reason": "Training successfully finished with certification"
    }, headers=headers_alpha)
    assert res_complete.status_code == 200
    assert res_complete.json()["referral_status"] == "COMPLETED"

    # Terminal transition to CLOSED
    res_close = client.post(f"/staff/referrals/{ref_id}/transition", json={
        "to_status": "CLOSED",
        "reason": "Placement verified and case successfully closed"
    }, headers=headers_alpha)
    assert res_close.status_code == 200
    assert res_close.json()["referral_status"] == "CLOSED"
    assert res_close.json()["closed_at"] is not None

    # Terminal state lock: attempting to transition a CLOSED referral -> 400
    res_lock = client.post(f"/staff/referrals/{ref_id}/transition", json={
        "to_status": "CONTACTED"
    }, headers=headers_alpha)
    assert res_lock.status_code == 400

    # ------------------------------------------------------------------------
    # STEP 5: Beneficiary Data Isolation & Localized Experience
    # ------------------------------------------------------------------------
    # Beneficiary GET /me/cases
    res_ben_cases = client.get("/me/cases", headers=headers_ben)
    assert res_ben_cases.status_code == 200
    assert len(res_ben_cases.json()) == 1

    # Beneficiary GET /me/cases/{case_id}
    res_ben_case_detail = client.get(f"/me/cases/{case_id}", headers=headers_ben)
    assert res_ben_case_detail.status_code == 200
    ben_case = res_ben_case_detail.json()
    # Check that only BENEFICIARY_SAFE notes are returned
    note_texts = [n["note_text"] for n in ben_case["notes"]]
    assert any("preliminary eligibility has been verified" in t for t in note_texts)
    # Check that STAFF_ONLY notes are NOT leaked!
    assert not any("transport constraints" in t for t in note_texts)

    # Beneficiary GET /me/referrals (English)
    res_ben_refs_en = client.get("/me/referrals", headers=headers_ben)
    assert res_ben_refs_en.status_code == 200
    ref_item_en = res_ben_refs_en.json()[0]
    assert ref_item_en["referralId"] == ref_id
    assert ref_item_en["displayStatus"] == "Case Completed"
    assert "completed successfully" in ref_item_en["nextStep"].lower()

    # Beneficiary GET /me/referrals (Hindi Parity via Accept-Language: hi)
    headers_ben_hi = dict(headers_ben)
    headers_ben_hi["Accept-Language"] = "hi"
    res_ben_refs_hi = client.get("/me/referrals", headers=headers_ben_hi)
    assert res_ben_refs_hi.status_code == 200
    ref_item_hi = res_ben_refs_hi.json()[0]
    assert ref_item_hi["displayStatus"] == "मामला संपन्न"

    # Beneficiary GET /me/referrals/{referral_id}
    res_ben_ref_detail = client.get(f"/me/referrals/{ref_id}", headers=headers_ben_hi)
    assert res_ben_ref_detail.status_code == 200
    ben_ref_data = res_ben_ref_detail.json()
    assert ben_ref_data["opportunity"]["title"] == "Solar Technician Batch 2026-A"
    assert ben_ref_data["opportunity"]["provider_name"] == "Apex Skill Institute"
    # Ensure internal staff snapshot is NOT exposed to beneficiary
    assert "eligibility_snapshot_json" not in ben_ref_data
    assert "eligibilitySnapshot" not in ben_ref_data

    # Beneficiary submits support request
    res_supp = client.post(f"/me/referrals/{ref_id}/support-request", json={
        "message": "Need clarification on post-training certificate distribution."
    }, headers=headers_ben)
    assert res_supp.status_code == 200
    assert res_supp.json()["status"] == "success"

    # Beneficiary declining a referral workflow
    # Create another recommendation and referral to test decline
    with get_db() as conn:
        conn.execute("""
            INSERT INTO recommendations (
                id, beneficiary_id, qualification_id, local_opportunity_id,
                rank, score, score_breakdown, match_state, explanation_text,
                audio_explanation_script, tradeoff_summary, skill_gap_summary,
                data_snapshot, created_at, updated_at
            ) VALUES ('rec_solar_decline', 'usr_ben_1', 'qual_solar_tech', 'opp_solar_moradabad', 4, 0.85, '{}', 'Verified Match', 'Match', 'script', 'tradeoff', 'gap', '{}', ?, ?);
        """, (now_iso, now_iso))

    res_ref_2 = client.post(f"/staff/cases/{case_id}/referrals", json={
        "recommendationId": "rec_solar_decline"
    }, headers=headers_alpha)
    assert res_ref_2.status_code == 201
    ref_id_2 = res_ref_2.json()["id"]

    res_decline = client.post(f"/me/referrals/{ref_id_2}/decline", json={
        "reason": "Relocating to another town with family."
    }, headers=headers_ben)
    print("DECLINE RESPONSE:", res_decline.status_code, res_decline.json())
    assert res_decline.status_code == 200

    with get_db() as conn:
        dec_row = conn.execute("SELECT referral_status FROM referrals WHERE id = ?", (ref_id_2,)).fetchone()
        assert dec_row["referral_status"] == "BENEFICIARY_DECLINED"
