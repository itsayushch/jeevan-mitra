from sqlite3 import Connection
import uuid
import json
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

class OpportunityService:
    @staticmethod
    def _now():
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def create_provider(conn: Connection, data: Dict, user_id: str) -> Dict:
        provider_id = f"prov_{uuid.uuid4().hex[:8]}"
        now = OpportunityService._now()
        
        conn.execute("""
            INSERT INTO opportunity_providers (
                id, provider_type, name, contact_name, contact_phone, contact_email,
                address_line, district_id, block_id, pincode, latitude, longitude,
                status, source_name, source_reference, created_by_user_id, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            provider_id, data['provider_type'], data['name'], data.get('contact_name'),
            data.get('contact_phone'), data.get('contact_email'), data.get('address_line'),
            data.get('district_id'), data.get('block_id'), data.get('pincode'),
            data.get('latitude'), data.get('longitude'), data.get('status', 'ACTIVE'),
            data.get('source_name'), data.get('source_reference'), user_id, now, now
        ))
        
        return dict(conn.execute("SELECT * FROM opportunity_providers WHERE id = ?", (provider_id,)).fetchone())

    @staticmethod
    def create_opportunity(conn: Connection, data: Dict, user_id: str) -> Dict:
        opp_id = f"opp_{uuid.uuid4().hex[:8]}"
        now = OpportunityService._now()
        
        conn.execute("""
            INSERT INTO local_opportunities (
                id, qualification_id, provider_id, opportunity_type, title, summary,
                district_id, block_id, location_text, delivery_mode, start_date, end_date,
                application_deadline, seats_total, seats_available, vacancies_total,
                vacancies_available, stipend_amount, fee_amount, travel_support_available,
                hostel_available, eligibility_notes, accessibility_notes, evidence_summary,
                source_url, status, created_by_user_id, updated_by_user_id, created_at, updated_at
            ) VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
        """, (
            opp_id, data['qualification_id'], data['provider_id'], data['opportunity_type'],
            data['title'], data['summary'], data['district_id'], data.get('block_id'),
            data.get('location_text'), data['delivery_mode'], data.get('start_date'),
            data.get('end_date'), data.get('application_deadline'), data.get('seats_total'),
            data.get('seats_available'), data.get('vacancies_total'), data.get('vacancies_available'),
            data.get('stipend_amount'), data.get('fee_amount'), data.get('travel_support_available', 0),
            data.get('hostel_available', 0), data.get('eligibility_notes'), data.get('accessibility_notes'),
            None, data.get('source_url'), 'DRAFT', user_id, user_id, now, now
        ))
        
        return OpportunityService.get_opportunity(conn, opp_id)

    @staticmethod
    def get_opportunity(conn: Connection, opp_id: str) -> Optional[Dict]:
        row = conn.execute("SELECT * FROM local_opportunities WHERE id = ?", (opp_id,)).fetchone()
        return dict(row) if row else None

    @staticmethod
    def update_opportunity_status(conn: Connection, opp_id: str, new_status: str, user_id: str, verified_at: Optional[str] = None, verification_expires_at: Optional[str] = None):
        now = OpportunityService._now()
        updates = ["status = ?", "updated_by_user_id = ?", "updated_at = ?"]
        params = [new_status, user_id, now]
        
        if verified_at:
            updates.append("verified_at = ?")
            updates.append("verified_by_user_id = ?")
            params.extend([verified_at, user_id])
            
        if verification_expires_at:
            updates.append("verification_expires_at = ?")
            params.append(verification_expires_at)
            
        params.append(opp_id)
        
        query = f"UPDATE local_opportunities SET {', '.join(updates)} WHERE id = ?"
        conn.execute(query, tuple(params))
