import uuid
import json
from datetime import datetime, timezone
from sqlite3 import Connection
from typing import Optional, List, Dict, Any
from app.utils.audit_events import log_audit_event

class CaseManagementService:
    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def get_or_create_case(
        conn: Connection,
        beneficiary_id: str,
        district_id: str,
        block_id: Optional[str] = None,
        intake_source: str = "WEB",
        assigned_worker_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Retrieves existing open operational case for beneficiary or creates one atomically.
        """
        row = conn.execute("""
            SELECT * FROM beneficiary_cases
            WHERE beneficiary_id = ? AND case_status NOT IN ('COMPLETED', 'CLOSED')
            ORDER BY created_at DESC LIMIT 1;
        """, (beneficiary_id,)).fetchone()

        if row:
            return dict(row)

        case_id = f"case_{uuid.uuid4().hex[:10]}"
        now = CaseManagementService._now()

        conn.execute("""
            INSERT INTO beneficiary_cases (
                id, beneficiary_id, district_id, block_id, assigned_worker_id,
                case_status, priority, intake_source, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, 'NEW', 'NORMAL', ?, ?, ?);
        """, (case_id, beneficiary_id, district_id, block_id, assigned_worker_id, intake_source, now, now))

        if assigned_worker_id:
            assign_id = f"cassign_{uuid.uuid4().hex[:10]}"
            conn.execute("""
                INSERT INTO case_assignments (
                    id, case_id, worker_id, assigned_by_user_id, assignment_reason, assigned_at
                ) VALUES (?, ?, ?, ?, 'Initial intake assignment', ?);
            """, (assign_id, case_id, assigned_worker_id, assigned_worker_id, now))

        log_audit_event(
            conn=conn,
            actor_id=assigned_worker_id or "system",
            actor_name="System",
            actor_role="system",
            action="case.created",
            entity_type="beneficiary_case",
            entity_id=case_id,
            metadata={"beneficiary_id": beneficiary_id, "district_id": district_id}
        )

        created = conn.execute("SELECT * FROM beneficiary_cases WHERE id = ?", (case_id,)).fetchone()
        return dict(created)

    @staticmethod
    def get_case(conn: Connection, case_id: str) -> Optional[Dict[str, Any]]:
        row = conn.execute("SELECT * FROM beneficiary_cases WHERE id = ?", (case_id,)).fetchone()
        return dict(row) if row else None

    @staticmethod
    def list_cases(
        conn: Connection,
        actor,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        assigned_to_me: bool = False,
        district_id: Optional[str] = None,
        block_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        query = "SELECT * FROM beneficiary_cases WHERE 1=1"
        params = []

        # Scope enforcement
        if not ("super_admin" in actor.roles or "admin" in actor.roles):
            # Worker or auditor scope
            if actor.scopes:
                scoped_dists = [s.get("district_id") for s in actor.scopes if s.get("district_id")]
                if scoped_dists:
                    placeholders = ",".join("?" for _ in scoped_dists)
                    query += f" AND district_id IN ({placeholders})"
                    params.extend(scoped_dists)
            else:
                return []

        if assigned_to_me:
            query += " AND assigned_worker_id = ?"
            params.append(actor.actor_id)

        if status:
            query += " AND case_status = ?"
            params.append(status.upper())

        if priority:
            query += " AND priority = ?"
            params.append(priority.upper())

        if district_id:
            query += " AND LOWER(district_id) = LOWER(?)"
            params.append(district_id)

        if block_id:
            query += " AND LOWER(block_id) = LOWER(?)"
            params.append(block_id)

        query += " ORDER BY updated_at DESC LIMIT ? OFFSET ?;"
        params.extend([limit, offset])

        rows = conn.execute(query, tuple(params)).fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def assign_case(
        conn: Connection,
        case_id: str,
        worker_id: str,
        assigned_by_user_id: str,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        now = CaseManagementService._now()
        assign_id = f"cassign_{uuid.uuid4().hex[:10]}"

        # Close prior open assignment if any
        conn.execute("""
            UPDATE case_assignments
            SET unassigned_at = ?
            WHERE case_id = ? AND unassigned_at IS NULL;
        """, (now, case_id))

        conn.execute("""
            INSERT INTO case_assignments (
                id, case_id, worker_id, assigned_by_user_id, assignment_reason, assigned_at
            ) VALUES (?, ?, ?, ?, ?, ?);
        """, (assign_id, case_id, worker_id, assigned_by_user_id, reason, now))

        conn.execute("""
            UPDATE beneficiary_cases
            SET assigned_worker_id = ?, updated_at = ?
            WHERE id = ?;
        """, (worker_id, now, case_id))

        log_audit_event(
            conn=conn,
            actor_id=assigned_by_user_id,
            actor_name="Staff",
            actor_role="staff",
            action="case.assigned",
            entity_type="beneficiary_case",
            entity_id=case_id,
            metadata={"assigned_worker_id": worker_id, "reason": reason}
        )

        return CaseManagementService.get_case(conn, case_id)

    @staticmethod
    def add_note(
        conn: Connection,
        case_id: str,
        author_user_id: str,
        note_text: str,
        note_type: str = "GENERAL",
        visibility: str = "STAFF_ONLY"
    ) -> Dict[str, Any]:
        now = CaseManagementService._now()
        note_id = f"cnote_{uuid.uuid4().hex[:10]}"

        conn.execute("""
            INSERT INTO case_notes (
                id, case_id, author_user_id, note_text, note_type, visibility, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """, (note_id, case_id, author_user_id, note_text, note_type.upper(), visibility.upper(), now, now))

        conn.execute("UPDATE beneficiary_cases SET updated_at = ? WHERE id = ?;", (now, case_id))

        log_audit_event(
            conn=conn,
            actor_id=author_user_id,
            actor_name="Staff",
            actor_role="staff",
            action="case.note_added",
            entity_type="beneficiary_case",
            entity_id=case_id,
            metadata={"note_id": note_id, "note_type": note_type, "visibility": visibility}
        )

        row = conn.execute("SELECT * FROM case_notes WHERE id = ?", (note_id,)).fetchone()
        return dict(row)

    @staticmethod
    def get_notes(conn: Connection, case_id: str, include_staff_only: bool = False) -> List[Dict[str, Any]]:
        if include_staff_only:
            rows = conn.execute("SELECT * FROM case_notes WHERE case_id = ? ORDER BY created_at ASC;", (case_id,)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM case_notes WHERE case_id = ? AND visibility = 'BENEFICIARY_SAFE' ORDER BY created_at ASC;", (case_id,)).fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def schedule_follow_up(
        conn: Connection,
        case_id: str,
        next_follow_up_at: str,
        actor_user_id: str,
        note: Optional[str] = None
    ) -> Dict[str, Any]:
        now = CaseManagementService._now()
        conn.execute("""
            UPDATE beneficiary_cases
            SET next_follow_up_at = ?, updated_at = ?
            WHERE id = ?;
        """, (next_follow_up_at, now, case_id))

        if note:
            CaseManagementService.add_note(
                conn, case_id, actor_user_id,
                f"Follow-up scheduled for {next_follow_up_at}. Note: {note}",
                note_type="CONTACT_ATTEMPT",
                visibility="STAFF_ONLY"
            )

        log_audit_event(
            conn=conn,
            actor_id=actor_user_id,
            actor_name="Staff",
            actor_role="staff",
            action="case.priority_changed",
            entity_type="beneficiary_case",
            entity_id=case_id,
            metadata={"next_follow_up_at": next_follow_up_at}
        )

        return CaseManagementService.get_case(conn, case_id)
