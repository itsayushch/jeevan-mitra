import traceback
from typing import Dict, Any
from app.services.interfaces import IAIEngine, ExtractionResult, MatchingResult
from app.utils.logger import logger
from app.ai_layers.layer2_extraction.extraction_engine import extract_entities
from app.ai_layers.layer3_matching.matching_engine import rank_opportunities
from app.ai_layers.layer5_planning.narrative_engine import generate_brief_narrative

class AIOrchestrator(IAIEngine):
    def extract_profile(self, transcript: str) -> ExtractionResult:
        try:
            res = extract_entities(transcript)
            return ExtractionResult(
                profile=res.get("profile", {}),
                confidence_scores=res.get("confidence", {}),
                read_back_script=res.get("read_back", "")
            )
        except Exception as e:
            logger.error(f"AI Extraction failed: {e}\n{traceback.format_exc()}")
            # Fallback
            return ExtractionResult(
                profile={}, confidence_scores={}, read_back_script="Could not extract details. Please speak to an agent."
            )

    def generate_recommendations(self, profile: Dict[str, Any], district: str) -> MatchingResult:
        try:
            recs = rank_opportunities(profile, district)
            return MatchingResult(recommendations=recs)
        except Exception as e:
            logger.error(f"AI Matching failed: {e}\n{traceback.format_exc()}")
            return MatchingResult(recommendations=[])

    def generate_planning_brief(self, district: str) -> str:
        try:
            return generate_brief_narrative(district, {})
        except Exception as e:
            logger.error(f"AI Planning Narrative failed: {e}\n{traceback.format_exc()}")
            return "Unable to generate planning narrative."

ai_service = AIOrchestrator()
