from typing import Protocol, Any, Dict, List
from pydantic import BaseModel

class ExtractionResult(BaseModel):
    profile: Dict[str, Any]
    confidence_scores: Dict[str, float]
    read_back_script: str

class MatchingResult(BaseModel):
    recommendations: List[Dict[str, Any]]

class IAIEngine(Protocol):
    def extract_profile(self, transcript: str) -> ExtractionResult:
        ...
    def generate_recommendations(self, profile: Dict[str, Any], district: str) -> MatchingResult:
        ...
    def generate_planning_brief(self, district: str) -> str:
        ...
