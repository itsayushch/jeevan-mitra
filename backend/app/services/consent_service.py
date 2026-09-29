import uuid
import sqlite3
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from app.models import ConsentRecordCreate, ConsentRevokeRequest
from app.utils.audit_events import log_audit_event
from app.utils.errors import EntityNotFoundException, AppError

class ConsentService:
    @staticmethod
    def record_consent(conn: sqlite3.Connection, data: ConsentRecordCreate, actor_id: str = "system") -> Dict[str, Any]:
        consent_id = f"cnst_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).isoformat()
        status = "granted" if data.granted else "revoked"

        conn.execute("""
            INSERT INTO consent_records (
                id, session_id, beneficiary_id, consent_type, policy_version,
                status, user_language, capture_channel, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            consent_id, data.session_id, data.beneficiary_id, data.consent_type,
            data.policy_version or "1.0", status, data.user_language or "hi",
            data.capture_channel or "web_app", now
        ))

        # Also insert into legacy consents table if beneficiary_id is present
        if data.beneficiary_id:
            legacy_id = f"consent_{uuid.uuid4().hex[:12]}"
            conn.execute("""
                INSERT INTO consents (
                    id, beneficiary_id, purpose, notice_version,
                    audio_consent_recorded, voice_retention_choice, dpdp_affirmative_consent, timestamp
                ) VALUES (?, ?, ?, ?, 1, 'do_not_keep', ?, ?);
            """, (legacy_id, data.beneficiary_id, f"DPDP Consent for {data.consent_type}", data.policy_version or "1.0", 1 if data.granted else 0, now))

        log_audit_event(
            conn=conn,
            actor_id=actor_id,
            actor_name="Beneficiary / Guest",
            actor_role="beneficiary",
            action="CONSENT_RECORDED",
            entity_type="consent_record",
            entity_id=consent_id,
            new_values=data.model_dump(),
            metadata={"consent_type": data.consent_type, "status": status}
        )

        row = conn.execute("SELECT * FROM consent_records WHERE id = ?;", (consent_id,)).fetchone()
        return dict(row)

    @staticmethod
    def get_consents(conn: sqlite3.Connection, identifier: str) -> List[Dict[str, Any]]:
        """Fetch consent history for either session_id or beneficiary_id."""
        rows = conn.execute("""
            SELECT * FROM consent_records
            WHERE session_id = ? OR beneficiary_id = ?
            ORDER BY timestamp DESC;
        """, (identifier, identifier)).fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def revoke_consent(conn: sqlite3.Connection, consent_id: str, reason: Optional[str] = None, actor_id: str = "system") -> Dict[str, Any]:
        """Revokes a specific consent record and applies post-revocation actions."""
        row = conn.execute("SELECT * FROM consent_records WHERE id = ?;", (consent_id,)).fetchone()
        if not row:
            raise EntityNotFoundException("ConsentRecord", consent_id)

        now = datetime.now(timezone.utc).isoformat()
        reason_text = reason or "Beneficiary requested revocation"

        conn.execute("""
            UPDATE consent_records
            SET status = 'revoked', revoked_at = ?, revocation_reason = ?
            WHERE id = ?;
        """, (now, reason_text, consent_id))

        consent_type = row["consent_type"]
        ben_id = row["beneficiary_id"]
        sess_id = row["session_id"]

        # Apply post-revocation cascade policies:
        if consent_type == "counselor_referral":
            # Pause or close active referrals
            conn.execute("""
                UPDATE referral_cases
                SET status = 'closed', notes = COALESCE(notes, '') || ' [Closed: Consent revoked by beneficiary]'
                WHERE (
                    (beneficiary_id IS NOT NULL AND beneficiary_id = ?)
                    OR (interview_id IS NOT NULL AND (interview_id = ? OR interview_id IN (
                        SELECT id FROM interview_sessions WHERE beneficiary_id = ? OR session_id = ?
                    )))
                ) AND status NOT IN ('resolved', 'closed');
            """, (ben_id or "", sess_id or "", ben_id or "", sess_id or ""))

        elif consent_type == "profile_storage":
            # If profile storage is revoked, anonymize/mark non-retained
            if ben_id:
                conn.execute("""
                    UPDATE beneficiaries
                    SET name = 'Anonymized User', phone = NULL, village = NULL
                    WHERE id = ?;
                """, (ben_id,))

        log_audit_event(
            conn=conn,
            actor_id=actor_id,
            actor_name="Beneficiary / Guest",
            actor_role="beneficiary",
            action="CONSENT_REVOKED",
            entity_type="consent_record",
            entity_id=consent_id,
            old_values={"status": row["status"]},
            new_values={"status": "revoked", "revocation_reason": reason_text},
            metadata={"consent_type": consent_type}
        )

        updated_row = conn.execute("SELECT * FROM consent_records WHERE id = ?;", (consent_id,)).fetchone()
        return dict(updated_row)
