"""Authenticated speech adapters; audio is processed in memory, never stored."""
import base64
import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field
from typing import Literal
from app.config import settings
from app.dependencies.auth import Actor, get_current_actor
from app.dependencies.consent import verify_consent
from app.database import get_db
from fastapi.responses import StreamingResponse

router = APIRouter(prefix='/voice', tags=['Voice'])
Language = Literal['hi', 'en']
MAX_AUDIO = 4 * 1024 * 1024


def require_voice_consent(actor: Actor):
    if not actor.session_id and not actor.beneficiary_id:
        raise HTTPException(401, 'Start a session before using voice.')
    with get_db() as conn:
        verify_consent(conn, 'ai_processing', actor.beneficiary_id, actor.session_id)


@router.post('/transcribe')
async def transcribe(request: Request, language: Language = 'hi', actor: Actor = Depends(get_current_actor)):
    require_voice_consent(actor)
    if not settings.GROQ_API_KEY:
        raise HTTPException(503, 'Speech recognition is not configured.')
    mime = request.headers.get('content-type', '').split(';')[0]
    extensions = {'audio/webm': 'webm', 'audio/mp4': 'm4a', 'audio/ogg': 'ogg', 'audio/wav': 'wav'}
    if mime not in extensions:
        raise HTTPException(415, 'Unsupported audio format.')
    audio = bytearray()
    async for chunk in request.stream():
        audio.extend(chunk)
        if len(audio) > MAX_AUDIO:
            raise HTTPException(413, 'Please speak in shorter turns.')
    if len(audio) < 100:
        raise HTTPException(422, 'No audio was recorded.')
    return {'text': await recognize_audio(bytes(audio), mime, extensions[mime], language)}


async def recognize_audio(audio: bytes, mime: str, extension: str, language: str) -> str:
    if not settings.GROQ_API_KEY:
        raise HTTPException(503, 'Speech recognition is not configured.')
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            result = await client.post('https://api.groq.com/openai/v1/audio/transcriptions',
                headers={'Authorization': f'Bearer {settings.GROQ_API_KEY}'},
                files={'file': (f'turn.{extension}', audio, mime)},
                data={'model': settings.GROQ_STT_MODEL, 'language': language, 'response_format': 'verbose_json'})
            result.raise_for_status()
            payload = result.json()
        segments = payload.get('segments', [])
        if segments and all(s.get('no_speech_prob', 0) > 0.8 for s in segments):
            raise HTTPException(422, 'No clear speech was detected. Please repeat.')
        text = payload.get('text', '').strip()
        if not text:
            raise HTTPException(422, 'No clear speech was detected. Please repeat.')
        return text[:4000]
    except (httpx.HTTPError, ValueError, KeyError) as exc:
        raise HTTPException(503, 'Speech recognition is temporarily unavailable.') from exc


class SpeechRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2400)
    language: Language = 'hi'
    slow: bool = False


async def neural_speech(data: SpeechRequest):
    """Stream MPEG frames as soon as the cloud voice produces them."""
    import edge_tts
    voice = settings.VOICE_HI_VOICE if data.language == 'hi' else settings.VOICE_EN_VOICE
    async for chunk in edge_tts.Communicate(data.text, voice, rate='-20%' if data.slow else '+0%',
                                           connect_timeout=8, receive_timeout=12).stream():
        if chunk['type'] == 'audio':
            yield chunk['data']


@router.get('/notice')
async def voice_notice(language: Language = 'hi'):
    # Fixed public notice: no arbitrary input, credentials or personal data sent.
    text = ('शुरू करने पर आवाज़ का AI द्वारा उपयोग और उत्तर सुरक्षित रखने की अनुमति मिलती है। '
            'ऐप ऑडियो सुरक्षित नहीं रखता। सलाहकार से साझा करने के लिए अलग अनुमति ली जाएगी।'
            if language == 'hi' else
            'Starting gives permission to process your speech with AI and store your answers for guidance. '
            'Your audio is not saved by this app. Sharing with a counselor requires separate permission.')
    return StreamingResponse(neural_speech(SpeechRequest(text=text, language=language)),
                             media_type='audio/mpeg', headers={'Cache-Control': 'public, max-age=86400'})


@router.post('/speak')
async def speak(data: SpeechRequest, actor: Actor = Depends(get_current_actor)):
    require_voice_consent(actor)
    if settings.VOICE_TTS_PROVIDER == 'edge':
        return StreamingResponse(neural_speech(data), media_type='audio/mpeg', headers={'Cache-Control': 'no-store'})
    if not settings.SARVAM_API_KEY:
        raise HTTPException(503, 'Configure the selected cloud speech provider.')
    try:
        async with httpx.AsyncClient(timeout=25) as client:
            result = await client.post('https://api.sarvam.ai/text-to-speech',
                headers={'api-subscription-key': settings.SARVAM_API_KEY},
                json={'text': data.text, 'language_code': f'{data.language}-IN',
                      'model': settings.SARVAM_TTS_MODEL, 'speaker': settings.SARVAM_TTS_VOICE,
                      'pace': 0.8 if data.slow else 1.0, 'output_audio_codec': 'wav'})
            result.raise_for_status()
        audio = base64.b64decode(result.json()['audios'][0], validate=True)
        return Response(audio, media_type='audio/wav', headers={'Cache-Control': 'no-store'})
    except (httpx.HTTPError, ValueError, KeyError, IndexError) as exc:
        raise HTTPException(503, 'Speech playback is temporarily unavailable.') from exc
