import pytest
from app.ai_layers.layer1_intake.dialogue_manager import DialogueManager
from app.ai_layers.layer2_extraction.extraction_engine import ExtractionEngine
from app.ai_layers.layer2_extraction.validation import SafeProfileExtractionOutput
from pydantic import ValidationError

def test_ai_fallback_guided_mode_when_offline():
    # Simulate AI timeout/offline fallback using DialogueManager
    fallback_turn = DialogueManager.get_fallback_turn(current_index=1, language="en")
    assert fallback_turn["mode"] == "guided_fallback"
    assert "We can continue with a few simple questions" in fallback_turn["question"]

    # Hindi fallback
    fallback_hi = DialogueManager.get_fallback_turn(current_index=1, language="hi")
    assert fallback_hi["mode"] == "guided_fallback"
    assert "हम कुछ सरल सवालों के साथ जारी रख सकते हैं" in fallback_hi["question"]

def test_low_confidence_triggers_clarification_question():
    engine = ExtractionEngine(threshold=0.75)
    # Ambiguous user text with low confidence on education
    ambiguous_transcript = [
        {"speaker": "ai", "text": "What is your education?"},
        {"speaker": "user", "text": "I went to school for a few years maybe"}
    ]
    extracted = engine.extract_profile(ambiguous_transcript)
    assert extracted["clarification_needed"] is not None
    assert "highest completed educational standard" in extracted["clarification_needed"]

def test_safe_validation_bounds_and_sanitizes():
    # Valid model input
    valid_data = {
        "district": "Moradabad",
        "block": "Chhajlet",
        "education": "Class 10",
        "interests": ["Solar PV", "Electronics"],
        "mobility": 5.0,
        "employment_preference": "wage"
    }
    validated = SafeProfileExtractionOutput.model_validate(valid_data)
    assert validated.education == "Class 10"
    assert validated.employment_preference == "wage"

    # Reject invalid enum for employment preference
    with pytest.raises(ValidationError):
        SafeProfileExtractionOutput.model_validate({
            "employment_preference": "guaranteed_government_job"  # Invalid!
        })

def test_ai_inferred_fields_are_never_auto_confirmed():
    engine = ExtractionEngine()
    transcript = [
        {"speaker": "user", "text": "I passed class 10 and do farming"}
    ]
    extracted = engine.extract_profile(transcript)
    assert extracted["education"] == "Class 10"
    # Extraction output does not set confirmed status - confirmation is strictly user-controlled
    assert "user_confirmed" not in extracted or extracted.get("user_confirmed") is False
