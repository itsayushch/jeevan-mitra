from datetime import datetime, timedelta, timezone
import secrets
import uuid
import json
from fastapi import APIRouter, Depends, Header, HTTPException
from app.database import get_db
from app.core.settings import settings
from app.models import ProfileCorrectionRequest, BatchVerificationRequest, ApproveReferralRequest
from app.ai_layers.layer3_matching.state_machine import MatchStateMachine
from app.dependencies.auth import require_admin_or_worker, Actor

def _record_worker_audit(conn, worker: Actor, action, entity_type, entity_id, old_values=None, new_values=None, metadata=None):
    conn.execute("""
        INSERT INTO audit_events (
            id, actor_id, actor_name, actor_role, action, entity_type,
            entity_id, old_values, new_values, metadata, timestamp
        ) VALUES (?, ?, ?, 'field_worker', ?, ?, ?, ?, ?, ?, ?);
    """, (
        f"aud_{uuid.uuid4().hex[:8]}", worker.actor_id, worker.actor_role, action,
        entity_type, entity_id,
        json.dumps(old_values) if old_values is not None else None,
        json.dumps(new_values) if new_values is not None else None,
        json.dumps(metadata) if metadata is not None else None,
        datetime.now(timezone.utc).isoformat()
    ))

router = APIRouter(
    prefix="/worker",
    tags=["Field-Worker"],
    dependencies=[Depends(require_admin_or_worker)]
)

@router.get("/cases")
def list_worker_cases(district: str = "Moradabad"):
    with get_db() as conn:
        rows = conn.execute("""
            SELECT b.id as beneficiary_id, b.name, b.phone, b.village, b.block, b.district,
                   b.created_at, s.id as session_id, s.status as session_status
            FROM beneficiaries b
            LEFT JOIN interview_sessions s ON b.id = s.beneficiary_id
            WHERE b.district = ?
            ORDER BY b.created_at DESC;
        """, (district,)).fetchall()
        return [dict(r) for r in rows]

@router.get("/cases/{beneficiary_id}")
def get_case_detail(beneficiary_id: str):
    with get_db() as conn:
        ben = conn.execute("SELECT * FROM beneficiaries WHERE id = ?;", (beneficiary_id,)).fetchone()
        if not ben:
            raise HTTPException(status_code=404, detail="Beneficiary case not found")

        answers = conn.execute("""
            SELECT * FROM profile_answers WHERE beneficiary_id = ? ORDER BY created_at ASC;
        """, (beneficiary_id,)).fetchall()

        session = conn.execute("""
            SELECT * FROM interview_sessions WHERE beneficiary_id = ? ORDER BY created_at DESC LIMIT 1;
        """, (beneficiary_id,)).fetchone()

        recs = conn.execute("""
            SELECT r.*, q.title as qual_title, o.centre_or_employer_name
            FROM recommendations r
            JOIN qualifications q ON r.qualification_id = q.id
            LEFT JOIN local_opportunities o ON r.local_opportunity_id = o.id
            WHERE r.beneficiary_id = ?
            ORDER BY r.rank ASC;
        """, (beneficiary_id,)).fetchall()

        return {
            "beneficiary": dict(ben),
            "profile_answers": [dict(a) for a in answers],
            "session": dict(session) if session else None,
            "recommendations": [dict(r) for r in recs]
        }

@router.patch("/cases/{beneficiary_id}/profile")
def correct_profile(
    beneficiary_id: str,
    req: ProfileCorrectionRequest,
    worker: Actor = Depends(require_admin_or_worker)
):
    now = datetime.now(timezone.utc).isoformat()
    with get_db() as conn:
        ans_id = f"ans_corr_{uuid.uuid4().hex[:8]}"
        conn.execute("""
            INSERT INTO profile_answers (
                id, beneficiary_id, field_name, field_value, confidence_score,
                confirmation_status, source, created_at, updated_at
            ) VALUES (?, ?, ?, ?, 1.0, 'corrected', 'worker_correction', ?, ?);
        """, (ans_id, beneficiary_id, req.field_name, str(req.field_value), now, now))

        _record_worker_audit(
            conn, worker, "profile_field_correction", "profile_answers", ans_id,
            new_values={req.field_name: req.field_value}
        )

        return {
            "status": "corrected",
            "message": f"Field '{req.field_name}' corrected by field worker."
        }

@router.post("/opportunities/{opportunity_id}/verify")
def verify_opportunity(
    opportunity_id: str,
    req: BatchVerificationRequest,
    worker: Actor = Depends(require_admin_or_worker)
):
    now = datetime.now(timezone.utc)
    today = now.date().isoformat()
    with get_db() as conn:
        if not req.notes.strip():
            raise HTTPException(status_code=422, detail="Verification evidence notes are required")
        opportunity = conn.execute(
            "SELECT * FROM local_opportunities WHERE id = ?;",
            (opportunity_id,)
        ).fetchone()
        if not opportunity:
            raise HTTPException(status_code=404, detail="Opportunity not found")
        if req.available_seats > opportunity["total_seats"]:
            raise HTTPException(status_code=422, detail="Available seats cannot exceed total seats")
        if req.batch_status in ("active", "upcoming") and req.available_seats == 0:
            raise HTTPException(status_code=422, detail="Use full status when no seats remain")
        if req.batch_status in ("full", "completed", "cancelled") and req.available_seats != 0:
            raise HTTPException(status_code=422, detail="Closed opportunities must have zero available seats")

        old_values = {
            "available_seats": opportunity["available_seats"],
            "batch_status": opportunity["batch_status"],
            "verified_by_worker_id": opportunity["verified_by_worker_id"],
            "verified_at": opportunity["verified_at"]
        }
        is_verified = (
            req.batch_status in ("active", "upcoming")
            and req.available_seats > 0
            and opportunity["batch_end_date"] >= today
        )
        verified_by = worker.actor_id if is_verified else None
        conn.execute("""
            UPDATE local_opportunities
            SET available_seats = ?, batch_status = ?, verified_by_worker_id = ?, verified_at = ?
            WHERE id = ?;
        """, (req.available_seats, req.batch_status, verified_by, now.isoformat(), opportunity_id))

        target_state = "Verified Match" if is_verified else "Interest Match"
        recommendations = conn.execute("""
            SELECT id, match_state FROM recommendations WHERE local_opportunity_id = ?;
        """, (opportunity_id,)).fetchall()
        changed_recommendations = 0
        for recommendation in recommendations:
            if recommendation["match_state"] == target_state:
                continue
            if is_verified:
                MatchStateMachine.validate_transition(
                    recommendation["match_state"], target_state, "field_worker", True
                )
            conn.execute(
                "UPDATE recommendations SET match_state = ?, updated_at = ? WHERE id = ?;",
                (target_state, now.isoformat(), recommendation["id"])
            )
            changed_recommendations += 1
            _record_worker_audit(
                conn, worker, "match_state_changed", "recommendations", recommendation["id"],
                old_values={"match_state": recommendation["match_state"]},
                new_values={"match_state": target_state, "opportunity_id": opportunity_id}
            )

        _record_worker_audit(
            conn, worker, "opportunity_verification_updated", "local_opportunities", opportunity_id,
            old_values=old_values,
            new_values={
                "available_seats": req.available_seats,
                "batch_status": req.batch_status,
                "verified_by_worker_id": verified_by,
                "verified_at": now.isoformat()
            },
            metadata={"evidence_notes": req.notes.strip()}
        )

        return {
            "opportunity_id": opportunity_id,
            "verified": is_verified,
            "batch_status": req.batch_status,
            "available_seats": req.available_seats,
            "recommendations_updated": changed_recommendations
        }

@router.post("/cases/{beneficiary_id}/referral", status_code=201)
def approve_referral(
    beneficiary_id: str,
    req: ApproveReferralRequest,
    worker: Actor = Depends(require_admin_or_worker)
):
    now = datetime.now(timezone.utc)
    today = now.date().isoformat()
    error = None
    referral = None
    with get_db() as conn:
        recommendation = conn.execute("""
            SELECT beneficiary_id, local_opportunity_id, match_state
            FROM recommendations WHERE id = ?;
        """, (req.recommendation_id,)).fetchone()
        if not recommendation:
            raise HTTPException(status_code=404, detail="Recommendation not found")
        if recommendation["beneficiary_id"] != beneficiary_id:
            raise HTTPException(status_code=409, detail="Recommendation does not belong to beneficiary")
        if recommendation["local_opportunity_id"] != req.local_opportunity_id:
            raise HTTPException(status_code=409, detail="Recommendation is not linked to this opportunity")
        if recommendation["match_state"] != "Verified Match":
            raise HTTPException(status_code=409, detail="Opportunity must be worker-verified before referral")

        opportunity = conn.execute("""
            SELECT batch_status, available_seats, batch_end_date, verified_by_worker_id
            FROM local_opportunities WHERE id = ?;
        """, (req.local_opportunity_id,)).fetchone()
        if (
            not opportunity
            or opportunity["batch_status"] not in ("active", "upcoming")
            or opportunity["available_seats"] <= 0
            or not opportunity["verified_by_worker_id"]
            or opportunity["batch_end_date"] < today
        ):
            raise HTTPException(status_code=409, detail="Verified opportunity is no longer available")

        consent = conn.execute("""
            SELECT dpdp_affirmative_consent FROM consents
            WHERE beneficiary_id = ?
            ORDER BY timestamp DESC, rowid DESC LIMIT 1;
        """, (beneficiary_id,)).fetchone()
        if not consent or not consent["dpdp_affirmative_consent"]:
            raise HTTPException(status_code=403, detail="Affirmative consent is required for referral")
        if not all((req.caste_document_verified, req.income_criteria_verified, req.residence_proof_verified)):
            raise HTTPException(status_code=409, detail="Required eligibility documents have not all been verified")
        existing_referral = conn.execute("""
            SELECT id FROM referrals
            WHERE recommendation_id = ? AND status NOT IN ('rejected', 'ineligible')
            LIMIT 1;
        """, (req.recommendation_id,)).fetchone()
        if existing_referral:
            raise HTTPException(status_code=409, detail="An open referral already exists for this recommendation")

        ref_id = f"ref_{uuid.uuid4().hex[:10]}"
        next_follow_up = (now + timedelta(days=7)).date().isoformat()
        conn.execute("""
            INSERT INTO referrals (
                id, beneficiary_id, recommendation_id, local_opportunity_id,
                assigned_worker_id, status, notes, caste_document_verified,
                income_criteria_verified, residence_proof_verified, sms_sent,
                whatsapp_sent, next_follow_up, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, 'documents_verified', ?, 1, 1, 1, 0, 0, ?, ?, ?);
        """, (
            ref_id, beneficiary_id, req.recommendation_id, req.local_opportunity_id,
            worker.actor_id, req.notes, next_follow_up, now.isoformat(), now.isoformat()
        ))
        _record_worker_audit(
            conn, worker, "referral_created", "referrals", ref_id,
            new_values={"status": "documents_verified", "recommendation_id": req.recommendation_id,
                        "local_opportunity_id": req.local_opportunity_id}
        )
        referral = {"referral_id": ref_id, "status": "documents_verified", "match_state": "Verified Match"}

    return {
        **referral,
        "message": "Referral recorded for the worker-verified opportunity."
    }
