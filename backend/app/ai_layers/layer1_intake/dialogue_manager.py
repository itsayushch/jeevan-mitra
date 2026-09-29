from typing import Dict, Any, List, Optional
from app.ai_layers.layer1_intake.prompts import INTERVIEW_QUESTIONS
from app.ai_layers.layer1_intake.speech_adapter import SpeechAdapter

class DialogueManager:
    """Manages interview conversational turns, fallback guided questions, and transitions."""

    @staticmethod
    def get_initial_turn(language: str = "hi", mode: str = "standard") -> Dict[str, Any]:
        q0 = INTERVIEW_QUESTIONS[0]
        question_text = q0["hi"] if language == "hi" else q0["en"]
        return {
            "question_index": 0,
            "field": q0["field"],
            "question": question_text,
            "mode": mode,
            "is_final": False
        }

    @staticmethod
    def get_fallback_turn(current_index: int, language: str = "hi") -> Dict[str, Any]:
        """Provides deterministic guided fallback turn when AI is unavailable or low-confidence."""
        idx = min(current_index, len(INTERVIEW_QUESTIONS) - 1)
        q = INTERVIEW_QUESTIONS[idx]
        prefix = "हम कुछ सरल सवालों के साथ जारी रख सकते हैं: " if language == "hi" else "We can continue with a few simple questions: "
        question_text = prefix + (q["hi"] if language == "hi" else q["en"])
        return {
            "question_index": idx,
            "field": q["field"],
            "question": question_text,
            "mode": "guided_fallback",
            "is_final": False
        }

    @staticmethod
    def process_turn(
        current_index: int,
        user_utterance: str,
        transcript_history: List[Dict[str, str]],
        language: str = "hi",
        clarification_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        # Record user utterance
        transcript_history.append({"speaker": "user", "text": user_utterance})

        # If low-confidence clarification was requested
        if clarification_prompt:
            transcript_history.append({"speaker": "ai", "text": clarification_prompt})
            return {
                "question_index": current_index,
                "field": "clarification",
                "question": clarification_prompt,
                "mode": "clarification",
                "is_final": False
            }

        next_index = current_index + 1
        if next_index >= len(INTERVIEW_QUESTIONS):
            closing_text = (
                "धन्यवाद! हमने आपकी सभी बातें समझ ली हैं। कृपया अपनी प्रोफ़ाइल की पुष्टि करें ताकि हम उपयुक्त अवसरों से मिलान कर सकें।"
                if language == "hi"
                else "Thank you! We have recorded your responses. Please review and confirm your profile summary before recommendation matching."
            )
            return {
                "question_index": next_index,
                "field": "completed",
                "question": closing_text,
                "mode": "standard",
                "is_final": True
            }

        next_q = INTERVIEW_QUESTIONS[next_index]
        question_text = next_q["hi"] if language == "hi" else next_q["en"]
        transcript_history.append({"speaker": "ai", "text": question_text})

        return {
            "question_index": next_index,
            "field": next_q["field"],
            "question": question_text,
            "mode": "standard",
            "is_final": False
        }
