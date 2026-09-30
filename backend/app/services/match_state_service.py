from sqlite3 import Connection
import uuid
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any

class MatchStateService:
    @staticmethod
    def _now():
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def recalculate_match(conn: Connection, beneficiary_id: str, qual_id: str, opp_id: Optional[str] = None):
        # 1. Determine match state.
        match_state = 'INTEREST_MATCH'
        now_dt = datetime.now(timezone.utc)
        
        if opp_id:
            opp = conn.execute(
                "SELECT status, verification_expires_at, seats_available, vacancies_available FROM local_opportunities WHERE id = ?",
                (opp_id,)
            ).fetchone()
            if opp:
                status = opp['status']
                expires_at_str = opp['verification_expires_at']
                seats = opp['seats_available'] if opp['seats_available'] is not None else 1
                vacancies = opp['vacancies_available'] if opp['vacancies_available'] is not None else 1
                
                # Evaluate expiry
                is_expired = False
                if expires_at_str:
                    try:
                        expires_at = datetime.fromisoformat(str(expires_at_str).replace("Z", "+00:00"))
                        if expires_at <= now_dt:
                            is_expired = True
                    except Exception:
                        is_expired = True

                has_capacity = (seats > 0) or (vacancies > 0)

                if status == 'ACTIVE' and not is_expired and has_capacity:
                    match_state = 'VERIFIED_MATCH'
                else:
                    match_state = 'INTEREST_MATCH'
        
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

    @staticmethod
    def get_or_compute_match(
        conn: Connection,
        beneficiary_id: str,
        qual_id: Optional[str] = None,
        district_id: Optional[str] = None,
        block_id: Optional[str] = None,
        qualification_id: Optional[str] = None
    ) -> Dict[str, Any]:
        qual_id = qual_id or qualification_id
        now_dt = datetime.now(timezone.utc)
        now_str = now_dt.isoformat()

        # Find active, non-expired opportunity with available capacity for this qualification
        query = """
            SELECT * FROM local_opportunities
            WHERE qualification_id = ?
              AND status = 'ACTIVE'
              AND (verification_expires_at IS NULL OR verification_expires_at > ?)
              AND (seats_available > 0 OR vacancies_available > 0)
        """
        params = [qual_id, now_str]

        if district_id:
            query += " AND (LOWER(district_id) = LOWER(?) OR LOWER(district) = LOWER(?))"
            params.extend([district_id, district_id])
        if block_id:
            query += " AND (LOWER(block_id) = LOWER(?) OR LOWER(block) = LOWER(?))"
            params.extend([block_id, block_id])

        query += " ORDER BY seats_available DESC LIMIT 1"
        opp = conn.execute(query, tuple(params)).fetchone()

        if opp:
            opp_d = dict(opp)
            MatchStateService.recalculate_match(conn, beneficiary_id, qual_id, opp_d['id'])
            verified_at = opp_d.get('verified_at')
            ver_dt = datetime.fromisoformat(str(verified_at).replace("Z", "+00:00")) if verified_at else None
            return {
                "matchState": "VERIFIED_MATCH",
                "beneficiaryMessage": f"Verified local batch available in {opp_d.get('district_id')}. Seats available: {opp_d.get('seats_available')}.",
                "canRequestReferral": True,
                "canRequestWorkerSupport": True,
                "verificationUpdatedAt": ver_dt,
                "opportunity": {
                    "id": opp_d['id'],
                    "title": opp_d['title'],
                    "summary": opp_d['summary'],
                    "district_id": opp_d['district_id'],
                    "seats_available": opp_d.get('seats_available'),
                    "delivery_mode": opp_d['delivery_mode'],
                    "status": opp_d['status']
                }
            }
        else:
            MatchStateService.recalculate_match(conn, beneficiary_id, qual_id, None)
            return {
                "matchState": "INTEREST_MATCH",
                "beneficiaryMessage": "National qualification pathway available within your mobility preference (local batch verification pending).",
                "canRequestReferral": False,
                "canRequestWorkerSupport": True,
                "verificationUpdatedAt": None,
                "opportunity": None
            }
