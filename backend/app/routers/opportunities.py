from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, List
from app.database import get_db
from app.schemas.opportunities import OpportunityCreate, OpportunityBeneficiaryResponse, OpportunityStaffResponse, EvidenceCreate, VerificationAction, MatchStateResponse, ProviderCreate, ProviderResponse
from app.services.opportunity_service import OpportunityService
from app.services.opportunity_verification_service import OpportunityVerificationService
from app.dependencies.auth import require_authenticated_user, Actor

router = APIRouter(tags=["Opportunities"])

@router.post("/staff/opportunity-providers", status_code=201, response_model=ProviderResponse)
def create_provider(data: ProviderCreate, user: Actor = Depends(require_authenticated_user)):
    with get_db() as conn:
        return OpportunityService.create_provider(conn, data.dict(exclude_unset=True), user.actor_id)

@router.post("/staff/opportunities", status_code=201, response_model=OpportunityStaffResponse)
def create_opportunity(data: OpportunityCreate, user: Actor = Depends(require_authenticated_user)):
    with get_db() as conn:
        return OpportunityService.create_opportunity(conn, data.dict(exclude_unset=True), user.actor_id)

@router.get("/opportunities", response_model=List[OpportunityBeneficiaryResponse])
def list_opportunities():
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM local_opportunities WHERE status = 'ACTIVE'")
        return [dict(row) for row in cursor.fetchall()]

@router.get("/opportunities/{opportunity_id}", response_model=OpportunityBeneficiaryResponse)
def get_opportunity(opportunity_id: str):
    with get_db() as conn:
        opp = OpportunityService.get_opportunity(conn, opportunity_id)
        if not opp or opp['status'] not in ['ACTIVE', 'FULL']:
            raise HTTPException(status_code=404, detail="Opportunity not found")
        return opp

@router.post("/staff/opportunities/{opportunity_id}/evidence", status_code=201)
def add_evidence(opportunity_id: str, data: EvidenceCreate, user: Actor = Depends(require_authenticated_user)):
    with get_db() as conn:
        return OpportunityVerificationService.submit_evidence(conn, opportunity_id, data.dict(exclude_unset=True), user.actor_id)

@router.post("/staff/opportunities/{opportunity_id}/{action}")
def verify_opportunity(opportunity_id: str, action: str, data: VerificationAction, user: Actor = Depends(require_authenticated_user)):
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
        try:
            expires_at = data.verification_expires_at.isoformat() if data.verification_expires_at else None
            return OpportunityVerificationService.transition_status(
                conn, opportunity_id, valid_actions[action], user.actor_id,
                expires_at=expires_at, reason=data.reason
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
