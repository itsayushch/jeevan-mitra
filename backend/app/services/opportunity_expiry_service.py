from sqlite3 import Connection
from datetime import datetime, timezone
import logging
from app.services.opportunity_verification_service import OpportunityVerificationService
from app.services.match_state_service import MatchStateService

logger = logging.getLogger(__name__)

class OpportunityExpiryService:
    @staticmethod
    def _now():
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def process_expiries(conn: Connection, dry_run: bool = False):
        now = OpportunityExpiryService._now()
        
        # Find ACTIVE opportunities where verification_expires_at <= now
        cursor = conn.execute("""
            SELECT id FROM local_opportunities
            WHERE status = 'ACTIVE' 
            AND verification_expires_at IS NOT NULL
            AND verification_expires_at <= ?
        """, (now,))
        
        expired_ids = [row['id'] for row in cursor.fetchall()]
        
        if dry_run:
            logger.info(f"[DRY RUN] Would expire {len(expired_ids)} opportunities: {expired_ids}")
            return expired_ids
            
        system_user_id = "sys_expiry_job"
        
        for opp_id in expired_ids:
            # Transition to EXPIRED
            OpportunityVerificationService.transition_status(
                conn, opp_id, "EXPIRED", system_user_id, reason="Scheduled expiry job"
            )
            
            # Find all recommendation matches attached to this opportunity and recalculate
            recs = conn.execute(
                "SELECT beneficiary_id, qualification_id FROM recommendation_match_state WHERE local_opportunity_id = ?",
                (opp_id,)
            ).fetchall()
            
            for rec in recs:
                MatchStateService.recalculate_match(
                    conn, rec['beneficiary_id'], rec['qualification_id'], opp_id
                )
                
        return expired_ids
