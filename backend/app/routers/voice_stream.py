"""Cloud adaptation of RealtimeVoiceChat's cancellable WebSocket audio pipeline.

Each connection owns its input buffer and tasks. Audio never reaches disk.
Authentication is in the first frame, rather than in a logged URL.
"""
import asyncio
import io
import json
import struct
import wave
from contextlib import suppress
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import ValidationError
from app.config import settings
from app.dependencies.auth import get_current_actor
from app.routers.voice import MAX_AUDIO, SpeechRequest, neural_speech, recognize_audio, require_voice_consent, speak

router = APIRouter(prefix='/voice', tags=['Voice'])


def wav_audio(pcm: bytes, sample_rate: int) -> bytes:
    output = io.BytesIO()
    with wave.open(output, 'wb') as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(sample_rate)
        audio.writeframes(pcm)
    return output.getvalue()


@router.websocket('/stream')
async def stream_voice(ws: WebSocket):
    origin = ws.headers.get('origin')
    if origin and origin not in settings.ALLOWED_ORIGINS:
        await ws.close(code=1008)
        return
    await ws.accept()
    tasks: dict[str, asyncio.Task] = {}
    lock = asyncio.Lock()
    recognition_lock = asyncio.Lock()
    pcm = bytearray()
    turn_id = None

    async def send(payload):
        async with lock:
            await ws.send_json(payload)

    async def stop(name):
        task = tasks.pop(name, None)
        if task:
            task.cancel()
            with suppress(asyncio.CancelledError, WebSocketDisconnect, RuntimeError):
                await task

    async def recognize(identity, audio):
        try:
            async with recognition_lock:
                await asyncio.to_thread(require_voice_consent, actor)
                text = await recognize_audio(wav_audio(audio, sample_rate), 'audio/wav', 'wav', language)
            await send({'type': 'transcript', 'id': identity, 'text': text})
        except Exception:
            await send({'type': 'error', 'id': identity, 'message': 'I could not hear that clearly. Please repeat.'})

    async def synthesize(identity, data):
        try:
            await asyncio.to_thread(require_voice_consent, actor)
            if settings.VOICE_TTS_PROVIDER == 'edge':
                await send({'type': 'speech_start', 'id': identity, 'mime': 'audio/mpeg'})
                async with asyncio.timeout(45):
                    async for chunk in neural_speech(data):
                        async with lock:
                            await ws.send_bytes(struct.pack('<I', identity) + chunk)
            else:
                response = await speak(data, actor)
                await send({'type': 'speech_start', 'id': identity, 'mime': 'audio/wav'})
                async with lock:
                    await ws.send_bytes(struct.pack('<I', identity) + response.body)
            await send({'type': 'speech_end', 'id': identity})
        except Exception:
            await send({'type': 'error', 'id': identity, 'message': 'Neural speech is unavailable. Tap Repeat to retry, or use the keyboard.'})

    try:
        hello = await asyncio.wait_for(ws.receive_json(), timeout=8)
        if not isinstance(hello, dict):
            raise ValueError('Invalid authentication frame')
        token = hello.get('token')
        language = hello.get('language', 'hi')
        sample_rate = hello.get('sample_rate', 16000)
        if hello.get('type') != 'auth' or not isinstance(token, str) or len(token) > 512:
            raise ValueError('Invalid authentication frame')
        if language not in ('hi', 'en') or sample_rate not in (16000, 24000, 44100, 48000):
            raise ValueError('Invalid audio configuration')
        actor = await asyncio.to_thread(get_current_actor, x_session_token=token, x_session_id=None,
                                       x_worker_api_key=None, x_beneficiary_id=None, authorization=None)
        await asyncio.to_thread(require_voice_consent, actor)
        await send({'type': 'ready'})
        while True:
            message = await asyncio.wait_for(ws.receive(), timeout=180)
            if message['type'] == 'websocket.disconnect':
                break
            binary = message.get('bytes')
            if binary is not None:
                if len(binary) < 4 or len(binary) > 32772 or (len(binary) - 4) % 2:
                    raise ValueError('Invalid PCM frame')
                identity = struct.unpack_from('<I', binary)[0]
                if identity != turn_id:
                    continue
                if len(pcm) + len(binary) - 4 > min(MAX_AUDIO, sample_rate * 2 * 30):
                    raise ValueError('Speak in shorter turns')
                pcm.extend(binary[4:])
                continue
            raw = message.get('text', '')
            if len(raw) > 16000:
                raise ValueError('Frame too large')
            data = json.loads(raw)
            if not isinstance(data, dict):
                raise ValueError('Invalid command')
            identity = data.get('id', 0)
            if type(identity) is not int or not 0 <= identity <= 0xffffffff:
                raise ValueError('Invalid generation')
            kind = data.get('type')
            if kind == 'interrupt':
                await stop('speech')
            elif kind == 'turn_start':
                turn_id = identity
                pcm.clear()
            elif kind == 'turn_end' and identity == turn_id:
                if len(pcm) < 100:
                    await send({'type': 'error', 'id': identity, 'message': 'Please speak a little longer.'})
                else:
                    tasks = {name: task for name, task in tasks.items() if not task.done()}
                    if sum(name.startswith('recognition:') for name in tasks) >= 3:
                        await send({'type': 'error', 'id': identity, 'message': 'Please wait a moment before your next answer.'})
                    else:
                        tasks[f'recognition:{identity}'] = asyncio.create_task(recognize(identity, bytes(pcm)))
                pcm.clear()
                turn_id = None
            elif kind == 'speak':
                speech = SpeechRequest(text=data.get('text'), language=language, slow=data.get('slow', False))
                await stop('speech')
                tasks['speech'] = asyncio.create_task(synthesize(identity, speech))
            else:
                raise ValueError('Unknown voice command')
    except (HTTPException, ValueError, ValidationError, TimeoutError):
        with suppress(RuntimeError, WebSocketDisconnect):
            await send({'type': 'error', 'message': 'Voice connection needs a valid session and consent. Resume to reconnect.'})
            await ws.close(code=1008)
    except WebSocketDisconnect:
        pass
    finally:
        for name in list(tasks):
            await stop(name)
        pcm.clear()
