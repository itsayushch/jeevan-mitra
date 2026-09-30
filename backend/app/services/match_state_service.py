from sqlite3 import Connection
import uuid
import json
from datetime import datetime, timezone
from typing import Optional, Dict

class MatchStateService:
    @staticmethod
    def _now():
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def recalculate_match(conn: Connection, beneficiary_id: str, qual_id: str, opp_id: Optional[str] = None):
        # 1. Determine match state.
        match_state = 'INTEREST_MATCH'
        if opp_id:
            opp = conn.execute("SELECT status, verification_expires_at FROM local_opportunities WHERE id = ?", (opp_id,)).fetchone()
            if opp:
                status = opp['status']
                expires_at_str = opp['verification_expires_at']
                
                # Evaluate expiry
                is_expired = False
                if expires_at_str:
                    expires_at = datetime.fromisoformat(expires_at_str.replace("Z", "+00:00"))
                    if expires_at <= datetime.now(timezone.utc):
                        is_expired = True

                if status == 'ACTIVE' and not is_expired:
                    match_state = 'VERIFIED_MATCH'
                else:
                    # If it was attached but is now expired or closed, it degrades.
                    match_state = 'EXPIRED_MATCH'
        
        # 2. Upsert recommendation state
        row = conn.execute(
            "SELECT id FROM recommendation_match_state WHERE beneficiary_id = ? AND qualification_id = ?", 
            (beneficiary_id, qual_id)
        ).fetchone()

        now = MatchStateService._now()
        
        if row:
            rec_id = row['id']
            conn.execute("""
                UPDATE recommendation_match_state 
                SET local_opportunity_id = ?, match_state = ?, updated_at = ?
                WHERE id = ?
            """, (opp_id, match_state, now, rec_id))
        else:
            rec_id = f"rec_{uuid.uuid4().hex[:8]}"
            conn.execute("""
                INSERT INTO recommendation_match_state (
                    id, beneficiary_id, qualification_id, local_opportunity_id,
                    match_state, calculation_version, eligibility_snapshot_json,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                rec_id, beneficiary_id, qual_id, opp_id,
                match_state, 1, "{}", now, now
            ))
            
        return conn.execute("SELECT * FROM recommendation_match_state WHERE id = ?", (rec_id,)).fetchone()
