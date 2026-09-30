from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from app.database import get_db
from app.schemas.opportunities import (
    OpportunityCreate,
    OpportunityUpdate,
    OpportunityBeneficiaryResponse,
    OpportunityStaffResponse,
    EvidenceCreate,
    VerificationAction,
    MatchStateResponse,
    ProviderCreate,
    ProviderResponse
)
from app.services.opportunity_service import OpportunityService
from app.services.opportunity_verification_service import OpportunityVerificationService
from app.services.match_state_service import MatchStateService
from app.dependencies.auth import require_authenticated_user, get_current_actor, Actor
from app.utils.audit_events import log_audit_event

router = APIRouter(tags=["Opportunities"])

FIELD_WORKER_ROLES = {"field_worker", "district_admin", "super_admin"}
STAFF_READ_ROLES = {"field_worker", "district_admin", "auditor", "super_admin"}

@router.post("/staff/opportunity-providers", status_code=201, response_model=ProviderResponse)
def create_provider(data: ProviderCreate, user: Actor = Depends(require_authenticated_user)):
    if not any(r in FIELD_WORKER_ROLES for r in user.roles):
        raise HTTPException(status_code=403, detail="Field worker or district administrator credentials required.")
    
    if not user.check_scope(data.district_id, data.block_id):
        raise HTTPException(status_code=403, detail="Access denied: outside assigned geographic scope.")

    with get_db() as conn:
        payload = data.model_dump(exclude_unset=True) if hasattr(data, "model_dump") else data.dict(exclude_unset=True)
        return OpportunityService.create_provider(conn, payload, user.actor_id)

@router.post("/staff/opportunities", status_code=201, response_model=OpportunityStaffResponse)
def create_opportunity(data: OpportunityCreate, user: Actor = Depends(require_authenticated_user)):
    if not any(r in FIELD_WORKER_ROLES for r in user.roles):
        raise HTTPException(status_code=403, detail="Field worker or district administrator credentials required.")
    
    if not user.check_scope(data.district_id, data.block_id):
        raise HTTPException(status_code=403, detail="Access denied: outside assigned geographic scope.")

    with get_db() as conn:
        payload = data.model_dump(exclude_unset=True) if hasattr(data, "model_dump") else data.dict(exclude_unset=True)
        return OpportunityService.create_opportunity(conn, payload, user.actor_id)

@router.get("/staff/opportunities/{opportunity_id}", response_model=OpportunityStaffResponse)
def get_staff_opportunity(opportunity_id: str, user: Actor = Depends(require_authenticated_user)):
    if not any(r in STAFF_READ_ROLES for r in user.roles):
        raise HTTPException(status_code=403, detail="Staff credentials required.")
    
    with get_db() as conn:
        opp = OpportunityService.get_opportunity(conn, opportunity_id, include_staff_details=True)
        if not opp:
            raise HTTPException(status_code=404, detail="Opportunity not found")
        
        if not user.check_scope(opp.get("district_id"), opp.get("block_id")):
            log_audit_event(
                conn=conn,
                actor_id=user.actor_id,
                actor_name=user.actor_name,
                actor_role=user.actor_role,
                action="SECURITY_ACCESS_DENIED",
                entity_type="local_opportunity",
                entity_id=opportunity_id,
                metadata={"reason": "cross_scope_access_attempt"}
            )
            conn.commit()
            raise HTTPException(status_code=403, detail="Access denied: outside assigned geographic scope.")
        
        return opp

@router.patch("/staff/opportunities/{opportunity_id}", response_model=OpportunityStaffResponse)
def patch_staff_opportunity(opportunity_id: str, data: OpportunityUpdate, user: Actor = Depends(require_authenticated_user)):
    if not any(r in FIELD_WORKER_ROLES for r in user.roles):
        raise HTTPException(status_code=403, detail="Field worker or district administrator credentials required.")
    
    with get_db() as conn:
        opp = OpportunityService.get_opportunity(conn, opportunity_id)
        if not opp:
            raise HTTPException(status_code=404, detail="Opportunity not found")
        
        if not user.check_scope(opp.get("district_id"), opp.get("block_id")):
            log_audit_event(
                conn=conn,
                actor_id=user.actor_id,
                actor_name=user.actor_name,
                actor_role=user.actor_role,
                action="SECURITY_ACCESS_DENIED",
                entity_type="local_opportunity",
                entity_id=opportunity_id,
                metadata={"reason": "cross_scope_access_attempt"}
            )
            conn.commit()
            raise HTTPException(status_code=403, detail="Access denied: outside assigned geographic scope.")

        payload = data.model_dump(exclude_unset=True) if hasattr(data, "model_dump") else data.dict(exclude_unset=True)
        return OpportunityService.update_opportunity_fields(conn, opportunity_id, payload, user.actor_id)

@router.post("/staff/opportunities/{opportunity_id}/evidence", status_code=201)
def add_evidence(opportunity_id: str, data: EvidenceCreate, user: Actor = Depends(require_authenticated_user)):
    if not any(r in FIELD_WORKER_ROLES for r in user.roles):
        raise HTTPException(status_code=403, detail="Field worker or district administrator credentials required.")
    
    with get_db() as conn:
        opp = OpportunityService.get_opportunity(conn, opportunity_id)
        if not opp:
            raise HTTPException(status_code=404, detail="Opportunity not found")
        
        if not user.check_scope(opp.get("district_id"), opp.get("block_id")):
            log_audit_event(
                conn=conn,
                actor_id=user.actor_id,
                actor_name=user.actor_name,
                actor_role=user.actor_role,
                action="SECURITY_ACCESS_DENIED",
                entity_type="local_opportunity",
                entity_id=opportunity_id,
                metadata={"reason": "cross_scope_access_attempt"}
            )
            conn.commit()
            raise HTTPException(status_code=403, detail="Access denied: outside assigned geographic scope.")

        payload = data.model_dump(exclude_unset=True) if hasattr(data, "model_dump") else data.dict(exclude_unset=True)
        try:
            return OpportunityVerificationService.submit_evidence(conn, opportunity_id, payload, user.actor_id)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

@router.post("/staff/opportunities/{opportunity_id}/{action}")
def verify_opportunity(opportunity_id: str, action: str, data: VerificationAction, user: Actor = Depends(require_authenticated_user)):
    if not any(r in FIELD_WORKER_ROLES for r in user.roles):
        raise HTTPException(status_code=403, detail="Field worker or district administrator credentials required.")
    
    valid_actions = {
        "submit": "SUBMITTED",
        "verify": "VERIFIED",
        "reverify": "REVERIFIED",
        "mark-full": "MARKED_FULL",
        "pause": "PAUSED",
        "close": "CLOSED",
        "reject": "REJECTED"
    }
    if action not in valid_actions:
        raise HTTPException(status_code=400, detail="Invalid action")
        
    with get_db() as conn:
        opp = OpportunityService.get_opportunity(conn, opportunity_id)
        if not opp:
            raise HTTPException(status_code=404, detail="Opportunity not found")
        
        if not user.check_scope(opp.get("district_id"), opp.get("block_id")):
            log_audit_event(
                conn=conn,
                actor_id=user.actor_id,
                actor_name=user.actor_name,
                actor_role=user.actor_role,
                action="SECURITY_ACCESS_DENIED",
                entity_type="local_opportunity",
                entity_id=opportunity_id,
                metadata={"reason": "cross_scope_access_attempt"}
            )
            conn.commit()
            raise HTTPException(status_code=403, detail="Access denied: outside assigned geographic scope.")

        try:
            expires_at = data.verification_expires_at.isoformat() if data.verification_expires_at else None
            return OpportunityVerificationService.transition_status(
                conn, opportunity_id, valid_actions[action], user.actor_id,
                expires_at=expires_at, reason=data.reason
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

@router.get("/opportunities", response_model=List[OpportunityBeneficiaryResponse])
def list_opportunities():
    with get_db() as conn:
        now_str = datetime.now(timezone.utc).isoformat()
        # Read-time expiry check: only return active opportunities whose verification_expires_at is strictly in the future
        cursor = conn.execute("""
            SELECT * FROM local_opportunities 
            WHERE status = 'ACTIVE'
              AND (verification_expires_at IS NULL OR verification_expires_at > ?)
        """, (now_str,))
        return [dict(row) for row in cursor.fetchall()]

@router.get("/opportunities/matches/{qualification_id}", response_model=MatchStateResponse)
def get_match_state(
    qualification_id: str,
    district_id: Optional[str] = Query(None),
    block_id: Optional[str] = Query(None),
    actor: Actor = Depends(get_current_actor)
):
    with get_db() as conn:
        ben_id = actor.beneficiary_id or actor.actor_id or "anonymous"
        # If district not explicitly passed, infer from actor's scopes if available
        if not district_id and actor.scopes:
            district_id = actor.scopes[0].get("district_id")
            block_id = actor.scopes[0].get("block_id")
        
        match_info = MatchStateService.get_or_compute_match(
            conn, ben_id, qualification_id, district_id=district_id, block_id=block_id
        )
        return MatchStateResponse(
            matchState=match_info["matchState"],
            beneficiaryMessage=match_info["beneficiaryMessage"],
            canRequestReferral=match_info["canRequestReferral"],
            canRequestWorkerSupport=match_info["canRequestWorkerSupport"],
            verificationUpdatedAt=match_info.get("verificationUpdatedAt")
        )

@router.get("/opportunities/{opportunity_id}", response_model=OpportunityBeneficiaryResponse)
def get_opportunity(opportunity_id: str):
    with get_db() as conn:
        opp = OpportunityService.get_opportunity(conn, opportunity_id)
        if not opp or opp['status'] not in ['ACTIVE', 'FULL']:
            raise HTTPException(status_code=404, detail="Opportunity not found")
        
        # Read-time expiry check
        expires_at_str = opp.get("verification_expires_at")
        if expires_at_str:
            try:
                exp_dt = datetime.fromisoformat(str(expires_at_str).replace("Z", "+00:00"))
                if exp_dt <= datetime.now(timezone.utc):
                    raise HTTPException(status_code=404, detail="Opportunity not found or expired")
            except HTTPException:
                raise
            except Exception:
                raise HTTPException(status_code=404, detail="Opportunity not found or expired")
                
        return opp

