from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
from app.database import get_db
from app.models import ConsentCreate, ConsentRecordCreate, ConsentRevokeRequest
from app.services.consent_service import ConsentService
from app.dependencies.auth import get_current_actor, Actor

router = APIRouter(prefix="/consents", tags=["Consents"])

@router.post("", status_code=201)
def record_consent(data: Dict[str, Any], actor: Actor = Depends(get_current_actor)):
    """
    Records versioned consent under A1. Supports both ConsentRecordCreate and legacy ConsentCreate payloads.
    """
    if not actor.is_staff():
        if data.get("session_id") and actor.session_id and data["session_id"] != actor.session_id:
            raise HTTPException(status_code=403, detail="Session does not belong to caller")
        if data.get("beneficiary_id") and actor.beneficiary_id and data["beneficiary_id"] != actor.beneficiary_id:
            raise HTTPException(status_code=403, detail="Beneficiary does not belong to caller")

    with get_db() as conn:
        if not data.get("session_id") and actor.session_id:
            data["session_id"] = actor.session_id
        if not data.get("beneficiary_id") and actor.beneficiary_id:
            data["beneficiary_id"] = actor.beneficiary_id

        if "consent_type" in data:
            sess_id = data.get("session_id")
            ben_id = data.get("beneficiary_id")

            if not sess_id and not ben_id:
                raise HTTPException(status_code=422, detail="Either session_id or beneficiary_id is required")

            if ben_id and ben_id.startswith("ben_"):
                ben = conn.execute("SELECT id FROM beneficiaries WHERE id = ?;", (ben_id,)).fetchone()
                if not ben:
                    raise HTTPException(status_code=404, detail="Beneficiary not found")

            req = ConsentRecordCreate(**data)
            return ConsentService.record_consent(conn, req, actor_id=actor.actor_id)
        else:
            # Legacy consent model mapping
            ben_id = data.get("beneficiary_id")
            sess_id = data.get("session_id")

            if ben_id:
                # Check beneficiary exists
                ben = conn.execute("SELECT id FROM beneficiaries WHERE id = ?;", (ben_id,)).fetchone()
                if not ben:
                    raise HTTPException(status_code=404, detail="Beneficiary not found")

                # Record in both legacy and versioned consent systems
                rec = ConsentRecordCreate(
                    beneficiary_id=ben_id,
                    session_id=sess_id,
                    consent_type="dpdp_general",
                    policy_version=data.get("notice_version", "1.0"),
                    user_language=data.get("user_language", "hi"),
                    capture_channel=data.get("capture_channel", "web_app"),
                    granted=bool(data.get("dpdp_affirmative_consent", data.get("granted", True)))
                )
                return ConsentService.record_consent(conn, rec, actor_id=actor.actor_id)
            elif sess_id:
                # Check session exists
                sess = conn.execute("SELECT id FROM anonymous_sessions WHERE id = ?;", (sess_id,)).fetchone()
                if not sess:
                    raise HTTPException(status_code=404, detail="Session not found")

                rec = ConsentRecordCreate(
                    session_id=sess_id,
                    consent_type="dpdp_general",
                    policy_version=data.get("notice_version", "1.0"),
                    user_language=data.get("user_language", "hi"),
                    capture_channel=data.get("capture_channel", "web_app"),
                    granted=bool(data.get("dpdp_affirmative_consent", data.get("granted", True)))
                )
                return ConsentService.record_consent(conn, rec, actor_id=actor.actor_id)
            else:
                raise HTTPException(status_code=422, detail="beneficiary_id is required")

@router.get("/{session_or_beneficiary_id}")
def get_consents_by_id(
    session_or_beneficiary_id: str,
    actor: Actor = Depends(get_current_actor)
):
    """
    Retrieves consent history for either an anonymous session ID or a beneficiary ID.
    """
    if not actor.is_staff() and session_or_beneficiary_id not in (actor.session_id, actor.beneficiary_id):
        raise HTTPException(status_code=403, detail="Consent history does not belong to caller")
    with get_db() as conn:
        return ConsentService.get_consents(conn, session_or_beneficiary_id)

@router.get("/beneficiary/{beneficiary_id}")
def get_beneficiary_consents_legacy(
    beneficiary_id: str,
    actor: Actor = Depends(get_current_actor)
):
    """
    Backwards-compatible route for retrieving beneficiary consents.
    """
    if not actor.is_staff() and beneficiary_id != actor.beneficiary_id:
        raise HTTPException(status_code=403, detail="Consent history does not belong to caller")
    with get_db() as conn:
        rows = conn.execute("""
            SELECT * FROM consents WHERE beneficiary_id = ? ORDER BY timestamp DESC;
        """, (beneficiary_id,)).fetchall()
        if not rows:
            # Check versioned records
            rows = conn.execute("""
                SELECT * FROM consent_records WHERE beneficiary_id = ? ORDER BY timestamp DESC;
            """, (beneficiary_id,)).fetchall()
        return [dict(r) for r in rows]

@router.post("/{consent_id}/revoke")
def revoke_consent(consent_id: str, body: Optional[ConsentRevokeRequest] = None, actor: Actor = Depends(get_current_actor)):
    """
    Revokes consent, halts future processing immediately, and executes post-revocation cascade.
    """
    reason = body.reason if body else "Beneficiary requested revocation"
    with get_db() as conn:
        consent = conn.execute(
            "SELECT session_id, beneficiary_id FROM consent_records WHERE id = ?;",
            (consent_id,)
        ).fetchone()
        if not consent:
            raise HTTPException(status_code=404, detail="Consent record not found")
        if not actor.is_staff() and not (
            consent["session_id"] == actor.session_id
            or consent["beneficiary_id"] == actor.beneficiary_id
        ):
            raise HTTPException(status_code=403, detail="Consent record does not belong to caller")
        return ConsentService.revoke_consent(conn, consent_id, reason=reason, actor_id=actor.actor_id)
