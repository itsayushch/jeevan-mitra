from typing import Dict, Any, List, Optional, Literal, Union
from pydantic import BaseModel, Field, field_validator
import re

ALLOWED_EDUCATION_LEVELS = [
    "No Formal Education", "Class 5", "Class 8", "Class 10", "Class 12", "ITI / Diploma", "Graduate", "Post Graduate"
]

ALLOWED_WORK_PREFERENCES = ["wage", "self_employment", "both"]

def education_to_rank(edu_str: str) -> int:
    s = str(edu_str).lower()
    grade = re.fullmatch(r'\s*(?:class|grade)\s*(\d{1,2})\s*', s)
    if grade:
        completed = int(grade.group(1))
        return 4 if completed >= 12 else 3 if completed >= 10 else 2 if completed >= 8 else 1 if completed >= 5 else 0
    if 'post' in s or 'master' in s or 'phd' in s:
        return 6
    if 'degree' in s or 'graduate' in s or 'ba' in s or 'bsc' in s or 'bcom' in s or 'btech' in s:
        return 5
    if '12' in s or 'inter' in s or 'higher' in s or 'iti' in s or 'diploma' in s:
        return 4
    if '10' in s or 'matric' in s:
        return 3
    if '8' in s or 'middle' in s:
        return 2
    if '5' in s or 'primary' in s:
        return 1
    return 0

class ExtractedFieldDetail(BaseModel):
    value: Any
    confidence: float = Field(ge=0.0, le=1.0)
    source: Literal['ai_inferred', 'user', 'counselor', 'system'] = "ai_inferred"
    confirmed: bool = False

class SafeProfileExtractionOutput(BaseModel):
    district: Optional[str] = Field(default="Moradabad", max_length=100)
    block: Optional[str] = Field(default="Chhajlet", max_length=100)
    language: Optional[str] = Field(default="hi", max_length=10)
    education: Optional[str] = Field(default="Class 8", max_length=50)
    current_work: Optional[str] = Field(default="Daily Wage / Farming", max_length=150)
    traditional_or_existing_skills: List[str] = Field(default_factory=list, max_length=10)
    interests: List[str] = Field(default_factory=list, max_length=10)
    mobility: Optional[Union[float, str]] = Field(default=5.0)
    access_needs: Optional[str] = Field(default="None", max_length=200)
    employment_preference: Optional[Literal['wage', 'self_employment', 'both']] = "both"
    self_employment_or_wage_preference: Optional[Literal['wage', 'self_employment', 'both']] = "both"
    confidence_scores: Dict[str, float] = Field(default_factory=dict)
    clarification_needed: Optional[str] = None

    @field_validator("traditional_or_existing_skills", "interests", mode="before")
    def clean_string_list(cls, v):
        if isinstance(v, str):
            v = [item.strip() for item in re.split(r'[,;\n]', v) if item.strip()]
        if isinstance(v, list):
            # Limit string lengths and sanitize
            return [str(item)[:80] for item in v[:10]]
        return []

    @field_validator("access_needs", "current_work", mode="before")
    def truncate_strings(cls, v):
        if v:
            return str(v)[:200]
        return v
