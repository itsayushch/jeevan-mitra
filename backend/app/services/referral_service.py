import uuid
import sqlite3
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from app.models import CreateReferralRequest, AssignCounselorRequest, UpdateReferralStatusRequest, AddCounselorNoteRequest
from app.dependencies.consent import verify_consent
from app.utils.audit_events import log_audit_event
from app.utils.errors import EntityNotFoundException, UnauthorizedAccessException, ValidationException

class ReferralService:
    ALLOWED_REASONS = [
        'no_verified_local_option',
        'user_requested_human_help',
        'accessibility_support_required',
        'complex_eligibility_query',
        'low_confidence_profile',
        'technical_issue'
    ]

    ALLOWED_STATUSES = ['new', 'assigned', 'contacted', 'in_progress', 'resolved', 'closed']

    @staticmethod
    def create_referral(conn: sqlite3.Connection, data: CreateReferralRequest, actor) -> Dict[str, Any]:
        target_ben_id = data.beneficiary_id or actor.beneficiary_id
        target_interview_id = data.interview_id or actor.session_id

        # Mandatory Consent Check: Counselor referral consent is strictly required
        verify_consent(conn, "counselor_referral", target_ben_id, actor.session_id or target_interview_id)

        if data.referral_reason not in ReferralService.ALLOWED_REASONS:
            raise ValidationException(f"Invalid referral reason '{data.referral_reason}'. Must be one of {ReferralService.ALLOWED_REASONS}")

        case_id = f"case_{uuid.uuid4().hex[:10]}"
        now = datetime.now(timezone.utc).isoformat()

        conn.execute("""
            INSERT INTO referral_cases (
                id, beneficiary_id, interview_id, recommendation_id, local_opportunity_id,
                referral_reason, consent_verification_state, status, priority, notes, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, 'verified', 'new', ?, ?, ?, ?);
        """, (
            case_id, target_ben_id, target_interview_id, data.recommendation_id,
            data.local_opportunity_id, data.referral_reason, data.priority or "medium",
            data.notes, now, now
        ))

        # Also create entry in legacy referrals table if recommendation and opportunity exist
        if data.recommendation_id and data.local_opportunity_id:
            legacy_id = f"ref_{uuid.uuid4().hex[:10]}"
            conn.execute("""
                INSERT OR IGNORE INTO referrals (
                    id, beneficiary_id, recommendation_id, local_opportunity_id, assigned_worker_id,
                    status, notes, created_at, updated_at
                ) VALUES (?, ?, ?, ?, 'unassigned', 'pending', ?, ?, ?);
            """, (legacy_id, target_ben_id or "anonymous", data.recommendation_id, data.local_opportunity_id, data.notes, now, now))

        log_audit_event(
            conn=conn,
            actor_id=actor.actor_id,
            actor_name=actor.actor_name,
            actor_role=actor.actor_role,
            action="REFERRAL_CASE_CREATED",
            entity_type="referral_case",
            entity_id=case_id,
            new_values=data.model_dump()
        )

        row = conn.execute("SELECT * FROM referral_cases WHERE id = ?;", (case_id,)).fetchone()
        res = dict(row)
        res["user_safe_message"] = "Your referral request has been submitted for career counselor review. Support staff will review local options and follow up based on resource availability."
        return res

    @staticmethod
    def get_my_referrals(conn: sqlite3.Connection, actor) -> List[Dict[str, Any]]:
        target_ben_id = actor.beneficiary_id
        session_id = actor.session_id or actor.actor_id

        rows = conn.execute("""
            SELECT * FROM referral_cases
            WHERE (beneficiary_id IS NOT NULL AND beneficiary_id = ?)
               OR (interview_id IS NOT NULL AND interview_id = ?)
            ORDER BY created_at DESC;
        """, (target_ben_id or "", session_id)).fetchall()

        return [dict(r) for r in rows]

    @staticmethod
    def list_counselor_referrals(conn: sqlite3.Connection, actor, status: Optional[str] = None) -> List[Dict[str, Any]]:
        # Staff check
        if actor.actor_role not in ["counselor", "admin", "district_officer", "field_worker"]:
            raise UnauthorizedAccessException("Only authorized counselors and administrators may access the counselor queue.")

        query = "SELECT * FROM referral_cases WHERE 1=1"
        params = []

        # If counselor is not admin, show unassigned cases or cases assigned to them
        if actor.actor_role == "counselor":
            query += " AND (assigned_counselor_id = ? OR assigned_counselor_id IS NULL)"
            params.append(actor.actor_id)

        if status:
            query += " AND status = ?"
            params.append(status)

        query += " ORDER BY created_at DESC;"
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def assign_counselor(conn: sqlite3.Connection, referral_id: str, data: AssignCounselorRequest, actor) -> Dict[str, Any]:
        existing = conn.execute("SELECT * FROM referral_cases WHERE id = ?;", (referral_id,)).fetchone()
        if not existing:
            raise EntityNotFoundException("ReferralCase", referral_id)

        now = datetime.now(timezone.utc).isoformat()
        conn.execute("""
            UPDATE referral_cases
            SET assigned_counselor_id = ?, status = 'assigned', updated_at = ?
            WHERE id = ?;
        """, (data.counselor_id, now, referral_id))

        log_audit_event(
            conn=conn,
            actor_id=actor.actor_id,
            actor_name=actor.actor_name,
            actor_role=actor.actor_role,
            action="REFERRAL_COUNSELOR_ASSIGNED",
            entity_type="referral_case",
            entity_id=referral_id,
            new_values={"assigned_counselor_id": data.counselor_id, "status": "assigned"}
        )

        row = conn.execute("SELECT * FROM referral_cases WHERE id = ?;", (referral_id,)).fetchone()
        return dict(row)

    @staticmethod
    def update_status(conn: sqlite3.Connection, referral_id: str, data: UpdateReferralStatusRequest, actor) -> Dict[str, Any]:
        existing = conn.execute("SELECT * FROM referral_cases WHERE id = ?;", (referral_id,)).fetchone()
        if not existing:
            raise EntityNotFoundException("ReferralCase", referral_id)

        # Assignment verification: If counselor, must be assigned to case or admin
        if actor.actor_role == "counselor" and existing["assigned_counselor_id"] != actor.actor_id:
            raise UnauthorizedAccessException("You are not assigned to this referral case.")

        now = datetime.now(timezone.utc).isoformat()
        set_clauses = ["status = ?", "updated_at = ?"]
        params = [data.status, now]

        if data.outcome:
            set_clauses.append("outcome = ?")
            params.append(data.outcome)
        if data.notes:
            set_clauses.append("notes = ?")
            params.append(data.notes)

        params.append(referral_id)
        conn.execute(f"UPDATE referral_cases SET {', '.join(set_clauses)} WHERE id = ?;", params)

        log_audit_event(
            conn=conn,
            actor_id=actor.actor_id,
            actor_name=actor.actor_name,
            actor_role=actor.actor_role,
            action="REFERRAL_STATUS_UPDATED",
            entity_type="referral_case",
            entity_id=referral_id,
            old_values={"status": existing["status"]},
            new_values={"status": data.status, "outcome": data.outcome}
        )

        row = conn.execute("SELECT * FROM referral_cases WHERE id = ?;", (referral_id,)).fetchone()
        return dict(row)

    @staticmethod
    def add_counselor_note(conn: sqlite3.Connection, referral_id: str, data: AddCounselorNoteRequest, actor) -> Dict[str, Any]:
        existing = conn.execute("SELECT * FROM referral_cases WHERE id = ?;", (referral_id,)).fetchone()
        if not existing:
            raise EntityNotFoundException("ReferralCase", referral_id)

        # Assignment verification
        if actor.actor_role == "counselor" and existing["assigned_counselor_id"] != actor.actor_id:
            raise UnauthorizedAccessException("You are not assigned to this referral case.")

        note_id = f"note_{uuid.uuid4().hex[:10]}"
        now = datetime.now(timezone.utc).isoformat()
        counselor_id = data.counselor_id or actor.actor_id

        conn.execute("""
            INSERT INTO counselor_notes (id, referral_case_id, counselor_id, note, created_at)
            VALUES (?, ?, ?, ?, ?);
        """, (note_id, referral_id, counselor_id, data.note, now))

        log_audit_event(
            conn=conn,
            actor_id=actor.actor_id,
            actor_name=actor.actor_name,
            actor_role=actor.actor_role,
            action="COUNSELOR_NOTE_ADDED",
            entity_type="counselor_note",
            entity_id=note_id,
            metadata={"referral_case_id": referral_id}
        )

        row = conn.execute("SELECT * FROM counselor_notes WHERE id = ?;", (note_id,)).fetchone()
        return dict(row)
