import asyncio
import struct
import wave
import io
import pytest
from starlette.websockets import WebSocketDisconnect
from test_recommendations import client
from test_voice_agent import session


def authenticate(ws, headers):
    ws.send_json({'type': 'auth', 'token': headers['X-Session-Token'], 'language': 'hi', 'sample_rate': 16000})
    assert ws.receive_json()['type'] == 'ready'


def test_stream_auth_consent_and_origin(client):
    _, headers = session(client, False)
    with client.websocket_connect('/api/v1/voice/stream') as ws:
        ws.send_json({'type': 'auth', 'token': headers['X-Session-Token']})
        assert ws.receive_json()['type'] == 'error'
        with pytest.raises(WebSocketDisconnect):
            ws.receive_json()
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect('/api/v1/voice/stream', headers={'origin': 'https://untrusted.test'}):
            pass


def test_stream_pcm_recognition_and_neural_audio(client, monkeypatch):
    _, headers = session(client)
    async def recognize(audio, mime, extension, language):
        with wave.open(io.BytesIO(audio)) as wav:
            assert wav.getframerate() == 16000
            assert wav.getnchannels() == 1
            assert wav.readframes(1000) == b'\x01\x00' * 200
        assert language == 'hi'
        return 'मैं सिलाई करता हूँ'
    async def synthesize(data):
        assert data.text == 'आप कहाँ रहते हैं?'
        yield b'first-mpeg-frame'
        yield b'second-mpeg-frame'
    monkeypatch.setattr('app.routers.voice_stream.recognize_audio', recognize)
    monkeypatch.setattr('app.routers.voice_stream.neural_speech', synthesize)
    with client.websocket_connect('/api/v1/voice/stream') as ws:
        authenticate(ws, headers)
        ws.send_json({'type': 'turn_start', 'id': 1})
        ws.send_bytes(struct.pack('<I', 99) + b'\x00\x00' * 10)
        ws.send_bytes(struct.pack('<I', 1) + b'\x01\x00' * 200)
        ws.send_json({'type': 'turn_end', 'id': 1})
        assert ws.receive_json() == {'type': 'transcript', 'id': 1, 'text': 'मैं सिलाई करता हूँ'}
        ws.send_json({'type': 'speak', 'id': 2, 'text': 'आप कहाँ रहते हैं?'})
        assert ws.receive_json() == {'type': 'speech_start', 'id': 2, 'mime': 'audio/mpeg'}
        assert ws.receive_bytes() == struct.pack('<I', 2) + b'first-mpeg-frame'
        assert ws.receive_bytes() == struct.pack('<I', 2) + b'second-mpeg-frame'
        assert ws.receive_json() == {'type': 'speech_end', 'id': 2}


def test_interrupt_cancels_provider_and_allows_next_generation(client, monkeypatch):
    _, headers = session(client)
    cancelled = []
    async def synthesize(data):
        yield b'first'
        if data.text == 'old':
            try:
                await asyncio.sleep(10)
            finally:
                cancelled.append(True)
        else:
            yield b'new'
    monkeypatch.setattr('app.routers.voice_stream.neural_speech', synthesize)
    with client.websocket_connect('/api/v1/voice/stream') as ws:
        authenticate(ws, headers)
        ws.send_json({'type': 'speak', 'id': 1, 'text': 'old'})
        ws.receive_json()
        ws.receive_bytes()
        ws.send_json({'type': 'interrupt', 'id': 2})
        ws.send_json({'type': 'speak', 'id': 3, 'text': 'new'})
        assert ws.receive_json()['id'] == 3
        assert ws.receive_bytes() == struct.pack('<I', 3) + b'first'
        assert ws.receive_bytes() == struct.pack('<I', 3) + b'new'
        assert ws.receive_json() == {'type': 'speech_end', 'id': 3}
    assert cancelled == [True]


def test_invalid_frames_close_connection(client):
    _, headers = session(client)
    with client.websocket_connect('/api/v1/voice/stream') as ws:
        authenticate(ws, headers)
        ws.send_json({'type': 'turn_start', 'id': 1})
        ws.send_bytes(b'x' * 40000)
        assert ws.receive_json()['type'] == 'error'
        with pytest.raises(WebSocketDisconnect):
            ws.receive_json()
