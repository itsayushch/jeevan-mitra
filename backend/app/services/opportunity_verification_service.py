from sqlite3 import Connection
from pathlib import Path
import uuid
import json
from datetime import datetime, timezone
from typing import Optional, Dict

from app.services.opportunity_service import OpportunityService
from app.utils.audit_events import log_audit_event

class OpportunityVerificationService:
    @staticmethod
    def _now():
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def submit_evidence(conn: Connection, opp_id: str, data: Dict, user_id: str) -> Dict:
        opp = OpportunityService.get_opportunity(conn, opp_id)
        if not opp:
            raise ValueError("Opportunity not found")

        valid_types = {'FIELD_VISIT', 'DOCUMENT', 'PHONE_VERIFICATION', 'THIRD_PARTY'}
        ev_type = data.get('evidence_type', '').upper()
        if ev_type not in valid_types:
            raise ValueError(f"Invalid evidence_type. Must be one of {valid_types}")

        storage_key = data.get('storage_key')
        if storage_key:
            if ".." in storage_key or storage_key.startswith("/") or "\\" in storage_key:
                raise ValueError("Invalid storage_key: path traversal sequences are forbidden.")
            disallowed_exts = {".exe", ".sh", ".bat", ".cmd", ".php", ".py", ".pl", ".dll", ".so", ".bin", ".js", ".vbs"}
            ext = Path(storage_key).suffix.lower()
            if ext in disallowed_exts:
                raise ValueError(f"Invalid file extension: '{ext}' is prohibited for evidence upload.")

        evidence_id = f"ev_{uuid.uuid4().hex[:8]}"
        now = OpportunityVerificationService._now()
        
        is_approved = 1 if data.get('is_approved', False) else 0
        
        conn.execute("""
            INSERT INTO opportunity_evidence (
                id, opportunity_id, evidence_type, storage_key, external_url,
                note, submitted_by_user_id, created_at, is_approved
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            evidence_id, opp_id, ev_type, data.get('storage_key'),
            data.get('external_url'), data.get('note'), user_id, now, is_approved
        ))
        
        log_audit_event(
            conn=conn,
            actor_id=user_id,
            actor_name="Field Worker",
            actor_role="field_worker",
            action="OPPORTUNITY_EVIDENCE_ATTACHED",
            entity_type="opportunity_evidence",
            entity_id=evidence_id,
            new_values={"opportunity_id": opp_id, "evidence_type": ev_type, "is_approved": is_approved}
        )

        return dict(conn.execute("SELECT * FROM opportunity_evidence WHERE id = ?", (evidence_id,)).fetchone())

    @staticmethod
    def record_event(conn: Connection, opp_id: str, actor_id: str, prev: str, new_status: str, action: str, expires_at: Optional[str] = None, reason: Optional[str] = None):
        event_id = f"ver_ev_{uuid.uuid4().hex[:8]}"
        now = OpportunityVerificationService._now()
        conn.execute("""
            INSERT INTO opportunity_verification_events (
                id, opportunity_id, actor_user_id, previous_status, new_status,
                verification_action, reason, verification_expires_at, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            event_id, opp_id, actor_id, prev, new_status, action, reason, expires_at, now
        ))
        return event_id

    @staticmethod
    def transition_status(conn: Connection, opp_id: str, action: str, user_id: str, expires_at: Optional[str] = None, reason: Optional[str] = None):
        opp = OpportunityService.get_opportunity(conn, opp_id)
        if not opp:
            raise ValueError("Opportunity not found")
        
        prev = opp['status']
        new_status = prev
        verified_at = None
        now_dt = datetime.now(timezone.utc)
        
        if action == 'SUBMITTED':
            if prev != 'DRAFT':
                raise ValueError(f"Cannot submit opportunity from status {prev}. Must be DRAFT.")
            new_status = 'PENDING_VERIFICATION'

        elif action in ('VERIFIED', 'REVERIFIED'):
            # 1. Require at least one approved evidence record
            ev_count = conn.execute(
                "SELECT COUNT(*) FROM opportunity_evidence WHERE opportunity_id = ? AND is_approved = 1",
                (opp_id,)
            ).fetchone()[0]
            if ev_count == 0:
                raise ValueError("Cannot verify opportunity without approved evidence.")

            # 2. Expiry must be specified and strictly in the future
            if not expires_at:
                raise ValueError("Expires at is required for verification.")
            try:
                exp_dt = datetime.fromisoformat(str(expires_at).replace("Z", "+00:00"))
                if exp_dt <= now_dt:
                    raise ValueError("Verification expiry date must be in the future.")
            except Exception as e:
                if "future" in str(e):
                    raise
                raise ValueError("Invalid verification_expires_at format.")

            # 3. Capacity check: seats_available must be > 0
            seats = opp.get('seats_available')
            vacancies = opp.get('vacancies_available')
            if (seats is not None and seats <= 0) and (vacancies is not None and vacancies <= 0):
                raise ValueError("Cannot verify opportunity with zero seats available.")

            new_status = 'ACTIVE'
            verified_at = OpportunityVerificationService._now()

        elif action == 'MARKED_FULL':
            new_status = 'FULL'
            conn.execute("UPDATE local_opportunities SET seats_available = 0 WHERE id = ?", (opp_id,))

        elif action == 'REJECTED':
            if prev != 'PENDING_VERIFICATION':
                raise ValueError(f"Cannot reject opportunity from status {prev}.")
            new_status = 'DRAFT'

        elif action == 'PAUSED':
            new_status = 'PAUSED'

        elif action == 'CLOSED':
            new_status = 'CLOSED'

        elif action == 'EXPIRED':
            new_status = 'EXPIRED'

        else:
            raise ValueError(f"Invalid transition from {prev} with action {action}")

        OpportunityService.update_opportunity_status(
            conn, opp_id, new_status, user_id, verified_at=verified_at, verification_expires_at=expires_at
        )
        
        OpportunityVerificationService.record_event(
            conn, opp_id, user_id, prev, new_status, action, expires_at, reason
        )

        # Log audit event for state transition
        audit_action_map = {
            'VERIFIED': 'OPPORTUNITY_VERIFIED',
            'REVERIFIED': 'OPPORTUNITY_REVERIFIED',
            'SUBMITTED': 'OPPORTUNITY_SUBMITTED',
            'MARKED_FULL': 'OPPORTUNITY_MARKED_FULL',
            'REJECTED': 'OPPORTUNITY_REJECTED',
            'PAUSED': 'OPPORTUNITY_PAUSED',
            'CLOSED': 'OPPORTUNITY_CLOSED',
            'EXPIRED': 'OPPORTUNITY_EXPIRED'
        }
        log_audit_event(
            conn=conn,
            actor_id=user_id,
            actor_name="Verification Workflow",
            actor_role="field_worker" if not user_id.startswith("sys_") else "system",
            action=audit_action_map.get(action, f"OPPORTUNITY_{action}"),
            entity_type="local_opportunity",
            entity_id=opp_id,
            old_values={"status": prev},
            new_values={"status": new_status, "verification_action": action, "expires_at": expires_at}
        )

        # Recalculate match state for any recommendation match state referencing this opportunity
        from app.services.match_state_service import MatchStateService
        recs = conn.execute(
            "SELECT beneficiary_id, qualification_id FROM recommendation_match_state WHERE local_opportunity_id = ?",
            (opp_id,)
        ).fetchall()
        for r in recs:
            MatchStateService.recalculate_match(conn, r['beneficiary_id'], r['qualification_id'], opp_id)

        return OpportunityService.get_opportunity(conn, opp_id, include_staff_details=True)
