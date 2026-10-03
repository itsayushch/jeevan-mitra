import json
from typing import Dict, Any, Optional
from app.config import settings
from app.utils.logger import logger

class SpeechAdapter:
    """Adapts voice speech audio to text and text to speech audio."""

    @staticmethod
    def transcribe(audio_base64: Optional[str] = None, text_input: Optional[str] = None, lang: str = "hi") -> str:
        if text_input and text_input.strip():
            return text_input.strip()

        if audio_base64:
            from fastapi import HTTPException
            raise HTTPException(422, "Use /voice/transcribe to transcribe real audio before submitting a turn.")

        return ""

    @staticmethod
    def synthesize_speech_url(text: str, lang: str = "hi") -> Optional[str]:
        # Return none or mock audio link when using Web Speech API client-side
        return None
