from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class QualificationBase(BaseModel):
    external_reference: Optional[str] = None
    title: str
    description: str
    sector: str
    nsqf_level: Optional[float] = None
    duration_hours: Optional[int] = None
    entry_requirements_json: Optional[Dict[str, Any]] = None
    skills_json: Optional[List[str]] = None
    source_name: str
    source_url: Optional[str] = None
    source_version: Optional[str] = None
    source_verified_at: datetime
    verification_status: str

class QualificationCreate(BaseModel):
    external_reference: Optional[str] = None
    title: str
    description: str
    sector: str
    nsqf_level: Optional[float] = None
    duration_hours: Optional[int] = None
    entry_requirements_json: Optional[Dict[str, Any]] = None
    skills_json: Optional[List[str]] = None
    source_name: str
    source_url: Optional[str] = None
    source_version: Optional[str] = None
    source_verified_at: datetime

class QualificationResponse(QualificationBase):
    id: str
    created_at: datetime
    updated_at: datetime

    # Internal fields staff might see
    created_by_user_id: Optional[str] = None
    verified_by_user_id: Optional[str] = None
    verified_at: Optional[datetime] = None
    archived_at: Optional[datetime] = None

class QualificationBeneficiaryResponse(BaseModel):
    # Safe subset for beneficiaries
    id: str
    title: str
    description: str
    sector: str
    nsqf_level: Optional[float] = None
    duration_hours: Optional[int] = None
    entry_requirements_json: Optional[Dict[str, Any]] = None
    skills_json: Optional[List[str]] = None
    source_name: str
    verification_status: str

class QualificationUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    verification_status: Optional[str] = None
