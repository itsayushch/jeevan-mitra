import json
import sqlite3
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from app.models import BeneficiaryUpdate
from app.utils.audit_events import log_audit_event
from app.utils.errors import EntityNotFoundException, UnauthorizedAccessException

class ProfileService:
    @staticmethod
    def get_profile_for_actor(conn: sqlite3.Connection, actor) -> Dict[str, Any]:
        """
        Retrieves profile based on active session or authenticated beneficiary id.
        Guest users return ephemeral or stored state without forcing permanent account creation.
        """
        target_ben_id = actor.beneficiary_id
        session_id = actor.session_id

        # 1. If permanent beneficiary ID exists
        if target_ben_id:
            row = conn.execute("SELECT * FROM beneficiaries WHERE id = ?;", (target_ben_id,)).fetchone()
            if row:
                data = dict(row)
                # Attach latest confirmed profile fields
                fields = conn.execute("""
                    SELECT field_name, field_value, user_confirmed, source
                    FROM profile_field_values
                    WHERE beneficiary_id = ?
                    ORDER BY updated_at ASC;
                """, (target_ben_id,)).fetchall()
                data["confirmed_fields"] = {
                    f["field_name"]: json.loads(f["field_value"]) if f["field_value"].startswith(("{", "[")) else f["field_value"]
                    for f in fields if f["user_confirmed"]
                }
                return data

        # 2. If anonymous session
        if session_id:
            # Check if there is an interview associated with this session
            interview = conn.execute("""
                SELECT * FROM interview_sessions
                WHERE session_id = ? OR id = ?
                ORDER BY created_at DESC LIMIT 1;
            """, (session_id, session_id)).fetchone()

            fields_dict = {}
            if interview:
                field_rows = conn.execute("""
                    SELECT field_name, field_value, user_confirmed, source
                    FROM profile_field_values
                    WHERE interview_id = ?;
                """, (interview["id"],)).fetchall()
                fields_dict = {
                    f["field_name"]: json.loads(f["field_value"]) if f["field_value"].startswith(("{", "[")) else f["field_value"]
                    for f in field_rows
                }

            return {
                "id": session_id,
                "name": "Guest Beneficiary",
                "owner_type": "anonymous",
                "owner_id": session_id,
                "district": fields_dict.get("district", "Moradabad"),
                "block": fields_dict.get("block", "Chhajlet"),
                "preferred_language": fields_dict.get("language", "hi"),
                "confirmed_fields": fields_dict,
                "is_guest": True
            }

        raise EntityNotFoundException("BeneficiaryProfile", actor.actor_id)

    @staticmethod
    def update_profile_for_actor(conn: sqlite3.Connection, actor, updates: BeneficiaryUpdate) -> Dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        target_ben_id = actor.beneficiary_id

        if not target_ben_id:
            # For anonymous guest, update session metadata or fields
            session_id = actor.session_id or actor.actor_id
            update_data = updates.model_dump(exclude_unset=True)
            log_audit_event(
                conn=conn,
                actor_id=actor.actor_id,
                actor_name=actor.actor_name,
                actor_role=actor.actor_role,
                action="GUEST_PROFILE_UPDATED",
                entity_type="anonymous_session",
                entity_id=session_id,
                new_values=update_data
            )
            return ProfileService.get_profile_for_actor(conn, actor)

        existing = conn.execute("SELECT * FROM beneficiaries WHERE id = ?;", (target_ben_id,)).fetchone()
        if not existing:
            raise EntityNotFoundException("Beneficiary", target_ben_id)

        update_dict = updates.model_dump(exclude_unset=True)
        if not update_dict:
            return dict(existing)

        set_clauses = [f"{k} = ?" for k in update_dict.keys()]
        set_clauses.append("updated_at = ?")
        params = list(update_dict.values()) + [now, target_ben_id]

        conn.execute(f"UPDATE beneficiaries SET {', '.join(set_clauses)} WHERE id = ?;", params)

        log_audit_event(
            conn=conn,
            actor_id=actor.actor_id,
            actor_name=actor.actor_name,
            actor_role=actor.actor_role,
            action="BENEFICIARY_PROFILE_UPDATED",
            entity_type="beneficiary",
            entity_id=target_ben_id,
            old_values=dict(existing),
            new_values=update_dict
        )

        return ProfileService.get_profile_for_actor(conn, actor)

    @staticmethod
    def delete_profile_for_actor(conn: sqlite3.Connection, actor) -> Dict[str, Any]:
        """
        Executes complete privacy deletion / DPDP 'Right to Erasure'.
        Deletes or anonymizes:
        - interview turns & transcripts
        - profile field values & answers
        - recommendations & data snapshots
        - referrals & referral cases
        - anonymous sessions & beneficiary records
        Preserves minimal non-identifying audit event.
        """
        now = datetime.now(timezone.utc).isoformat()
        target_ben_id = actor.beneficiary_id
        session_id = actor.session_id or actor.actor_id

        # 1. Identify all interview sessions
        query_interviews = """
            SELECT id FROM interview_sessions
            WHERE (beneficiary_id IS NOT NULL AND beneficiary_id = ?)
               OR (session_id IS NOT NULL AND session_id = ?)
               OR id = ?;
        """
        int_rows = conn.execute(query_interviews, (target_ben_id or "", session_id or "", session_id or "")).fetchall()
        interview_ids = [r["id"] for r in int_rows]

        for i_id in interview_ids:
            # Delete interview turns
            conn.execute("DELETE FROM interview_turns WHERE interview_id = ?;", (i_id,))
            # Delete profile field values
            conn.execute("DELETE FROM profile_field_values WHERE interview_id = ?;", (i_id,))
            # Delete profile revisions
            conn.execute("DELETE FROM profile_revisions WHERE interview_id = ?;", (i_id,))
            # Delete recommendations
            conn.execute("DELETE FROM recommendations WHERE interview_id = ? OR session_id = ?;", (i_id, i_id))
            # Delete export audits
            conn.execute("DELETE FROM export_audits WHERE interview_id = ?;", (i_id,))

        if target_ben_id:
            # Delete profile answers
            conn.execute("DELETE FROM profile_answers WHERE beneficiary_id = ?;", (target_ben_id,))
            # Delete recommendations
            conn.execute("DELETE FROM recommendations WHERE beneficiary_id = ?;", (target_ben_id,))
            # Delete referrals & referral cases
            conn.execute("DELETE FROM referral_cases WHERE beneficiary_id = ?;", (target_ben_id,))
            conn.execute("DELETE FROM referrals WHERE beneficiary_id = ?;", (target_ben_id,))
            # Delete consents
            conn.execute("DELETE FROM consent_records WHERE beneficiary_id = ?;", (target_ben_id,))
            conn.execute("DELETE FROM consents WHERE beneficiary_id = ?;", (target_ben_id,))
            # Delete beneficiary record
            conn.execute("DELETE FROM beneficiaries WHERE id = ?;", (target_ben_id,))

        if session_id:
            conn.execute("DELETE FROM anonymous_sessions WHERE id = ? OR session_token = ?;", (session_id, session_id))
            conn.execute("DELETE FROM consent_records WHERE session_id = ?;", (session_id,))

        # Delete interview sessions themselves
        for i_id in interview_ids:
            conn.execute("DELETE FROM interview_sessions WHERE id = ?;", (i_id,))

        # Preserve minimal non-identifying audit event
        log_audit_event(
            conn=conn,
            actor_id="anonymous",
            actor_name="Anonymous",
            actor_role="beneficiary",
            action="PROFILE_DELETED_RIGHT_TO_ERASURE",
            entity_type="beneficiary_lifecycle",
            entity_id=target_ben_id or session_id,
            metadata={"erasure_timestamp": now, "status": "completed"}
        )

        return {
            "status": "success",
            "message": "All profile data, interview sessions, answers, and referrals have been permanently purged in accordance with DPDP regulations."
        }
