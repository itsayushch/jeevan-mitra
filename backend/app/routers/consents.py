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
    with get_db() as conn:
        if "consent_type" in data:
            req = ConsentRecordCreate(**data)
            return ConsentService.record_consent(conn, req, actor_id=actor.actor_id)
        else:
            # Legacy consent model mapping
            ben_id = data.get("beneficiary_id")
            if not ben_id:
                raise HTTPException(status_code=422, detail="beneficiary_id is required")

            # Check beneficiary exists
            ben = conn.execute("SELECT id FROM beneficiaries WHERE id = ?;", (ben_id,)).fetchone()
            if not ben:
                raise HTTPException(status_code=404, detail="Beneficiary not found")

            # Record in both legacy and versioned consent systems
            rec = ConsentRecordCreate(
                beneficiary_id=ben_id,
                consent_type="dpdp_general",
                policy_version=data.get("notice_version", "1.0"),
                granted=bool(data.get("dpdp_affirmative_consent", True))
            )
            return ConsentService.record_consent(conn, rec, actor_id=actor.actor_id)

@router.get("/{session_or_beneficiary_id}")
def get_consents_by_id(session_or_beneficiary_id: str):
    """
    Retrieves consent history for either an anonymous session ID or a beneficiary ID.
    """
    with get_db() as conn:
        return ConsentService.get_consents(conn, session_or_beneficiary_id)

@router.get("/beneficiary/{beneficiary_id}")
def get_beneficiary_consents_legacy(beneficiary_id: str):
    """
    Backwards-compatible route for retrieving beneficiary consents.
    """
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
        return ConsentService.revoke_consent(conn, consent_id, reason=reason, actor_id=actor.actor_id)
