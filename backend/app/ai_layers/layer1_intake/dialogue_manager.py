from typing import Dict, Any, List, Optional
from app.ai_layers.layer1_intake.prompts import INTERVIEW_QUESTIONS
from app.ai_layers.layer1_intake.speech_adapter import SpeechAdapter

class DialogueManager:
    """Manages interview conversational turns, fallback guided questions, and transitions."""

    @staticmethod
    def get_initial_turn(language: str = "hi", mode: str = "standard") -> Dict[str, Any]:
        question_text = "आप किस जिले में रहते हैं?" if language == "hi" else "Which district do you live in?"
        return {
            "question_index": 0,
            "field": "district",
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
        transcript_history.append({"speaker": "user", "text": user_utterance})

        demo_script_hi = [
            "Shukriya. Aap apni padhai aur kaam ke anubhav ke baare mein kuch batayenge?",
            "Accha. Aapki computer aur technical skills kaisi hain? Aur aap kis field mein aage badhna chahte hain?",
            "Ye bahut badhiya hai. Ek aakhiri sawal, aap naukri karna pasand karenge ya apna khud ka business shuru karna?",
            "Dhanyawad! Maine aapki jankari record kar li hai. Ab main aapke liye best courses aur jobs dhoondh raha hoon. Kripya apne profile ko confirm karein."
        ]

        demo_script_en = [
            "Thank you. Could you tell me a bit about your education and work experience?",
            "I see. How comfortable are you with computers and technology? And what field are you interested in?",
            "That's great. One last question, are you looking for a job or do you want to start your own business?",
            "Thank you! I have recorded your information. I am now looking for the best courses and jobs for you. Please confirm your profile."
        ]

        script = demo_script_hi if language == "hi" else demo_script_en

        next_index = current_index + 1
        is_final = next_index > len(script)

        if is_final:
            closing_text = script[-1]
            return {
                "question_index": next_index,
                "field": "completed",
                "question": closing_text,
                "mode": "standard",
                "is_final": True
            }
        else:
            return {
                "question_index": next_index,
                "field": "demo_field",
                "question": script[next_index - 1],
                "mode": "standard",
                "is_final": False
            }
