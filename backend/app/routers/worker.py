from fastapi import APIRouter, HTTPException
import uuid
import json
from datetime import datetime, timezone
from app.database import get_db
from app.models import ProfileCorrectionRequest, BatchVerificationRequest, ApproveReferralRequest
from app.ai_layers.layer4_copilot.outbound_messaging import OutboundMessaging

router = APIRouter(prefix="/worker", tags=["Field-Worker"])

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
def correct_profile(beneficiary_id: str, req: ProfileCorrectionRequest):
    now = datetime.now(timezone.utc).isoformat()
    with get_db() as conn:
        ans_id = f"ans_corr_{uuid.uuid4().hex[:8]}"
        conn.execute("""
            INSERT INTO profile_answers (
                id, beneficiary_id, field_name, field_value, confidence_score,
                confirmation_status, source, created_at, updated_at
            ) VALUES (?, ?, ?, ?, 1.0, 'corrected', 'worker_correction', ?, ?);
        """, (ans_id, beneficiary_id, req.field_name, str(req.field_value), now, now))

        # Log audit event
        audit_id = f"aud_{uuid.uuid4().hex[:8]}"
        conn.execute("""
            INSERT INTO audit_events (
                id, actor_id, actor_name, actor_role, action, entity_type,
                entity_id, new_values, timestamp
            ) VALUES (?, 'worker_sunita_01', 'Sunita Devi', 'field_worker', 'profile_field_correction',
                      'profile_answers', ?, ?, ?);
        """, (audit_id, ans_id, json.dumps({req.field_name: req.field_value}), now))

        return {
            "status": "corrected",
            "message": f"Field '{req.field_name}' corrected by field worker."
        }

@router.post("/cases/{beneficiary_id}/referral", status_code=201)
def approve_referral(beneficiary_id: str, req: ApproveReferralRequest):
    now = datetime.now(timezone.utc).isoformat()
    with get_db() as conn:
        ref_id = f"ref_{uuid.uuid4().hex[:10]}"
        conn.execute("""
            INSERT INTO referrals (
                id, beneficiary_id, recommendation_id, local_opportunity_id,
                assigned_worker_id, status, notes, caste_document_verified,
                income_criteria_verified, residence_proof_verified, sms_sent,
                whatsapp_sent, next_follow_up, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, 'documents_verified', ?, ?, ?, ?, 1, 1, ?, ?, ?);
        """, (
            ref_id, beneficiary_id, req.recommendation_id, req.local_opportunity_id,
            req.assigned_worker_id, req.notes or "Referral approved with verified documents.",
            1 if req.caste_document_verified else 0,
            1 if req.income_criteria_verified else 0,
            1 if req.residence_proof_verified else 0,
            "2026-10-15", now, now
        ))

        # Update recommendation to Verified Match
        conn.execute("""
            UPDATE recommendations SET match_state = 'Verified Match', updated_at = ? WHERE id = ?;
        """, (now, req.recommendation_id))

        # Log audit event
        audit_id = f"aud_{uuid.uuid4().hex[:8]}"
        conn.execute("""
            INSERT INTO audit_events (
                id, actor_id, actor_name, actor_role, action, entity_type,
                entity_id, new_values, timestamp
            ) VALUES (?, ?, 'Sunita Devi', 'field_worker', 'referral_approved_verified_match',
                      'referrals', ?, ?, ?);
        """, (audit_id, req.assigned_worker_id, ref_id, json.dumps({"status": "documents_verified"}), now))

        return {
            "referral_id": ref_id,
            "status": "documents_verified",
            "match_state": "Verified Match",
            "message": "Referral approved and confirmed under Claim 1 Verified Match Protocol."
        }
