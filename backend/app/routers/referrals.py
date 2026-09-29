from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, List, Dict, Any
from app.database import get_db
from app.models import (
    CreateReferralRequest, AssignCounselorRequest,
    UpdateReferralStatusRequest, AddCounselorNoteRequest
)
from app.services.referral_service import ReferralService
from app.dependencies.auth import get_current_actor, require_admin_or_worker, require_counselor_or_admin, Actor

router = APIRouter(tags=["Referrals"])

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
def legacy_list_referrals(
    status: Optional[str] = None,
    actor: Actor = Depends(require_admin_or_worker)
):
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
def legacy_get_referral(referral_id: str, actor: Actor = Depends(require_admin_or_worker)):
    with get_db() as conn:
        # Check referral_cases first
        case = conn.execute("SELECT * FROM referral_cases WHERE id = ?;", (referral_id,)).fetchone()
        if case:
            return dict(case)

        row = conn.execute("SELECT * FROM referrals WHERE id = ?;", (referral_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Referral not found")
        return dict(row)
