from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class ProviderBase(BaseModel):
    provider_type: str
    name: str
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    address_line: Optional[str] = None
    district_id: Optional[str] = None
    block_id: Optional[str] = None
    pincode: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    status: str = 'ACTIVE'
    source_name: Optional[str] = None
    source_reference: Optional[str] = None

class ProviderCreate(ProviderBase):
    pass

class ProviderResponse(ProviderBase):
    id: str
    created_by_user_id: str
    created_at: datetime
    updated_at: datetime

class OpportunityBase(BaseModel):
    qualification_id: str
    provider_id: str
    opportunity_type: str
    title: str
    summary: str
    district_id: str
    block_id: Optional[str] = None
    location_text: Optional[str] = None
    delivery_mode: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    application_deadline: Optional[datetime] = None
    seats_total: Optional[int] = None
    seats_available: Optional[int] = None
    vacancies_total: Optional[int] = None
    vacancies_available: Optional[int] = None
    stipend_amount: Optional[float] = None
    fee_amount: Optional[float] = None
    travel_support_available: bool = False
    hostel_available: bool = False
    eligibility_notes: Optional[str] = None
    accessibility_notes: Optional[str] = None
    source_url: Optional[str] = None
    status: Optional[str] = 'DRAFT'

class OpportunityCreate(OpportunityBase):
    pass

class OpportunityUpdate(BaseModel):
    title: Optional[str] = None
    summary: Optional[str] = None
    seats_total: Optional[int] = None
    seats_available: Optional[int] = None
    vacancies_total: Optional[int] = None
    vacancies_available: Optional[int] = None
    location_text: Optional[str] = None
    stipend_amount: Optional[float] = None
    travel_support_available: Optional[bool] = None
    hostel_available: Optional[bool] = None

class OpportunityStaffResponse(OpportunityBase):
    id: str
    evidence_summary: Optional[str] = None
    verified_by_user_id: Optional[str] = None
    verified_at: Optional[datetime] = None
    verification_expires_at: Optional[datetime] = None
    created_by_user_id: str
    updated_by_user_id: str
    created_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime] = None
    archived_at: Optional[datetime] = None
    evidence: Optional[List[Dict[str, Any]]] = None
    verification_history: Optional[List[Dict[str, Any]]] = None

class OpportunityBeneficiaryResponse(BaseModel):
    id: str
    opportunity_type: str
    title: str
    summary: str
    district_id: str
    location_text: Optional[str] = None
    delivery_mode: str
    start_date: Optional[datetime] = None
    seats_available: Optional[int] = None
    vacancies_available: Optional[int] = None
    travel_support_available: bool = False
    hostel_available: bool = False
    status: str

class EvidenceCreate(BaseModel):
    evidence_type: str
    storage_key: Optional[str] = None
    external_url: Optional[str] = None
    note: Optional[str] = None
    is_approved: Optional[bool] = False

class VerificationAction(BaseModel):
    action: Optional[str] = None # VERIFIED, REVERIFIED, MARKED_FULL, PAUSED, CLOSED, REJECTED
    reason: Optional[str] = None
    verification_expires_at: Optional[datetime] = None
    metadata_json: Optional[Dict[str, Any]] = None

class MatchStateResponse(BaseModel):
    matchState: str
    beneficiaryMessage: str
    canRequestReferral: bool
    canRequestWorkerSupport: bool
    verificationUpdatedAt: Optional[datetime] = None

from typing import Literal
from app.schemas.locale import SupportedLocale

class OpportunitySubmissionCreate(BaseModel):
    input_mode: Literal["text", "voice"]
    text: str
    locale: Optional[SupportedLocale] = None
    audio_storage_key: Optional[str] = None
    transcript_confidence: Optional[float] = None

class OpportunitySubmissionReview(BaseModel):
    status: Literal["UNDER_REVIEW", "LINKED_TO_OPPORTUNITY", "REJECTED", "CLOSED"]
    linked_opportunity_id: Optional[str] = None
    review_notes: Optional[str] = None

class OpportunitySubmissionResponse(BaseModel):
    id: str
    submitted_by_user_id: Optional[str] = None
    input_mode: str
    raw_text: str
    normalized_text: str
    locale: str
    audio_storage_key: Optional[str] = None
    transcript_confidence: Optional[float] = None
    status: str
    linked_opportunity_id: Optional[str] = None
    reviewed_by_user_id: Optional[str] = None
    review_notes: Optional[str] = None
    created_at: str
    updated_at: str

