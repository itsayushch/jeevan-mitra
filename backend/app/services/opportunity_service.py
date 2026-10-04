from sqlite3 import Connection
import uuid
import json
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from app.utils.audit_events import log_audit_event

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
        
        provider = dict(conn.execute("SELECT * FROM opportunity_providers WHERE id = ?", (provider_id,)).fetchone())
        
        log_audit_event(
            conn=conn,
            actor_id=user_id,
            actor_name="Field Worker",
            actor_role="field_worker",
            action="OPPORTUNITY_PROVIDER_CREATED",
            entity_type="opportunity_provider",
            entity_id=provider_id,
            new_values={"name": data["name"], "district_id": data.get("district_id")}
        )
        return provider

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
        
        opp = OpportunityService.get_opportunity(conn, opp_id)
        
        log_audit_event(
            conn=conn,
            actor_id=user_id,
            actor_name="Field Worker",
            actor_role="field_worker",
            action="LOCAL_OPPORTUNITY_CREATED",
            entity_type="local_opportunity",
            entity_id=opp_id,
            new_values={"title": data["title"], "status": "DRAFT", "district_id": data["district_id"]}
        )
        return opp

    @staticmethod
    def get_opportunity(conn: Connection, opp_id: str, include_staff_details: bool = False) -> Optional[Dict]:
        row = conn.execute("SELECT * FROM local_opportunities WHERE id = ?", (opp_id,)).fetchone()
        if not row:
            return None
        d = dict(row)
        if include_staff_details:
            ev_rows = conn.execute("SELECT * FROM opportunity_evidence WHERE opportunity_id = ? ORDER BY created_at ASC", (opp_id,)).fetchall()
            d['evidence'] = [dict(r) for r in ev_rows]
            
            hist_rows = conn.execute("SELECT * FROM opportunity_verification_events WHERE opportunity_id = ? ORDER BY created_at ASC", (opp_id,)).fetchall()
            d['verification_history'] = [dict(r) for r in hist_rows]
        return d

    @staticmethod
    def update_opportunity_fields(conn: Connection, opp_id: str, data: Dict, user_id: str) -> Dict:
        existing = OpportunityService.get_opportunity(conn, opp_id)
        if not existing:
            raise ValueError("Opportunity not found")
        
        now = OpportunityService._now()
        updates = ["updated_by_user_id = ?", "updated_at = ?"]
        params = [user_id, now]
        
        seats_avail = data.get("seats_available")
        is_marking_full = False
        if seats_avail is not None:
            updates.append("seats_available = ?")
            params.append(seats_avail)
            # If seats set to zero, transition status to FULL
            if seats_avail == 0 and existing["status"] == "ACTIVE":
                updates.append("status = ?")
                params.append("FULL")
                is_marking_full = True

        for k in ["title", "summary", "seats_total", "vacancies_total", "vacancies_available", "location_text", "stipend_amount"]:
            if k in data and data[k] is not None:
                updates.append(f"{k} = ?")
                params.append(data[k])

        params.append(opp_id)
        conn.execute(f"UPDATE local_opportunities SET {', '.join(updates)} WHERE id = ?", tuple(params))

        if is_marking_full:
            # Record verification history event for marking full
            event_id = f"ver_ev_{uuid.uuid4().hex[:8]}"
            conn.execute("""
                INSERT INTO opportunity_verification_events (
                    id, opportunity_id, actor_user_id, previous_status, new_status,
                    verification_action, reason, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (event_id, opp_id, user_id, "ACTIVE", "FULL", "MARKED_FULL", "Capacity depleted (seats set to 0)", now))

            log_audit_event(
                conn=conn,
                actor_id=user_id,
                actor_name="Field Worker",
                actor_role="field_worker",
                action="OPPORTUNITY_MARKED_FULL",
                entity_type="local_opportunity",
                entity_id=opp_id,
                new_values={"status": "FULL", "seats_available": 0}
            )
            
            # Recalculate match state for linked records
            from app.services.match_state_service import MatchStateService
            recs = conn.execute("SELECT beneficiary_id, qualification_id FROM recommendation_match_state WHERE local_opportunity_id = ?", (opp_id,)).fetchall()
            for r in recs:
                MatchStateService.recalculate_match(conn, r["beneficiary_id"], r["qualification_id"], opp_id)
        else:
            log_audit_event(
                conn=conn,
                actor_id=user_id,
                actor_name="Field Worker",
                actor_role="field_worker",
                action="LOCAL_OPPORTUNITY_UPDATED",
                entity_type="local_opportunity",
                entity_id=opp_id,
                new_values=data
            )

        return OpportunityService.get_opportunity(conn, opp_id, include_staff_details=True)

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

        if new_status == "CLOSED":
            updates.append("closed_at = ?")
            params.append(now)
            
        params.append(opp_id)
        
        query = f"UPDATE local_opportunities SET {', '.join(updates)} WHERE id = ?"
        conn.execute(query, tuple(params))
