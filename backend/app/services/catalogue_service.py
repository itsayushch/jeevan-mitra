import uuid
import json
import sqlite3
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from app.models import QualificationCreate, QualificationUpdate, OpportunityCreate, OpportunityUpdate
from app.utils.audit_events import log_audit_event
from app.utils.errors import EntityNotFoundException, ValidationException

class CatalogueService:
    STALE_DATA_THRESHOLD_DAYS = 90

    @staticmethod
    def _is_stale(verified_at_str: Optional[str]) -> bool:
        if not verified_at_str:
            return True
        try:
            # Handle YYYY-MM-DD or ISO strings
            if len(verified_at_str) == 10:
                v_date = datetime.strptime(verified_at_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            else:
                v_date = datetime.fromisoformat(verified_at_str.replace("Z", "+00:00"))
            return (datetime.now(timezone.utc) - v_date) > timedelta(days=CatalogueService.STALE_DATA_THRESHOLD_DAYS)
        except Exception:
            return True

    @staticmethod
    def list_qualifications(conn: sqlite3.Connection, sector: Optional[str] = None) -> List[Dict[str, Any]]:
        query = "SELECT * FROM qualifications WHERE verification_status = 'verified'"
        params = []
        if sector:
            query += " AND sector = ?"
            params.append(sector)
        query += " ORDER BY nsqf_level ASC;"

        rows = conn.execute(query, params).fetchall()
        results = []
        for r in rows:
            d = dict(r)
            d["skills_acquired"] = json.loads(d.get("skills_acquired") or "[]")
            d["official_source_url"] = d.get("official_source_url") or d.get("nqr_link")
            d["last_verified_at"] = d.get("last_verified_at") or d.get("verification_date")
            results.append(d)
        return results

    @staticmethod
    def get_qualification_detail(conn: sqlite3.Connection, qual_id: str) -> Dict[str, Any]:
        row = conn.execute("SELECT * FROM qualifications WHERE id = ? OR nqr_code = ?;", (qual_id, qual_id)).fetchone()
        if not row:
            raise EntityNotFoundException("Qualification", qual_id)

        qual = dict(row)
        qual["skills_acquired"] = json.loads(qual.get("skills_acquired") or "[]")
        qual["official_source_url"] = qual.get("official_source_url") or qual.get("nqr_link")

        # Fetch linked non-archived opportunities
        opp_rows = conn.execute("""
            SELECT * FROM local_opportunities
            WHERE qualification_id = ? AND is_archived = 0;
        """, (qual["id"],)).fetchall()

        opps = []
        for o in opp_rows:
            od = dict(o)
            # Apply stale-data rule
            if CatalogueService._is_stale(od.get("verified_at")):
                od["availability"] = "unknown"
            opps.append(od)

        return {
            "qualification": qual,
            "activeBatches": opps
        }

    @staticmethod
    def list_opportunities(
        conn: sqlite3.Connection,
        district: Optional[str] = None,
        block: Optional[str] = None,
        qualification_id: Optional[str] = None,
        include_archived: bool = False
    ) -> List[Dict[str, Any]]:
        query = "SELECT * FROM local_opportunities WHERE 1=1"
        params = []
        if not include_archived:
            query += " AND is_archived = 0"
        if district:
            query += " AND LOWER(district) = LOWER(?)"
            params.append(district)
        if block:
            query += " AND LOWER(block) = LOWER(?)"
            params.append(block)
        if qualification_id:
            query += " AND qualification_id = ?"
            params.append(qualification_id)

        query += " ORDER BY batch_start_date ASC;"
        rows = conn.execute(query, params).fetchall()

        results = []
        for r in rows:
            d = dict(r)
            # Apply stale-data rule
            if CatalogueService._is_stale(d.get("verified_at")):
                d["availability"] = "unknown"
            results.append(d)
        return results

    @staticmethod
    def create_qualification(conn: sqlite3.Connection, data: QualificationCreate, actor_id: str = "admin") -> Dict[str, Any]:
        qual_id = f"qual_{uuid.uuid4().hex[:10]}"
        now = datetime.now(timezone.utc).isoformat()
        v_date = data.verification_date or now[:10]

        conn.execute("""
            INSERT INTO qualifications (
                id, nqr_code, title, sector, nsqf_level, duration_hours,
                min_education, min_education_rank, work_type, physical_intensity,
                skills_acquired, curriculum_summary, entry_criteria, certification_body,
                nqr_link, official_source_url, verification_status, verification_date, last_verified_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            qual_id, data.nqr_code, data.title, data.sector, data.nsqf_level, data.duration_hours,
            data.min_education, data.min_education_rank, data.work_type, data.physical_intensity,
            json.dumps(data.skills_acquired), data.curriculum_summary, data.entry_criteria,
            data.certification_body, data.official_source_url, data.official_source_url,
            data.verification_status or "verified", v_date, now
        ))

        log_audit_event(
            conn=conn,
            actor_id=actor_id,
            actor_name="Catalog Admin",
            actor_role="admin",
            action="QUALIFICATION_CREATED",
            entity_type="qualification",
            entity_id=qual_id,
            new_values=data.model_dump()
        )

        return CatalogueService.get_qualification_detail(conn, qual_id)["qualification"]

    @staticmethod
    def update_qualification(conn: sqlite3.Connection, qual_id: str, updates: QualificationUpdate, actor_id: str = "admin") -> Dict[str, Any]:
        existing = conn.execute("SELECT * FROM qualifications WHERE id = ?;", (qual_id,)).fetchone()
        if not existing:
            raise EntityNotFoundException("Qualification", qual_id)

        update_dict = updates.model_dump(exclude_unset=True)
        if "skills_acquired" in update_dict and isinstance(update_dict["skills_acquired"], list):
            update_dict["skills_acquired"] = json.dumps(update_dict["skills_acquired"])
        if "official_source_url" in update_dict:
            update_dict["nqr_link"] = update_dict["official_source_url"]

        update_dict["last_verified_at"] = datetime.now(timezone.utc).isoformat()

        set_clauses = [f"{k} = ?" for k in update_dict.keys()]
        params = list(update_dict.values()) + [qual_id]

        conn.execute(f"UPDATE qualifications SET {', '.join(set_clauses)} WHERE id = ?;", params)

        log_audit_event(
            conn=conn,
            actor_id=actor_id,
            actor_name="Catalog Admin",
            actor_role="admin",
            action="QUALIFICATION_UPDATED",
            entity_type="qualification",
            entity_id=qual_id,
            old_values=dict(existing),
            new_values=update_dict
        )

        return CatalogueService.get_qualification_detail(conn, qual_id)["qualification"]

    @staticmethod
    def create_opportunity(conn: sqlite3.Connection, data: OpportunityCreate, actor_id: str = "admin") -> Dict[str, Any]:
        # Validate linked qualification exists
        qual = conn.execute("SELECT id FROM qualifications WHERE id = ?;", (data.qualification_id,)).fetchone()
        if not qual:
            raise ValidationException(f"Linked qualification '{data.qualification_id}' does not exist.")

        opp_id = f"opp_{uuid.uuid4().hex[:10]}"
        now = datetime.now(timezone.utc).isoformat()

        conn.execute("""
            INSERT INTO local_opportunities (
                id, qualification_id, centre_or_employer_name, type, district, block, state,
                address, latitude, longitude, batch_start_date, batch_end_date,
                total_seats, available_seats, sc_reserved_seats, batch_status, availability,
                hostel_available, stipend_amount_inr, free_toolkit_provided, source, source_url,
                contact_details, is_archived, verified_by_worker_id, verified_at, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            opp_id, data.qualification_id, data.centre_or_employer_name, data.type,
            data.district, data.block, data.state or "Uttar Pradesh", data.address,
            data.latitude, data.longitude, data.batch_start_date, data.batch_end_date,
            data.total_seats, data.available_seats, data.sc_reserved_seats,
            data.batch_status, data.availability or "verified_open",
            1 if data.hostel_available else 0, data.stipend_amount_inr,
            1 if data.free_toolkit_provided else 0, "pm_ajay_portal",
            data.source_url, data.contact_details, 0, actor_id, now, now
        ))

        log_audit_event(
            conn=conn,
            actor_id=actor_id,
            actor_name="Catalog Admin",
            actor_role="admin",
            action="LOCAL_OPPORTUNITY_CREATED",
            entity_type="local_opportunity",
            entity_id=opp_id,
            new_values=data.model_dump()
        )

        row = conn.execute("SELECT * FROM local_opportunities WHERE id = ?;", (opp_id,)).fetchone()
        return dict(row)

    @staticmethod
    def update_opportunity(conn: sqlite3.Connection, opp_id: str, updates: OpportunityUpdate, actor_id: str = "admin") -> Dict[str, Any]:
        existing = conn.execute("SELECT * FROM local_opportunities WHERE id = ?;", (opp_id,)).fetchone()
        if not existing:
            raise EntityNotFoundException("LocalOpportunity", opp_id)

        update_dict = updates.model_dump(exclude_unset=True)
        if "hostel_available" in update_dict:
            update_dict["hostel_available"] = 1 if update_dict["hostel_available"] else 0
        if "free_toolkit_provided" in update_dict:
            update_dict["free_toolkit_provided"] = 1 if update_dict["free_toolkit_provided"] else 0

        update_dict["verified_at"] = datetime.now(timezone.utc).isoformat()
        update_dict["verified_by_worker_id"] = actor_id

        set_clauses = [f"{k} = ?" for k in update_dict.keys()]
        params = list(update_dict.values()) + [opp_id]

        conn.execute(f"UPDATE local_opportunities SET {', '.join(set_clauses)} WHERE id = ?;", params)

        log_audit_event(
            conn=conn,
            actor_id=actor_id,
            actor_name="Catalog Admin",
            actor_role="admin",
            action="LOCAL_OPPORTUNITY_UPDATED",
            entity_type="local_opportunity",
            entity_id=opp_id,
            old_values=dict(existing),
            new_values=update_dict
        )

        row = conn.execute("SELECT * FROM local_opportunities WHERE id = ?;", (opp_id,)).fetchone()
        return dict(row)

    @staticmethod
    def archive_opportunity(conn: sqlite3.Connection, opp_id: str, actor_id: str = "admin") -> Dict[str, Any]:
        existing = conn.execute("SELECT * FROM local_opportunities WHERE id = ?;", (opp_id,)).fetchone()
        if not existing:
            raise EntityNotFoundException("LocalOpportunity", opp_id)

        conn.execute("""
            UPDATE local_opportunities
            SET is_archived = 1, availability = 'closed'
            WHERE id = ?;
        """, (opp_id,))

        log_audit_event(
            conn=conn,
            actor_id=actor_id,
            actor_name="Catalog Admin",
            actor_role="admin",
            action="LOCAL_OPPORTUNITY_ARCHIVED",
            entity_type="local_opportunity",
            entity_id=opp_id,
            new_values={"is_archived": 1, "availability": "closed"}
        )

        return {"status": "archived", "opportunity_id": opp_id}
