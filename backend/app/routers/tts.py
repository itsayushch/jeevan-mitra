import io
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
import edge_tts
import logging

router = APIRouter(prefix="/tts")
logger = logging.getLogger(__name__)

@router.get("/generate")
async def generate_tts(text: str = Query(...), lang: str = Query("hi")):
    """
    Generate ultra-realistic TTS using Edge TTS.
    """
    try:
        # Select best neural voices for Hindi and English
        voice = "hi-IN-SwaraNeural" if lang == "hi" else "en-IN-NeerjaExpressiveNeural"

        communicate = edge_tts.Communicate(text, voice)

        async def audio_stream():
            try:
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        yield chunk["data"]
            except Exception as e:
                logger.error(f"Error streaming TTS: {e}")

        return StreamingResponse(audio_stream(), media_type="audio/mpeg")
    except Exception as e:
        logger.error(f"TTS Error: {e}")
        raise HTTPException(status_code=500, detail="TTS generation failed")
