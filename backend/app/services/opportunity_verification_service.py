from sqlite3 import Connection
import uuid
import json
from datetime import datetime, timezone
from typing import Optional, Dict

from app.services.opportunity_service import OpportunityService

class OpportunityVerificationService:
    @staticmethod
    def _now():
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def submit_evidence(conn: Connection, opp_id: str, data: Dict, user_id: str) -> Dict:
        evidence_id = f"ev_{uuid.uuid4().hex[:8]}"
        now = OpportunityVerificationService._now()
        
        # Determine if it's auto-approved (e.g. if super_admin or based on policy, assuming false for now)
        is_approved = 1 if data.get('is_approved', False) else 0
        
        conn.execute("""
            INSERT INTO opportunity_evidence (
                id, opportunity_id, evidence_type, storage_key, external_url,
                note, submitted_by_user_id, created_at, is_approved
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            evidence_id, opp_id, data['evidence_type'], data.get('storage_key'),
            data.get('external_url'), data.get('note'), user_id, now, is_approved
        ))
        
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

    @staticmethod
    def transition_status(conn: Connection, opp_id: str, action: str, user_id: str, expires_at: Optional[str] = None, reason: Optional[str] = None):
        opp = OpportunityService.get_opportunity(conn, opp_id)
        if not opp:
            raise ValueError("Opportunity not found")
        
        prev = opp['status']
        new_status = prev
        verified_at = None
        
        if action == 'SUBMITTED' and prev == 'DRAFT':
            new_status = 'PENDING_VERIFICATION'
        elif action == 'VERIFIED' and prev in ['PENDING_VERIFICATION', 'DRAFT', 'PAUSED', 'EXPIRED']:
            # Require at least one approved evidence or a super admin override? 
            # We'll trust the route handler validates roles.
            new_status = 'ACTIVE'
            verified_at = OpportunityVerificationService._now()
            if not expires_at:
                raise ValueError("Expires at is required for verification")
        elif action == 'REJECTED' and prev == 'PENDING_VERIFICATION':
            new_status = 'DRAFT'
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
        return OpportunityService.get_opportunity(conn, opp_id)
