from typing import Dict, Any, List, Optional
from app.ai_layers.layer1_intake.prompts import INTERVIEW_QUESTIONS
from app.ai_layers.layer1_intake.speech_adapter import SpeechAdapter

class DialogueManager:
    """Manages interview conversational turns and transitions."""

    @staticmethod
    def get_initial_turn(language: str = "hi") -> Dict[str, Any]:
        q0 = INTERVIEW_QUESTIONS[0]
        question_text = q0["hi"] if language == "hi" else q0["en"]
        return {
            "question_index": 0,
            "field": q0["field"],
            "question": question_text,
            "is_final": False
        }

    @staticmethod
    def process_turn(
        current_index: int,
        user_utterance: str,
        transcript_history: List[Dict[str, str]],
        language: str = "hi"
    ) -> Dict[str, Any]:
        # Record user utterance
        transcript_history.append({"speaker": "user", "text": user_utterance})

        next_index = current_index + 1
        if next_index >= len(INTERVIEW_QUESTIONS):
            closing_text = "धन्यवाद! हमने आपकी सभी बातें समझ ली हैं। अब हम आपके लिए सबसे उपयुक्त अवसरों का विश्लेषण कर रहे हैं।" if language == "hi" else "Thank you! We have recorded your responses and are now finding your best matches."
            return {
                "question_index": next_index,
                "field": "completed",
                "question": closing_text,
                "is_final": True
            }

        next_q = INTERVIEW_QUESTIONS[next_index]
        question_text = next_q["hi"] if language == "hi" else next_q["en"]
        transcript_history.append({"speaker": "ai", "text": question_text})

        return {
            "question_index": next_index,
            "field": next_q["field"],
            "question": question_text,
            "is_final": False
        }
