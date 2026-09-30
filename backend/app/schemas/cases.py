from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class CaseNoteCreate(BaseModel):
    note_text: str
    note_type: str = Field(default="GENERAL") # GENERAL, COUNSELLING, VERIFICATION, CONTACT_ATTEMPT, REFERRAL, OUTCOME, ESCALATION
    visibility: str = Field(default="STAFF_ONLY") # STAFF_ONLY, BENEFICIARY_SAFE

class CaseNoteResponse(BaseModel):
    id: str
    case_id: str
    author_user_id: str
    note_text: str
    note_type: str
    visibility: str
    created_at: datetime
    updated_at: Optional[datetime] = None

class BeneficiaryNoteResponse(BaseModel):
    id: str
    note_text: str
    note_type: str
    created_at: datetime

class CaseAssignRequest(BaseModel):
    worker_id: str
    assignment_reason: Optional[str] = None

class CaseFollowUpRequest(BaseModel):
    next_follow_up_at: datetime
    note: Optional[str] = None

class CasePriorityUpdateRequest(BaseModel):
    priority: str # LOW, NORMAL, HIGH, URGENT

class CaseResponse(BaseModel):
    id: str
    beneficiary_id: str
    district_id: str
    block_id: Optional[str] = None
    assigned_worker_id: Optional[str] = None
    case_status: str
    priority: str
    intake_source: str
    latest_recommendation_id: Optional[str] = None
    latest_referral_id: Optional[str] = None
    next_follow_up_at: Optional[datetime] = None
    last_contacted_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    closed_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class BeneficiaryCaseResponse(BaseModel):
    id: str
    case_status: str
    display_status: str
    next_step: str
    next_follow_up_at: Optional[datetime] = None
    can_request_support: bool = True
