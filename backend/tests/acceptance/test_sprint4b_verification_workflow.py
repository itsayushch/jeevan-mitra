"""
Sprint 4B — Verification Workflow Acceptance Test

End-to-end 12-step verification workflow acceptance test executing against a clean database.
Proves the invariant:
A beneficiary can receive an Interest Match based on a verified qualification,
but can receive a Verified Match and eligibility for referral only when an authorised,
correctly scoped field worker verifies an active, non-expired local opportunity with required evidence.
"""

import pytest
import os
import json
import tempfile
from datetime import datetime, timezone, timedelta
import sys
from pathlib import Path

backend_root = Path(__file__).resolve().parent.parent.parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from fastapi.testclient import TestClient
from app.main import app
from app.config import settings
from app.database import get_db, init_database
from app.services.opportunity_expiry_service import OpportunityExpiryService
from app.services.match_state_service import MatchStateService

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
    create_learning_course,
    create_qualification_record,
    create_irrelevant_qualification,
    create_provider_record,
    create_opportunity_record,
    create_evidence_record
)

@pytest.fixture(scope="module")
def test_env():
    """Sets up a clean temporary SQLite database via Alembic upgrade head and returns client."""
    orig_db_path = settings.DATABASE_PATH
    temp_dir = tempfile.TemporaryDirectory()
    db_file = os.path.join(temp_dir.name, "test_sprint4b.db")
    settings.DATABASE_PATH = db_file
    
    # Initialize clean schema via Alembic migrations
    init_database()

    # Pre-seed fixed roles if not already present
    with get_db() as conn:
        now = datetime.now(timezone.utc).isoformat()
        roles = [
            ("role_beneficiary", "beneficiary", "Beneficiary", "End user"),
            ("role_field_worker", "field_worker", "Field Worker", "Local district worker"),
            ("role_district_admin", "district_admin", "District Admin", "District level administrator"),
            ("role_catalogue_manager", "catalogue_manager", "Catalogue Manager", "Manages courses and skills"),
            ("role_super_admin", "super_admin", "Super Admin", "Full system access"),
            ("role_auditor", "auditor", "Auditor", "Read-only audit access")
        ]
        for r in roles:
            conn.execute(
                "INSERT OR IGNORE INTO roles (id, key, display_name, description, created_at) VALUES (?, ?, ?, ?, ?)",
                (r[0], r[1], r[2], r[3], now)
            )

    with TestClient(app) as client:
        yield client

    settings.DATABASE_PATH = orig_db_path
    temp_dir.cleanup()


def test_sprint4b_full_verification_workflow(test_env):
    client = test_env

    # =========================================================================
    # SETUP ACTORS IN CLEAN DB
    # =========================================================================
    with get_db() as conn:
        cat_mgr = create_catalogue_manager(conn, user_id="usr_cat_mgr_a", email="cat_mgr_a@example.com")
        ben_a = create_beneficiary_actor(conn, user_id="usr_ben_a", email="ben_a@example.com", district_id="District Alpha", block_id="Block Alpha-1")
        fw_alpha = create_field_worker_alpha(conn, user_id="usr_fw_alpha", email="fw_alpha@example.com", district_id="District Alpha", block_id="Block Alpha-1")
        fw_beta = create_field_worker_beta(conn, user_id="usr_fw_beta", email="fw_beta@example.com", district_id="District Beta", block_id="Block Beta-1")
        auditor_a = create_auditor_alpha(conn, user_id="usr_auditor_a", email="auditor_a@example.com", district_id="District Alpha")
        s_admin = create_super_admin(conn, user_id="usr_super_admin", email="super_admin@example.com")

        # Also create published learning course
        course = create_learning_course(conn, course_id="course_elec_01", title="Basic Electrical Repair", slug="basic-electrical-repair")

    headers_cat = get_auth_headers("usr_cat_mgr_a")
    headers_ben = get_auth_headers("usr_ben_a")
    headers_fw_alpha = get_auth_headers("usr_fw_alpha")
    headers_fw_beta = get_auth_headers("usr_fw_beta")
    headers_auditor = get_auth_headers("usr_auditor_a")
    headers_admin = get_auth_headers("usr_super_admin")

    # =========================================================================
    # STEP 1 — Qualification creation and publishing
    # Actor: catalogue_manager_a
    # =========================================================================
    qual_payload = {
        "title": "Basic Electrical Repair Assistant",
        "description": "Foundational training in domestic and commercial electrical maintenance",
        "sector": "Electronics",
        "nsqf_level": 3,
        "duration_hours": 200,
        "source_name": "NQR",
        "source_url": "https://nqr.gov.in/qual/elec-01",
        "source_verified_at": datetime.now(timezone.utc).isoformat()
    }
    create_qual_res = client.post("/api/v1/admin/qualifications", json=qual_payload, headers=headers_cat)
    assert create_qual_res.status_code == 201, create_qual_res.text
    qual_data = create_qual_res.json()
    qual_id = qual_data["id"]

    # Mark it VERIFIED
    patch_qual_res = client.patch(
        f"/api/v1/admin/qualifications/{qual_id}",
        json={"verification_status": "VERIFIED"},
        headers=headers_cat
    )
    assert patch_qual_res.status_code == 200
    assert patch_qual_res.json()["verification_status"] == "VERIFIED"

    # Map to learning course
    map_res = client.post(
        f"/api/v1/admin/qualifications/{qual_id}/map-course",
        json={"training_course_id": "course_elec_01", "relationship_type": "direct"},
        headers=headers_cat
    )
    assert map_res.status_code == 201
    assert map_res.json()["training_course_id"] == "course_elec_01"

    # Create irrelevant qualification (NSQF 8, Post-Graduate)
    with get_db() as conn:
        create_irrelevant_qualification(conn, qual_id="qual_aerospace_01")

    # Assertion 1.1: Visible in beneficiary-safe catalogue
    ben_quals_res = client.get("/api/v1/qualifications")
    assert ben_quals_res.status_code == 200
    ben_quals = ben_quals_res.json()
    assert any(q["id"] == qual_id for q in ben_quals)

    # Assertion 1.2: Beneficiary response excludes internal provenance (e.g. source_url, created_by_user_id)
    target_ben_qual = next(q for q in ben_quals if q["id"] == qual_id)
    assert "source_url" not in target_ben_qual
    assert "created_by_user_id" not in target_ben_qual

    # Staff detail shows full provenance
    staff_qual_res = client.get(f"/api/v1/admin/qualifications/{qual_id}", headers=headers_cat)
    assert staff_qual_res.status_code == 200
    staff_qual_data = staff_qual_res.json()
    assert staff_qual_data["source_url"] == "https://nqr.gov.in/qual/elec-01"
    assert staff_qual_data["created_by_user_id"] == "usr_cat_mgr_a"

    # Assertion 1.3: Catalogue manager cannot create or verify local opportunities
    opp_deny_res = client.post(
        "/api/v1/staff/opportunities",
        json={
            "title": "Illegal Batch",
            "summary": "Unauthorized attempt",
            "opportunity_type": "training_centre",
            "qualification_id": qual_id,
            "provider_id": "p1",
            "district_id": "District Alpha",
            "delivery_mode": "offline_centre"
        },
        headers=headers_cat
    )
    assert opp_deny_res.status_code == 403

    # =========================================================================
    # STEP 2 — Interest Match with no local availability
    # Actor: beneficiary_a
    # =========================================================================
    # Request match state for the verified qualification
    match_res = client.get(
        f"/api/v1/opportunities/matches/{qual_id}?district_id=District%20Alpha&block_id=Block%20Alpha-1",
        headers=headers_ben
    )
    assert match_res.status_code == 200
    match_data = match_res.json()
    assert match_data["matchState"] == "INTEREST_MATCH"
    assert match_data["canRequestReferral"] is False
    assert match_data["canRequestWorkerSupport"] is True
    assert "pending" in match_data["beneficiaryMessage"].lower() or "not" in match_data["beneficiaryMessage"].lower() or "pathway" in match_data["beneficiaryMessage"].lower()

    # Generate recommendations
    rec_gen_res = client.post(
        "/api/v1/recommendations/generate",
        json={"beneficiary_id": "usr_ben_a"},
        headers=headers_ben
    )
    assert rec_gen_res.status_code == 200
    rec_data = rec_gen_res.json()
    assert rec_data["count"] > 0
    first_rec = rec_data["recommendations"][0]
    assert first_rec["match_state"] == "INTEREST_MATCH"
    assert first_rec["can_request_referral"] is False
    assert first_rec["local_availability"]["status"] == "unknown"

    # Check database state: recommendation_match_state table
    with get_db() as conn:
        state_row = conn.execute(
            "SELECT * FROM recommendation_match_state WHERE beneficiary_id = ? AND qualification_id = ?",
            ("usr_ben_a", qual_id)
        ).fetchone()
        assert state_row is not None
        assert state_row["match_state"] == "INTEREST_MATCH"

    # =========================================================================
    # STEP 3 — Draft opportunity creation
    # Actor: field_worker_alpha
    # =========================================================================
    # Create provider in District Alpha
    prov_res = client.post(
        "/api/v1/staff/opportunity-providers",
        json={
            "name": "Alpha Skills Training Centre",
            "provider_type": "training_centre",
            "district_id": "District Alpha",
            "block_id": "Block Alpha-1",
            "contact_name": "Director Sharma",
            "contact_phone": "+91-9876543210",
            "contact_email": "sharma@alphaskills.org"
        },
        headers=headers_fw_alpha
    )
    assert prov_res.status_code == 201
    prov_id = prov_res.json()["id"]

    # Create local opportunity in DRAFT
    future_start = (datetime.now(timezone.utc) + timedelta(days=20)).isoformat()
    future_expiry = (datetime.now(timezone.utc) + timedelta(days=60)).isoformat()
    draft_opp_payload = {
        "qualification_id": qual_id,
        "provider_id": prov_id,
        "opportunity_type": "training_centre",
        "title": "Basic Electrical Repair — October Batch",
        "summary": "Practical training with industry certification and toolkit",
        "district_id": "District Alpha",
        "block_id": "Block Alpha-1",
        "location_text": "Room 102, Alpha Skills Centre",
        "delivery_mode": "offline_centre",
        "start_date": future_start,
        "seats_total": 25,
        "seats_available": 20,
        "status": "DRAFT"
    }
    create_opp_res = client.post("/api/v1/staff/opportunities", json=draft_opp_payload, headers=headers_fw_alpha)
    assert create_opp_res.status_code == 201
    opp_data = create_opp_res.json()
    opp_id = opp_data["id"]
    assert opp_data["status"] == "DRAFT"

    # Assertion 3.1: Opportunity is not listed in beneficiary opportunities
    ben_opps_res = client.get("/api/v1/opportunities")
    assert ben_opps_res.status_code == 200
    assert not any(o["id"] == opp_id for o in ben_opps_res.json())

    # Assertion 3.2: Still produces only INTEREST_MATCH for beneficiary
    match_res2 = client.get(f"/api/v1/opportunities/matches/{qual_id}?district_id=District%20Alpha", headers=headers_ben)
    assert match_res2.json()["matchState"] == "INTEREST_MATCH"
    assert match_res2.json()["canRequestReferral"] is False

    # Assertion 3.3: Audit event recorded for creation
    with get_db() as conn:
        audit_row = conn.execute(
            "SELECT * FROM audit_events WHERE entity_id = ? AND action = 'LOCAL_OPPORTUNITY_CREATED'",
            (opp_id,)
        ).fetchone()
        assert audit_row is not None
        assert audit_row["actor_user_id"] == "usr_fw_alpha"

    # =========================================================================
    # STEP 4 — Invalid verification prevention
    # Actor: field_worker_alpha
    # =========================================================================
    # Attempt verification without approved evidence attached
    invalid_verify_res = client.post(
        f"/api/v1/staff/opportunities/{opp_id}/verify",
        json={"action": "verify", "verification_expires_at": future_expiry},
        headers=headers_fw_alpha
    )
    assert invalid_verify_res.status_code == 400
    assert "evidence" in invalid_verify_res.json()["detail"].lower()

    # Verify status is still DRAFT in database
    with get_db() as conn:
        db_opp = conn.execute("SELECT status FROM local_opportunities WHERE id = ?", (opp_id,)).fetchone()
        assert db_opp["status"] == "DRAFT"

    # =========================================================================
    # STEP 5 — Submit evidence and verify
    # Actor: field_worker_alpha
    # =========================================================================
    # Attach approved evidence (Field Visit report)
    evidence_res = client.post(
        f"/api/v1/staff/opportunities/{opp_id}/evidence",
        json={
            "evidence_type": "FIELD_VISIT",
            "storage_key": "private/evidence/alpha_inspection_report.pdf",
            "note": "Verified electrical lab equipment and instructor credentials",
            "is_approved": True
        },
        headers=headers_fw_alpha
    )
    assert evidence_res.status_code == 201
    assert evidence_res.json()["is_approved"] == 1

    # Transition: DRAFT -> PENDING_VERIFICATION
    submit_res = client.post(
        f"/api/v1/staff/opportunities/{opp_id}/submit",
        json={"action": "submit", "reason": "Ready for verification"},
        headers=headers_fw_alpha
    )
    assert submit_res.status_code == 200
    assert submit_res.json()["status"] == "PENDING_VERIFICATION"

    # Transition: PENDING_VERIFICATION -> ACTIVE (verify)
    verify_res = client.post(
        f"/api/v1/staff/opportunities/{opp_id}/verify",
        json={"action": "verify", "verification_expires_at": future_expiry, "reason": "Site inspection approved"},
        headers=headers_fw_alpha
    )
    assert verify_res.status_code == 200
    verified_opp = verify_res.json()
    assert verified_opp["status"] == "ACTIVE"
    assert verified_opp["verified_by_user_id"] == "usr_fw_alpha"
    assert verified_opp["verified_at"] is not None
    assert verified_opp["verification_expires_at"] is not None

    # Check database state
    with get_db() as conn:
        # Verification history event
        ver_event = conn.execute(
            "SELECT * FROM opportunity_verification_events WHERE opportunity_id = ? AND new_status = 'ACTIVE'",
            (opp_id,)
        ).fetchone()
        assert ver_event is not None
        assert ver_event["actor_user_id"] == "usr_fw_alpha"
        assert ver_event["verification_action"] == "VERIFIED"

        # Append-only audit event
        audit_event = conn.execute(
            "SELECT * FROM audit_events WHERE entity_id = ? AND action = 'OPPORTUNITY_VERIFIED'",
            (opp_id,)
        ).fetchone()
        assert audit_event is not None

    # Staff detail shows evidence and verification history
    staff_detail_res = client.get(f"/api/v1/staff/opportunities/{opp_id}", headers=headers_fw_alpha)
    assert staff_detail_res.status_code == 200
    staff_opp = staff_detail_res.json()
    assert len(staff_opp["evidence"]) >= 1
    assert len(staff_opp["verification_history"]) >= 1

    # =========================================================================
    # STEP 6 — Verified Match computation
    # Actor: beneficiary_a
    # =========================================================================
    # Query match endpoint
    ver_match_res = client.get(
        f"/api/v1/opportunities/matches/{qual_id}?district_id=District%20Alpha&block_id=Block%20Alpha-1",
        headers=headers_ben
    )
    assert ver_match_res.status_code == 200
    ver_match_data = ver_match_res.json()
    assert ver_match_data["matchState"] == "VERIFIED_MATCH"
    assert ver_match_data["canRequestReferral"] is True
    assert ver_match_data["verificationUpdatedAt"] is not None
    assert "verified" in ver_match_data["beneficiaryMessage"].lower()

    # Generate recommendations again
    rec_gen_res2 = client.post(
        "/api/v1/recommendations/generate",
        json={"beneficiary_id": "usr_ben_a"},
        headers=headers_ben
    )
    assert rec_gen_res2.status_code == 200
    top_rec = rec_gen_res2.json()["recommendations"][0]
    assert top_rec["match_state"] == "VERIFIED_MATCH"
    assert top_rec["can_request_referral"] is True
    assert top_rec["local_availability"]["status"] == "verified_open"

    # Confirm database recommendation_match_state is VERIFIED_MATCH
    with get_db() as conn:
        row = conn.execute(
            "SELECT match_state, local_opportunity_id FROM recommendation_match_state WHERE beneficiary_id = ? AND qualification_id = ?",
            ("usr_ben_a", qual_id)
        ).fetchone()
        assert row["match_state"] == "VERIFIED_MATCH"
        assert row["local_opportunity_id"] == opp_id

    # =========================================================================
    # STEP 7 — Cross-scope access denial
    # Actor: field_worker_beta (District Beta / Block Beta-1)
    # =========================================================================
    # 7.1 Attempt to read Alpha opportunity staff detail
    res_7_1 = client.get(f"/api/v1/staff/opportunities/{opp_id}", headers=headers_fw_beta)
    assert res_7_1.status_code == 403

    # 7.2 Attempt to attach evidence
    res_7_2 = client.post(
        f"/api/v1/staff/opportunities/{opp_id}/evidence",
        json={"evidence_type": "FIELD_VISIT", "note": "Hacked evidence"},
        headers=headers_fw_beta
    )
    assert res_7_2.status_code == 403

    # 7.3 Attempt to verify / reverify
    res_7_3 = client.post(
        f"/api/v1/staff/opportunities/{opp_id}/verify",
        json={"action": "verify", "verification_expires_at": future_expiry},
        headers=headers_fw_beta
    )
    assert res_7_3.status_code == 403

    # 7.4 Attempt to change seats
    res_7_4 = client.patch(
        f"/api/v1/staff/opportunities/{opp_id}",
        json={"seats_available": 0},
        headers=headers_fw_beta
    )
    assert res_7_4.status_code == 403

    # 7.5 Attempt to close opportunity
    res_7_5 = client.post(
        f"/api/v1/staff/opportunities/{opp_id}/close",
        json={"action": "close"},
        headers=headers_fw_beta
    )
    assert res_7_5.status_code == 403

    # Confirm Alpha opportunity was completely untouched
    with get_db() as conn:
        curr_opp = conn.execute("SELECT status, seats_available FROM local_opportunities WHERE id = ?", (opp_id,)).fetchone()
        assert curr_opp["status"] == "ACTIVE"
        assert curr_opp["seats_available"] == 20

        # Verify security denial audit event was logged
        sec_audit = conn.execute(
            "SELECT * FROM audit_events WHERE entity_id = ? AND action = 'SECURITY_ACCESS_DENIED' AND actor_user_id = 'usr_fw_beta'",
            (opp_id,)
        ).fetchall()
        assert len(sec_audit) >= 1

    # =========================================================================
    # STEP 8 — Beneficiary data-exposure check
    # Actor: beneficiary_a
    # =========================================================================
    prohibited_fields = {
        "storage_key", "external_url", "note", "contact_phone", "contact_email",
        "verified_by_user_id", "created_by_user_id", "actor_user_id",
        "before_json", "after_json", "metadata_json", "eligibility_notes", "accessibility_notes"
    }

    # 8.1 Opportunities list
    opps_list = client.get("/api/v1/opportunities").json()
    assert len(opps_list) > 0
    for o in opps_list:
        for f in prohibited_fields:
            assert f not in o, f"Prohibited field '{f}' leaked in opportunities list"

    # 8.2 Opportunity detail
    opp_detail = client.get(f"/api/v1/opportunities/{opp_id}").json()
    for f in prohibited_fields:
        assert f not in opp_detail, f"Prohibited field '{f}' leaked in opportunity detail"

    # 8.3 Recommendations generate response
    rec_res = client.post("/api/v1/recommendations/generate", json={"beneficiary_id": "usr_ben_a"}, headers=headers_ben).json()
    for rec in rec_res["recommendations"]:
        for f in prohibited_fields:
            assert f not in rec, f"Prohibited field '{f}' leaked in recommendation payload"
            if "local_availability" in rec:
                assert f not in rec["local_availability"], f"Prohibited field '{f}' leaked in local_availability"

    # 8.4 Qualification detail
    qual_detail = client.get(f"/api/v1/qualifications/{qual_id}").json()
    for f in ("source_url", "created_by_user_id", "verified_by_user_id"):
        assert f not in qual_detail, f"Prohibited field '{f}' leaked in qualification detail"

    # =========================================================================
    # STEP 9 — Capacity state behavior
    # Actor: field_worker_alpha
    # =========================================================================
    # Set available seats to 0
    cap_res = client.patch(
        f"/api/v1/staff/opportunities/{opp_id}",
        json={"seats_available": 0},
        headers=headers_fw_alpha
    )
    assert cap_res.status_code == 200
    assert cap_res.json()["status"] == "FULL"
    assert cap_res.json()["seats_available"] == 0

    # Beneficiary no longer receives VERIFIED_MATCH
    match_res_full = client.get(
        f"/api/v1/opportunities/matches/{qual_id}?district_id=District%20Alpha",
        headers=headers_ben
    )
    assert match_res_full.status_code == 200
    assert match_res_full.json()["matchState"] == "INTEREST_MATCH"
    assert match_res_full.json()["canRequestReferral"] is False

    # Recommendations also return INTEREST_MATCH
    rec_full_res = client.post("/api/v1/recommendations/generate", json={"beneficiary_id": "usr_ben_a"}, headers=headers_ben)
    assert rec_full_res.json()["recommendations"][0]["match_state"] == "INTEREST_MATCH"
    assert rec_full_res.json()["recommendations"][0]["can_request_referral"] is False

    # Check database audit and verification events
    with get_db() as conn:
        evt = conn.execute("SELECT * FROM opportunity_verification_events WHERE opportunity_id = ? AND new_status = 'FULL'", (opp_id,)).fetchone()
        assert evt is not None
        assert evt["verification_action"] == "MARKED_FULL"

    # =========================================================================
    # STEP 10 — Reverification behavior
    # Actor: field_worker_alpha
    # =========================================================================
    # Restore valid capacity
    client.patch(
        f"/api/v1/staff/opportunities/{opp_id}",
        json={"seats_available": 15},
        headers=headers_fw_alpha
    )

    # Reverify opportunity with future expiry
    new_future_expiry = (datetime.now(timezone.utc) + timedelta(days=90)).isoformat()
    rever_res = client.post(
        f"/api/v1/staff/opportunities/{opp_id}/reverify",
        json={"action": "reverify", "verification_expires_at": new_future_expiry, "reason": "New seats allocated"},
        headers=headers_fw_alpha
    )
    assert rever_res.status_code == 200
    assert rever_res.json()["status"] == "ACTIVE"
    assert rever_res.json()["seats_available"] == 15

    # Check verification history has appended event, old events are preserved
    with get_db() as conn:
        all_events = conn.execute(
            "SELECT * FROM opportunity_verification_events WHERE opportunity_id = ? ORDER BY created_at ASC",
            (opp_id,)
        ).fetchall()
        assert len(all_events) >= 3  # SUBMITTED, VERIFIED, MARKED_FULL, REVERIFIED
        assert any(e["verification_action"] == "REVERIFIED" for e in all_events)

    # Beneficiary can receive VERIFIED_MATCH again
    match_res_rever = client.get(
        f"/api/v1/opportunities/matches/{qual_id}?district_id=District%20Alpha",
        headers=headers_ben
    )
    assert match_res_rever.json()["matchState"] == "VERIFIED_MATCH"
    assert match_res_rever.json()["canRequestReferral"] is True

    # =========================================================================
    # STEP 11 — Expiry at read time
    # Actor: system clock / DB state
    # =========================================================================
    # In database: set verification_expires_at in the past WITHOUT running scheduled expiry job
    past_expiry = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()
    with get_db() as conn:
        conn.execute("UPDATE local_opportunities SET verification_expires_at = ? WHERE id = ?", (past_expiry, opp_id))

    # Read-time checks treat opportunity as expired immediately
    # 11.1 Beneficiary opportunities list excludes it
    active_opps = client.get("/api/v1/opportunities").json()
    assert not any(o["id"] == opp_id for o in active_opps)

    # 11.2 Single opportunity detail returns 404 (expired)
    single_opp_res = client.get(f"/api/v1/opportunities/{opp_id}")
    assert single_opp_res.status_code == 404

    # 11.3 Matches degrade to INTEREST_MATCH
    match_res_exp = client.get(
        f"/api/v1/opportunities/matches/{qual_id}?district_id=District%20Alpha",
        headers=headers_ben
    )
    assert match_res_exp.json()["matchState"] == "INTEREST_MATCH"
    assert match_res_exp.json()["canRequestReferral"] is False

    # 11.4 In database, stored status is still ACTIVE temporarily
    with get_db() as conn:
        status_in_db = conn.execute("SELECT status FROM local_opportunities WHERE id = ?", (opp_id,)).fetchone()["status"]
        assert status_in_db == "ACTIVE"

    # =========================================================================
    # STEP 12 — Scheduled expiry and auditability
    # Actor: expiry CLI/job, then auditor_alpha
    # =========================================================================
    # 12.1 Dry run reports candidate but does not mutate
    with get_db() as conn:
        dry_run_expired = OpportunityExpiryService.process_expiries(conn, dry_run=True)
        assert opp_id in dry_run_expired
        curr_status = conn.execute("SELECT status FROM local_opportunities WHERE id = ?", (opp_id,)).fetchone()["status"]
        assert curr_status == "ACTIVE"

    # 12.2 First real run changes status to EXPIRED
    with get_db() as conn:
        real_expired = OpportunityExpiryService.process_expiries(conn, dry_run=False)
        assert opp_id in real_expired
        curr_status = conn.execute("SELECT status FROM local_opportunities WHERE id = ?", (opp_id,)).fetchone()["status"]
        assert curr_status == "EXPIRED"

        # Verification history event ACTIVE -> EXPIRED recorded
        exp_event = conn.execute(
            "SELECT * FROM opportunity_verification_events WHERE opportunity_id = ? AND new_status = 'EXPIRED'",
            (opp_id,)
        ).fetchone()
        assert exp_event is not None
        assert exp_event["verification_action"] == "EXPIRED"

        # Audit event records expiry
        exp_audit = conn.execute(
            "SELECT * FROM audit_events WHERE entity_id = ? AND action = 'OPPORTUNITY_EXPIRED'",
            (opp_id,)
        ).fetchone()
        assert exp_audit is not None

    # 12.3 Second real run is idempotent (0 opportunities expired)
    with get_db() as conn:
        second_run_expired = OpportunityExpiryService.process_expiries(conn, dry_run=False)
        assert len(second_run_expired) == 0

    # 12.4 Auditor alpha inspections and mutation restrictions
    # Auditor CAN view audit events
    audit_res = client.get("/api/v1/audit/events?entity_type=local_opportunity", headers=headers_auditor)
    assert audit_res.status_code == 200
    assert len(audit_res.json()) >= 1

    # Auditor CAN view staff opportunity detail
    auditor_staff_res = client.get(f"/api/v1/staff/opportunities/{opp_id}", headers=headers_auditor)
    assert auditor_staff_res.status_code == 200
    assert auditor_staff_res.json()["status"] == "EXPIRED"

    # Auditor CANNOT create or mutate opportunities
    auditor_create_res = client.post(
        "/api/v1/staff/opportunities",
        json=draft_opp_payload,
        headers=headers_auditor
    )
    assert auditor_create_res.status_code == 403

    auditor_verify_res = client.post(
        f"/api/v1/staff/opportunities/{opp_id}/verify",
        json={"action": "verify", "verification_expires_at": future_expiry},
        headers=headers_auditor
    )
    assert auditor_verify_res.status_code == 403

    auditor_patch_res = client.patch(
        f"/api/v1/staff/opportunities/{opp_id}",
        json={"seats_available": 10},
        headers=headers_auditor
    )
    assert auditor_patch_res.status_code == 403
