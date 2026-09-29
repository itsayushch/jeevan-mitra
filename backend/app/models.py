from enum import Enum
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union, Literal
from datetime import datetime

# ============================================================================
# 1. Consent Models (A1)
# ============================================================================
class ConsentCreate(BaseModel):
    beneficiary_id: str
    purpose: str
    notice_version: Optional[str] = "1.0"
    audio_consent_recorded: Optional[bool] = True
    voice_retention_choice: Optional[str] = "do_not_keep"
    dpdp_affirmative_consent: Optional[bool] = True

class ConsentRecordCreate(BaseModel):
    session_id: Optional[str] = None
    beneficiary_id: Optional[str] = None
    consent_type: Literal['ai_processing', 'profile_storage', 'counselor_referral', 'analytics', 'export_summary', 'dpdp_general']
    policy_version: Optional[str] = "1.0"
    user_language: Optional[str] = "hi"
    capture_channel: Optional[str] = "web_app"
    granted: Optional[bool] = True

class ConsentRevokeRequest(BaseModel):
    reason: Optional[str] = "User requested revocation"

class ConsentRecordResponse(BaseModel):
    id: str
    session_id: Optional[str] = None
    beneficiary_id: Optional[str] = None
    consent_type: str
    policy_version: str
    status: str
    revoked_at: Optional[str] = None
    revocation_reason: Optional[str] = None
    user_language: str
    capture_channel: str
    timestamp: str

# ============================================================================
# 2. Anonymous Session & Beneficiary Lifecycle Models (A2)
# ============================================================================
class AnonymousSessionCreate(BaseModel):
    owner_type: Optional[Literal['anonymous', 'authenticated_user', 'counselor_assisted']] = "anonymous"
    owner_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class AnonymousSessionResponse(BaseModel):
    session_id: str
    session_token: str
    owner_type: str
    owner_id: Optional[str] = None
    expires_at: str
    created_at: str

class BeneficiaryCreate(BaseModel):
    name: str
    phone: Optional[str] = None
    gender: Optional[str] = "prefer_not_to_say"
    age: Optional[int] = None
    category: Optional[str] = "SC"
    preferred_language: Optional[str] = "hi"
    district: str
    block: str
    village: Optional[str] = None
    contact_preference: Optional[str] = "voice"
    owner_type: Optional[str] = "authenticated_user"
    owner_id: Optional[str] = None

class BeneficiaryUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[int] = None
    preferred_language: Optional[str] = None
    district: Optional[str] = None
    block: Optional[str] = None
    village: Optional[str] = None
    contact_preference: Optional[str] = None
    owner_type: Optional[str] = None
    owner_id: Optional[str] = None

# ============================================================================
# 3. Interview State & Field-Provenance Models (A3)
# ============================================================================
class InterviewStartRequest(BaseModel):
    beneficiary_id: Optional[str] = None
    session_id: Optional[str] = None
    channel: Optional[str] = "web_app"
    language: Optional[str] = "hi"

class InterviewTurnRequest(BaseModel):
    session_id: Optional[str] = None
    interview_id: Optional[str] = None
    audio_input_base64: Optional[str] = None
    text_input: Optional[str] = None
    message: Optional[str] = None
    language: Optional[str] = "hi"

class InterviewFieldUpdateRequest(BaseModel):
    value: Any
    source: Optional[Literal['user', 'counselor', 'system']] = "user"

class ConfirmProfileRequest(BaseModel):
    session_id: Optional[str] = None
    interview_id: Optional[str] = None
    beneficiary_id: Optional[str] = None
    confirmed_fields: Dict[str, Any]

# ============================================================================
# 4. Verified Catalog Models (A4)
# ============================================================================
class QualificationCreate(BaseModel):
    nqr_code: str = Field(min_length=3, max_length=50)
    title: str = Field(min_length=3, max_length=200)
    sector: str = Field(min_length=2, max_length=100)
    nsqf_level: int = Field(ge=1, le=10)
    duration_hours: int = Field(ge=10, le=2000)
    min_education: str
    min_education_rank: int = Field(ge=0, le=5)
    work_type: Literal['wage', 'self_employment', 'both']
    physical_intensity: Optional[Literal['light', 'medium', 'medium_high', 'high']] = "light"
    skills_acquired: List[str] = Field(min_length=1)
    curriculum_summary: str = Field(min_length=10)
    entry_criteria: str = Field(min_length=5)
    certification_body: str = Field(min_length=3)
    official_source_url: str = Field(min_length=5)
    verification_status: Optional[Literal['verified', 'pending', 'deprecated']] = "verified"
    verification_date: Optional[str] = None

class QualificationUpdate(BaseModel):
    title: Optional[str] = None
    sector: Optional[str] = None
    nsqf_level: Optional[int] = None
    duration_hours: Optional[int] = None
    min_education: Optional[str] = None
    min_education_rank: Optional[int] = None
    work_type: Optional[Literal['wage', 'self_employment', 'both']] = None
    physical_intensity: Optional[Literal['light', 'medium', 'medium_high', 'high']] = None
    skills_acquired: Optional[List[str]] = None
    curriculum_summary: Optional[str] = None
    entry_criteria: Optional[str] = None
    certification_body: Optional[str] = None
    official_source_url: Optional[str] = None
    verification_status: Optional[Literal['verified', 'pending', 'deprecated']] = None

class OpportunityCreate(BaseModel):
    qualification_id: str
    centre_or_employer_name: str = Field(min_length=3, max_length=200)
    type: Optional[Literal['training_centre', 'employer_apprenticeship', 'enterprise_cluster', 'job', 'self_employment_support', 'other']] = "training_centre"
    district: str = Field(min_length=2, max_length=100)
    block: str = Field(min_length=2, max_length=100)
    state: Optional[str] = "Uttar Pradesh"
    address: str = Field(min_length=5, max_length=300)
    latitude: float = Field(ge=-90.0, le=90.0)
    longitude: float = Field(ge=-180.0, le=180.0)
    batch_start_date: str
    batch_end_date: str
    total_seats: Optional[int] = Field(default=30, ge=1)
    available_seats: Optional[int] = Field(default=15, ge=0)
    sc_reserved_seats: Optional[int] = Field(default=10, ge=0)
    batch_status: Optional[Literal['active', 'upcoming', 'full', 'completed', 'cancelled']] = "active"
    availability: Optional[Literal['verified_open', 'unknown', 'expired', 'closed']] = "verified_open"
    hostel_available: Optional[bool] = False
    stipend_amount_inr: Optional[int] = Field(default=0, ge=0)
    free_toolkit_provided: Optional[bool] = True
    source_url: Optional[str] = None
    contact_details: Optional[str] = None

class OpportunityUpdate(BaseModel):
    centre_or_employer_name: Optional[str] = None
    type: Optional[Literal['training_centre', 'employer_apprenticeship', 'enterprise_cluster', 'job', 'self_employment_support', 'other']] = None
    district: Optional[str] = None
    block: Optional[str] = None
    state: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    batch_start_date: Optional[str] = None
    batch_end_date: Optional[str] = None
    total_seats: Optional[int] = None
    available_seats: Optional[int] = None
    sc_reserved_seats: Optional[int] = None
    batch_status: Optional[Literal['active', 'upcoming', 'full', 'completed', 'cancelled']] = None
    availability: Optional[Literal['verified_open', 'unknown', 'expired', 'closed']] = None
    hostel_available: Optional[bool] = None
    stipend_amount_inr: Optional[int] = None
    free_toolkit_provided: Optional[bool] = None
    source_url: Optional[str] = None
    contact_details: Optional[str] = None

# ============================================================================
# 5. Recommendation Models (A5)
# ============================================================================
class RecommendationMatchRequest(BaseModel):
    beneficiaryId: Optional[str] = None
    sessionId: Optional[str] = None
    interview_id: Optional[str] = None
    district: str = "Moradabad"
    block: str = "Chhajlet"
    educationLevel: str = "Class 8"
    interests: List[str] = []
    skills: List[str] = []
    mobilityRadiusKm: float = 5.0
    accessibilityNeeds: Optional[str] = ""
    workPreference: Optional[str] = "both" # wage, self_employment, both
    preferredLanguage: Optional[str] = "hi"
    do_not_recommend: Optional[List[str]] = None

class GenerateRecommendationsRequest(BaseModel):
    interview_id: Optional[str] = None
    session_id: Optional[str] = None
    beneficiary_id: Optional[str] = None
    district: Optional[str] = None
    block: Optional[str] = None
    mobility_radius_km: Optional[float] = 5.0
    work_preference: Optional[str] = None
    language: Optional[str] = "hi"
    do_not_recommend: Optional[List[str]] = None

# ============================================================================
# 6. Counselor Referral Models (A7)
# ============================================================================
class CreateReferralRequest(BaseModel):
    beneficiary_id: Optional[str] = None
    interview_id: Optional[str] = None
    recommendation_id: Optional[str] = None
    local_opportunity_id: Optional[str] = None
    referral_reason: Literal[
        'no_verified_local_option',
        'user_requested_human_help',
        'accessibility_support_required',
        'complex_eligibility_query',
        'low_confidence_profile',
        'technical_issue'
    ]
    priority: Optional[Literal['low', 'medium', 'high', 'urgent']] = "medium"
    notes: Optional[str] = None

class AssignCounselorRequest(BaseModel):
    counselor_id: str

class UpdateReferralStatusRequest(BaseModel):
    status: Literal['new', 'assigned', 'contacted', 'in_progress', 'resolved', 'closed']
    outcome: Optional[str] = None
    notes: Optional[str] = None

class AddCounselorNoteRequest(BaseModel):
    note: str = Field(min_length=1, max_length=2000)
    counselor_id: Optional[str] = None

# ============================================================================
# 7. Summary Export Models (A8)
# ============================================================================
class ExportSummaryRequest(BaseModel):
    include_contact_info: Optional[bool] = False

# ============================================================================
# 8. Worker Models (Legacy support)
# ============================================================================
class ProfileCorrectionRequest(BaseModel):
    field_name: str
    field_value: Any
    correction_reason: Optional[str] = None

class BatchVerificationRequest(BaseModel):
    available_seats: int = Field(ge=0)
    batch_status: Literal['active', 'upcoming', 'full', 'completed', 'cancelled']
    notes: str = Field(min_length=1, max_length=2000)

class ApproveReferralRequest(BaseModel):
    recommendation_id: str
    local_opportunity_id: str
    caste_document_verified: bool
    income_criteria_verified: bool
    residence_proof_verified: bool
    notes: Optional[str] = None

# ============================================================================
# 9. Planning Brief & Chat Models
# ============================================================================
class GenerateBriefRequest(BaseModel):
    district: str
    period: str

class SignOffRequest(BaseModel):
    officer_name: str
    notes: Optional[str] = None

class ChatRequest(BaseModel):
    message: str
    beneficiary_id: Optional[str] = None
    language: Optional[str] = "hi"
# ============================================================================
# 10. Journey Models
# ============================================================================
class JourneyState(str, Enum):
    CREATED = 'created'
    AWAITING_CONSENT = 'awaiting_consent'
    COLLECTING_PROFILE = 'collecting_profile'
    CLARIFICATION_REQUIRED = 'clarification_required'
    PROFILE_REVIEW = 'profile_review'
    READY_FOR_RECOMMENDATIONS = 'ready_for_recommendations'
    RECOMMENDATIONS_READY = 'recommendations_ready'
    REFERRAL_REQUESTED = 'referral_requested'
    COMPLETED = 'completed'
    DELETED = 'deleted'

class JourneyResponse(BaseModel):
    id: str
    session_id: str
    actor_id: Optional[str] = None
    actor_role: Optional[str] = None
    state: JourneyState
    ai_processing_consent: bool
    storage_consent: bool
    referral_consent: bool
    profile_confirmed: bool
    created_at: str
    updated_at: str

class JourneyStartRequest(BaseModel):
    actor_id: Optional[str] = None
    actor_role: Optional[str] = None

class JourneyConsentRequest(BaseModel):
    ai_processing_consent: bool = False
    storage_consent: bool = False
    referral_consent: bool = False

class JourneyRespondRequest(BaseModel):
    message: str
    language: Optional[str] = "hi"

class JourneyConfirmProfileRequest(BaseModel):
    confirm: bool

