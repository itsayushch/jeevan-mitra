from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List, Dict, Any
from app.database import get_db
from app.schemas.cases import (
    CaseResponse,
    CaseAssignRequest,
    CaseNoteCreate,
    CaseNoteResponse,
    CaseFollowUpRequest
)
from app.services.case_management_service import CaseManagementService
from app.dependencies.auth import require_authenticated_user, Actor
from app.utils.audit_events import log_isolated_audit_event

router = APIRouter(tags=["Staff Cases"])

STAFF_ROLES = {"field_worker", "district_admin", "super_admin"}
STAFF_READ_ROLES = {"field_worker", "district_admin", "auditor", "super_admin"}

@router.get("/staff/cases")
def list_cases(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    assigned_to_me: bool = False,
    district_id: Optional[str] = None,
    block_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    user: Actor = Depends(require_authenticated_user)
) -> List[Dict[str, Any]]:
    if not any(r in STAFF_READ_ROLES for r in user.roles):
        raise HTTPException(status_code=403, detail="Staff credentials required to access case inbox.")

    with get_db() as conn:
        return CaseManagementService.list_cases(
            conn=conn,
            actor=user,
            status=status,
            priority=priority,
            assigned_to_me=assigned_to_me,
            district_id=district_id,
            block_id=block_id,
            limit=limit,
            offset=offset
        )

@router.post("/staff/cases", status_code=201)
def create_case(
    payload: Dict[str, Any],
    user: Actor = Depends(require_authenticated_user)
) -> Dict[str, Any]:
    if not any(r in STAFF_ROLES for r in user.roles):
        raise HTTPException(status_code=403, detail="Authorized field worker or administrator credentials required.")

    beneficiary_id = payload.get("beneficiary_id")
    district_id = payload.get("district_id")
    block_id = payload.get("block_id")
    intake_source = payload.get("intake_source", "WEB")

    if not beneficiary_id or not district_id:
        raise HTTPException(status_code=422, detail="beneficiary_id and district_id are required.")

    if not user.check_scope(district_id, block_id):
        log_isolated_audit_event(
            actor_id=user.actor_id,
            actor_name=user.actor_name,
            actor_role=user.actor_role,
            action="SECURITY_ACCESS_DENIED",
            entity_type="beneficiary_case",
            entity_id=beneficiary_id,
            metadata={"reason": "create_case_outside_assigned_scope", "district_id": district_id, "block_id": block_id}
        )
        raise HTTPException(status_code=403, detail="Access denied: target district/block is outside your assigned scope.")

    with get_db() as conn:
        return CaseManagementService.get_or_create_case(
            conn=conn,
            beneficiary_id=beneficiary_id,
            district_id=district_id,
            block_id=block_id,
            intake_source=intake_source,
            assigned_worker_id=user.actor_id
        )

@router.get("/staff/cases/{case_id}")
def get_case(
    case_id: str,
    user: Actor = Depends(require_authenticated_user)
) -> Dict[str, Any]:
    if not any(r in STAFF_READ_ROLES for r in user.roles):
        raise HTTPException(status_code=403, detail="Staff credentials required.")

    with get_db() as conn:
        case = CaseManagementService.get_case(conn, case_id)
        if not case:
            raise HTTPException(status_code=404, detail="Case not found.")

        if not user.check_scope(case.get("district_id"), case.get("block_id")):
            log_isolated_audit_event(
                actor_id=user.actor_id,
                actor_name=user.actor_name,
                actor_role=user.actor_role,
                action="SECURITY_ACCESS_DENIED",
                entity_type="beneficiary_case",
                entity_id=case_id,
                metadata={"reason": "read_case_outside_assigned_scope", "district_id": case.get("district_id")}
            )
            raise HTTPException(status_code=403, detail="Access denied: case is outside your assigned scope.")

        notes = CaseManagementService.get_notes(conn, case_id, include_staff_only=True)
        # Fetch referrals for this case
        ref_rows = conn.execute("SELECT * FROM referrals WHERE case_id = ? ORDER BY updated_at DESC;", (case_id,)).fetchall()
        referrals = [dict(r) for r in ref_rows]

        # Fetch case assignments history
        assign_rows = conn.execute("SELECT * FROM case_assignments WHERE case_id = ? ORDER BY assigned_at DESC;", (case_id,)).fetchall()
        assignments = [dict(r) for r in assign_rows]

        result = dict(case)
        result["notes"] = notes
        result["referrals"] = referrals
        result["assignments"] = assignments
        return result

@router.post("/staff/cases/{case_id}/assign")
def assign_case(
    case_id: str,
    data: CaseAssignRequest,
    user: Actor = Depends(require_authenticated_user)
) -> Dict[str, Any]:
    if not any(r in STAFF_ROLES for r in user.roles):
        raise HTTPException(status_code=403, detail="Field worker or administrator credentials required.")

    with get_db() as conn:
        case = CaseManagementService.get_case(conn, case_id)
        if not case:
            raise HTTPException(status_code=404, detail="Case not found.")

        if not user.check_scope(case.get("district_id"), case.get("block_id")):
            log_isolated_audit_event(
                actor_id=user.actor_id,
                actor_name=user.actor_name,
                actor_role=user.actor_role,
                action="SECURITY_ACCESS_DENIED",
                entity_type="beneficiary_case",
                entity_id=case_id,
                metadata={"reason": "assign_case_outside_assigned_scope"}
            )
            raise HTTPException(status_code=403, detail="Access denied: case is outside your assigned scope.")

        return CaseManagementService.assign_case(
            conn=conn,
            case_id=case_id,
            worker_id=data.worker_id,
            assigned_by_user_id=user.actor_id,
            reason=data.assignment_reason
        )

@router.post("/staff/cases/{case_id}/notes", status_code=201)
def add_case_note(
    case_id: str,
    data: CaseNoteCreate,
    user: Actor = Depends(require_authenticated_user)
) -> Dict[str, Any]:
    if not any(r in STAFF_ROLES for r in user.roles):
        raise HTTPException(status_code=403, detail="Field worker or administrator credentials required.")

    with get_db() as conn:
        case = CaseManagementService.get_case(conn, case_id)
        if not case:
            raise HTTPException(status_code=404, detail="Case not found.")

        if not user.check_scope(case.get("district_id"), case.get("block_id")):
            log_isolated_audit_event(
                actor_id=user.actor_id,
                actor_name=user.actor_name,
                actor_role=user.actor_role,
                action="SECURITY_ACCESS_DENIED",
                entity_type="beneficiary_case",
                entity_id=case_id,
                metadata={"reason": "add_note_outside_assigned_scope"}
            )
            raise HTTPException(status_code=403, detail="Access denied: case is outside your assigned scope.")

        return CaseManagementService.add_note(
            conn=conn,
            case_id=case_id,
            author_user_id=user.actor_id,
            note_text=data.note_text,
            note_type=data.note_type,
            visibility=data.visibility
        )

@router.post("/staff/cases/{case_id}/follow-up")
def schedule_case_follow_up(
    case_id: str,
    data: CaseFollowUpRequest,
    user: Actor = Depends(require_authenticated_user)
) -> Dict[str, Any]:
    if not any(r in STAFF_ROLES for r in user.roles):
        raise HTTPException(status_code=403, detail="Field worker or administrator credentials required.")

    with get_db() as conn:
        case = CaseManagementService.get_case(conn, case_id)
        if not case:
            raise HTTPException(status_code=404, detail="Case not found.")

        if not user.check_scope(case.get("district_id"), case.get("block_id")):
            log_isolated_audit_event(
                actor_id=user.actor_id,
                actor_name=user.actor_name,
                actor_role=user.actor_role,
                action="SECURITY_ACCESS_DENIED",
                entity_type="beneficiary_case",
                entity_id=case_id,
                metadata={"reason": "schedule_followup_outside_assigned_scope"}
            )
            raise HTTPException(status_code=403, detail="Access denied: case is outside your assigned scope.")

        next_str = data.next_follow_up_at.isoformat() if hasattr(data.next_follow_up_at, "isoformat") else str(data.next_follow_up_at)
        return CaseManagementService.schedule_follow_up(
            conn=conn,
            case_id=case_id,
            next_follow_up_at=next_str,
            actor_user_id=user.actor_id,
            note=data.note
        )
