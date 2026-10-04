from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class ReferralCreate(BaseModel):
    recommendationId: str
    note: Optional[str] = None

class ReferralTransitionRequest(BaseModel):
    to_status: str
    reason: Optional[str] = None
    note: Optional[str] = None

class ContactAttemptCreate(BaseModel):
    channel: str # PHONE, SMS, WHATSAPP, EMAIL, IN_PERSON, OTHER
    attempt_outcome: str # CONNECTED, NO_ANSWER, INVALID_CONTACT, CALLBACK_REQUESTED, MESSAGE_SENT, BENEFICIARY_DECLINED, OTHER
    summary: Optional[str] = None
    next_follow_up_at: Optional[datetime] = None

class ReferralFollowUpRequest(BaseModel):
    next_follow_up_at: datetime
    note: Optional[str] = None

class OutcomeCreate(BaseModel):
    outcome_type: str # ENROLMENT, TRAINING_START, TRAINING_COMPLETION, WAGE_EMPLOYMENT, SELF_EMPLOYMENT, ENTERPRISE_STARTED, DROPPED_OUT, OTHER
    occurred_at: Optional[datetime] = None
    evidence_summary: Optional[str] = None

class OutcomeVerifyRequest(BaseModel):
    outcome_status: str # VERIFIED, REJECTED, PENDING_VERIFICATION
    evidence_summary: Optional[str] = None

class ReferralStaffResponse(BaseModel):
    id: str
    case_id: Optional[str] = None
    beneficiary_id: str
    recommendation_id: str
    qualification_id: Optional[str] = None
    local_opportunity_id: str
    provider_id: Optional[str] = None
    created_by_worker_id: Optional[str] = None
    assigned_worker_id: Optional[str] = None
    referral_status: str
    referral_reason: Optional[str] = None
    beneficiary_consent_confirmed_at: Optional[datetime] = None
    eligibility_snapshot_json: Optional[Dict[str, Any]] = None
    referred_at: Optional[datetime] = None
    next_follow_up_at: Optional[datetime] = None
    last_contact_attempt_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    closure_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class BeneficiaryReferralResponse(BaseModel):
    referralId: str
    status: str
    displayStatus: str
    nextStep: str
    nextFollowUpAt: Optional[str] = None
    canRequestSupport: bool = True

class ReferralStatusHistoryResponse(BaseModel):
    id: str
    referral_id: str
    previous_status: Optional[str] = None
    new_status: str
    actor_user_id: str
    reason: Optional[str] = None
    note: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None
    created_at: datetime

class ContactAttemptResponse(BaseModel):
    id: str
    referral_id: str
    actor_user_id: str
    channel: str
    attempt_outcome: str
    summary: Optional[str] = None
    attempted_at: datetime
    next_follow_up_at: Optional[datetime] = None

class OutcomeResponse(BaseModel):
    id: str
    referral_id: str
    outcome_type: str
    outcome_status: str
    occurred_at: Optional[datetime] = None
    recorded_by_user_id: str
    verified_by_user_id: Optional[str] = None
    evidence_summary: Optional[str] = None
    follow_up_due_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
