from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime

# --- Beneficiary Models ---
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

# --- Consent Models ---
class ConsentCreate(BaseModel):
    beneficiary_id: str
    purpose: str
    notice_version: Optional[str] = "1.0"
    audio_consent_recorded: Optional[bool] = True
    voice_retention_choice: Optional[str] = "do_not_keep"
    dpdp_affirmative_consent: Optional[bool] = True

# --- Interview Models ---
class InterviewStartRequest(BaseModel):
    beneficiary_id: str
    channel: Optional[str] = "web_app"
    language: Optional[str] = "hi"

class InterviewTurnRequest(BaseModel):
    session_id: str
    audio_input_base64: Optional[str] = None
    text_input: Optional[str] = None
    language: Optional[str] = "hi"

class ConfirmProfileRequest(BaseModel):
    session_id: str
    beneficiary_id: str
    confirmed_fields: Dict[str, Any]

# --- Recommendation Models ---
class RecommendationMatchRequest(BaseModel):
    beneficiaryId: str
    sessionId: Optional[str] = None
    district: str
    block: str
    educationLevel: str
    interests: List[str] = []
    skills: List[str] = []
    mobilityRadiusKm: float = 5.0
    accessibilityNeeds: Optional[str] = ""
    workPreference: Optional[str] = "both" # wage, self_employment, both
    preferredLanguage: Optional[str] = "hi"

# --- Worker Models ---
class ProfileCorrectionRequest(BaseModel):
    field_name: str
    field_value: Any
    correction_reason: Optional[str] = None

class BatchVerificationRequest(BaseModel):
    opportunity_id: str
    available_seats: int
    batch_status: str
    notes: Optional[str] = None

class ApproveReferralRequest(BaseModel):
    recommendation_id: str
    local_opportunity_id: str
    assigned_worker_id: str
    caste_document_verified: bool = True
    income_criteria_verified: bool = True
    residence_proof_verified: bool = True
    notes: Optional[str] = None

# --- Planning Brief Models ---
class GenerateBriefRequest(BaseModel):
    district: str
    period: str

class SignOffRequest(BaseModel):
    officer_name: str
    notes: Optional[str] = None

# --- Chat Models ---
class ChatRequest(BaseModel):
    message: str
    beneficiary_id: Optional[str] = None
    language: Optional[str] = "hi"
