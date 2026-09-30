from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, List, Dict, Any
from app.database import get_db
from app.models import (
    CreateReferralRequest, AssignCounselorRequest,
    UpdateReferralStatusRequest, AddCounselorNoteRequest
)
from app.schemas.referrals import (
    ReferralCreate, ReferralTransitionRequest, ContactAttemptCreate,
    OutcomeCreate, OutcomeVerifyRequest
)
from app.services.referral_service import ReferralService
from app.dependencies.auth import get_current_actor, require_counselor_or_admin, require_authenticated_user, Actor
from app.utils.audit_events import log_isolated_audit_event

router = APIRouter(tags=["Referrals"])

STAFF_ROLES = {"field_worker", "district_admin", "super_admin"}
STAFF_READ_ROLES = {"field_worker", "district_admin", "auditor", "super_admin"}

# ============================================================================
# Beneficiary Referral Endpoints (A7)
# ============================================================================
@router.post("/referrals", status_code=201)
def create_referral(
    data: CreateReferralRequest,
    actor: Actor = Depends(get_current_actor)
):
    """
    Submits a referral request for counselor review.
    Requires prior 'counselor_referral' consent.
    """
    with get_db() as conn:
        return ReferralService.create_referral(conn, data, actor)

@router.get("/referrals/me")
def get_my_referrals(actor: Actor = Depends(get_current_actor)):
    """
    Retrieves all referrals created by or linked to the active session/beneficiary.
    """
    with get_db() as conn:
        return ReferralService.get_my_referrals(conn, actor)

# ============================================================================
# Counselor & Admin Referral Workflow Endpoints (A7)
# ============================================================================
@router.get("/counselor/referrals")
def list_counselor_referrals(
    status: Optional[str] = None,
    actor: Actor = Depends(require_counselor_or_admin)
):
    """
    Returns cases in the counselor queue (filtered by status or assigned counselor).
    """
    with get_db() as conn:
        return ReferralService.list_counselor_referrals(conn, actor, status=status)

@router.patch("/counselor/referrals/{referral_id}/assign")
def assign_counselor_to_case(
    referral_id: str,
    data: AssignCounselorRequest,
    actor: Actor = Depends(require_counselor_or_admin)
):
    with get_db() as conn:
        return ReferralService.assign_counselor(conn, referral_id, data, actor)

@router.patch("/counselor/referrals/{referral_id}/status")
def update_case_status(
    referral_id: str,
    data: UpdateReferralStatusRequest,
    actor: Actor = Depends(require_counselor_or_admin)
):
    with get_db() as conn:
        return ReferralService.update_status(conn, referral_id, data, actor)

@router.post("/counselor/referrals/{referral_id}/notes", status_code=201)
def add_case_note(
    referral_id: str,
    data: AddCounselorNoteRequest,
    actor: Actor = Depends(require_counselor_or_admin)
):
    with get_db() as conn:
        return ReferralService.add_counselor_note(conn, referral_id, data, actor)

# ============================================================================
# Legacy Referrals Endpoints (Backwards Compatibility)
# ============================================================================
@router.get("/referrals")
def legacy_list_referrals(status: Optional[str] = None):
    with get_db() as conn:
        query = "SELECT * FROM referrals WHERE 1=1"
        params = []
        if status:
            query += " AND status = ?"
            params.append(status)
        query += " ORDER BY created_at DESC;"
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]

@router.get("/referrals/{referral_id}")
def legacy_get_referral(referral_id: str):
    with get_db() as conn:
        # Check referral_cases first
        case = conn.execute("SELECT * FROM referral_cases WHERE id = ?;", (referral_id,)).fetchone()
        if case:
            return dict(case)

        row = conn.execute("SELECT * FROM referrals WHERE id = ?;", (referral_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Referral not found")
        return dict(row)

# ============================================================================
# Canonical Sprint 5 Staff Referral Endpoints
# ============================================================================
@router.post("/staff/cases/{case_id}/referrals", status_code=201)
def create_referral_for_case(
    case_id: str,
    data: ReferralCreate,
    user: Actor = Depends(require_authenticated_user)
) -> Dict[str, Any]:
    if not any(r in STAFF_ROLES for r in user.roles):
        raise HTTPException(status_code=403, detail="Field worker or administrator credentials required.")

    with get_db() as conn:
        try:
            return ReferralService.create_canonical_referral(
                conn=conn,
                case_id=case_id,
                recommendation_id=data.recommendationId,
                actor=user,
                note=data.note
            )
        except PermissionError as pe:
            log_isolated_audit_event(
                actor_id=user.actor_id,
                actor_name=user.actor_name,
                actor_role=user.actor_role,
                action="SECURITY_ACCESS_DENIED",
                entity_type="referral",
                entity_id=case_id,
                metadata={"reason": str(pe)}
            )
            raise HTTPException(status_code=403, detail=str(pe))
        except ValueError as ve:
            msg = str(ve)
            if "not found" in msg.lower():
                raise HTTPException(status_code=404, detail=msg)
            elif "already exists" in msg.lower():
                raise HTTPException(status_code=409, detail=msg)
            else:
                raise HTTPException(status_code=400, detail=msg)

@router.get("/staff/referrals")
def list_referrals(
    case_id: Optional[str] = None,
    beneficiary_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    user: Actor = Depends(require_authenticated_user)
) -> List[Dict[str, Any]]:
    if not any(r in STAFF_READ_ROLES for r in user.roles):
        raise HTTPException(status_code=403, detail="Staff credentials required.")

    with get_db() as conn:
        return ReferralService.list_referrals(
            conn=conn,
            actor=user,
            case_id=case_id,
            beneficiary_id=beneficiary_id,
            status=status,
            limit=limit,
            offset=offset
        )

@router.get("/staff/referrals/{referral_id}")
def get_referral_details(
    referral_id: str,
    user: Actor = Depends(require_authenticated_user)
) -> Dict[str, Any]:
    if not any(r in STAFF_READ_ROLES for r in user.roles):
        raise HTTPException(status_code=403, detail="Staff credentials required.")

    with get_db() as conn:
        ref = ReferralService.get_referral(conn, referral_id)
        if not ref:
            raise HTTPException(status_code=404, detail="Referral not found.")

        # Check scope on linked opportunity if worker
        opp = conn.execute("SELECT district_id, block_id FROM local_opportunities WHERE id = ?", (ref.get("local_opportunity_id"),)).fetchone()
        if opp and not user.check_scope(opp["district_id"], opp["block_id"]):
            log_isolated_audit_event(
                actor_id=user.actor_id,
                actor_name=user.actor_name,
                actor_role=user.actor_role,
                action="SECURITY_ACCESS_DENIED",
                entity_type="referral",
                entity_id=referral_id,
                metadata={"reason": "read_referral_outside_assigned_scope"}
            )
            raise HTTPException(status_code=403, detail="Access denied: referral is outside your assigned scope.")

        history = ReferralService.get_referral_history(conn, referral_id)
        contact_attempts = ReferralService.get_contact_attempts(conn, referral_id)
        outcomes = ReferralService.get_outcomes(conn, referral_id)

        result = dict(ref)
        result["history"] = history
        result["contact_attempts"] = contact_attempts
        result["outcomes"] = outcomes
        return result

@router.post("/staff/referrals/{referral_id}/transition")
def transition_referral_status(
    referral_id: str,
    data: ReferralTransitionRequest,
    user: Actor = Depends(require_authenticated_user)
) -> Dict[str, Any]:
    if not any(r in STAFF_ROLES for r in user.roles):
        raise HTTPException(status_code=403, detail="Field worker or administrator credentials required.")

    with get_db() as conn:
        ref = ReferralService.get_referral(conn, referral_id)
        if not ref:
            raise HTTPException(status_code=404, detail="Referral not found.")

        opp = conn.execute("SELECT district_id, block_id FROM local_opportunities WHERE id = ?", (ref.get("local_opportunity_id"),)).fetchone()
        if opp and not user.check_scope(opp["district_id"], opp["block_id"]):
            log_isolated_audit_event(
                actor_id=user.actor_id,
                actor_name=user.actor_name,
                actor_role=user.actor_role,
                action="SECURITY_ACCESS_DENIED",
                entity_type="referral",
                entity_id=referral_id,
                metadata={"reason": "transition_outside_assigned_scope"}
            )
            raise HTTPException(status_code=403, detail="Access denied: referral is outside your assigned scope.")

        try:
            return ReferralService.transition_status(
                conn=conn,
                referral_id=referral_id,
                to_status=data.to_status,
                actor=user,
                reason=data.reason,
                note=data.note
            )
        except ValueError as ve:
            raise HTTPException(status_code=400, detail=str(ve))

@router.post("/staff/referrals/{referral_id}/contact-attempts", status_code=201)
def log_contact_attempt(
    referral_id: str,
    data: ContactAttemptCreate,
    user: Actor = Depends(require_authenticated_user)
) -> Dict[str, Any]:
    if not any(r in STAFF_ROLES for r in user.roles):
        raise HTTPException(status_code=403, detail="Field worker or administrator credentials required.")

    with get_db() as conn:
        ref = ReferralService.get_referral(conn, referral_id)
        if not ref:
            raise HTTPException(status_code=404, detail="Referral not found.")

        payload = data.model_dump() if hasattr(data, "model_dump") else data.dict()
        if payload.get("next_follow_up_at") and hasattr(payload["next_follow_up_at"], "isoformat"):
            payload["next_follow_up_at"] = payload["next_follow_up_at"].isoformat()

        return ReferralService.log_contact_attempt(conn, referral_id, payload, user)

@router.post("/staff/referrals/{referral_id}/outcomes", status_code=201)
def record_outcome(
    referral_id: str,
    data: OutcomeCreate,
    user: Actor = Depends(require_authenticated_user)
) -> Dict[str, Any]:
    if not any(r in STAFF_ROLES for r in user.roles):
        raise HTTPException(status_code=403, detail="Field worker or administrator credentials required.")

    with get_db() as conn:
        ref = ReferralService.get_referral(conn, referral_id)
        if not ref:
            raise HTTPException(status_code=404, detail="Referral not found.")

        payload = data.model_dump() if hasattr(data, "model_dump") else data.dict()
        if payload.get("occurred_at") and hasattr(payload["occurred_at"], "isoformat"):
            payload["occurred_at"] = payload["occurred_at"].isoformat()

        return ReferralService.record_outcome(conn, referral_id, payload, user)

@router.post("/staff/referrals/outcomes/{outcome_id}/verify")
def verify_outcome(
    outcome_id: str,
    data: OutcomeVerifyRequest,
    user: Actor = Depends(require_authenticated_user)
) -> Dict[str, Any]:
    if not any(r in STAFF_ROLES for r in user.roles):
        raise HTTPException(status_code=403, detail="Staff credentials required.")

    with get_db() as conn:
        try:
            return ReferralService.verify_outcome(
                conn=conn,
                outcome_id=outcome_id,
                status=data.outcome_status,
                actor=user,
                evidence_summary=data.evidence_summary
            )
        except ValueError as ve:
            raise HTTPException(status_code=400, detail=str(ve))

@router.get("/staff/referrals/{referral_id}/history")
def get_referral_history(
    referral_id: str,
    user: Actor = Depends(require_authenticated_user)
) -> List[Dict[str, Any]]:
    if not any(r in STAFF_READ_ROLES for r in user.roles):
        raise HTTPException(status_code=403, detail="Staff credentials required.")

    with get_db() as conn:
        return ReferralService.get_referral_history(conn, referral_id)

