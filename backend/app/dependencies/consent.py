from typing import Optional, Callable
import sqlite3
from fastapi import Header, Depends
from app.database import get_db
from app.dependencies.auth import get_current_actor, Actor
from app.utils.errors import ConsentRequiredException, ConsentRevokedException

def verify_consent(
    conn: sqlite3.Connection,
    consent_type: str,
    beneficiary_id: Optional[str] = None,
    session_id: Optional[str] = None
) -> None:
    """
    Checks if active valid consent exists for the specified beneficiary or session.
    Raises ConsentRequiredException or ConsentRevokedException if not granted.
    """
    if not beneficiary_id and not session_id:
        raise ConsentRequiredException(consent_type, "Neither beneficiary_id nor session_id was provided to verify consent.")

    # 1. Query latest versioned consent record for this type (or general DPDP consent)
    query = """
        SELECT consent_type, status, revocation_reason
        FROM consent_records
        WHERE (consent_type = ? OR consent_type = 'dpdp_general')
          AND (
            (session_id IS NOT NULL AND session_id = ?)
            OR (beneficiary_id IS NOT NULL AND beneficiary_id = ?)
          )
        ORDER BY (CASE WHEN consent_type = ? THEN 1 ELSE 2 END) ASC, timestamp DESC, rowid DESC
        LIMIT 1;
    """
    row = conn.execute(query, (consent_type, session_id or "", beneficiary_id or "", consent_type)).fetchone()

    if row:
        if row["status"] == "revoked":
            raise ConsentRevokedException(
                consent_type,
                f"Consent for '{row['consent_type']}' was explicitly revoked: {row['revocation_reason'] or 'No reason provided.'}"
            )
        elif row["status"] == "granted":
            return  # Consent verified
    else:
        # Check if beneficiary has legacy affirmative consent
        if beneficiary_id:
            legacy = conn.execute("""
                SELECT dpdp_affirmative_consent
                FROM consents
                WHERE beneficiary_id = ?
                ORDER BY timestamp DESC, rowid DESC
                LIMIT 1;
            """, (beneficiary_id,)).fetchone()

            if legacy and legacy["dpdp_affirmative_consent"]:
                return  # Legacy DPDP affirmative consent accepted

        # If no record found
        raise ConsentRequiredException(consent_type)

def require_consent_dependency(consent_type: str) -> Callable:
    """
    Returns a FastAPI dependency that verifies consent for the active actor.
    """
    def dependency(
        actor: Actor = Depends(get_current_actor),
        x_beneficiary_id: Optional[str] = Header(None, alias="X-Beneficiary-ID"),
        x_session_id: Optional[str] = Header(None, alias="X-Session-ID")
    ):
        target_ben_id = actor.beneficiary_id or x_beneficiary_id
        target_sess_id = actor.session_id or x_session_id or actor.actor_id

        with get_db() as conn:
            verify_consent(conn, consent_type, target_ben_id, target_sess_id)
        return True

    return dependency
