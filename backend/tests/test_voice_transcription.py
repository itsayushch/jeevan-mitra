import base64
import httpx
import pytest
from app.config import settings
from tests.test_live_interview import live_interview

@pytest.fixture
def audio_payload():
    return {'audio_base64': base64.b64encode(b'RIFF-test-audio').decode(),
            'mime_type': 'audio/wav', 'language': 'en'}

@pytest.fixture
def provider(monkeypatch):
    monkeypatch.setattr(settings, 'GROQ_API_KEY', 'test-key')
    calls = []
    class Client:
        def __init__(self, **kwargs): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *args): pass
        async def post(self, url, **kwargs):
            calls.append((url, kwargs))
            return httpx.Response(200, json={'text': 'Moradabad', 'segments': [{'no_speech_prob': 0.01}]},
                                  request=httpx.Request('POST', url))
    monkeypatch.setattr('app.routers.interview.httpx.AsyncClient', Client)
    return calls

def test_transcription_does_not_submit_answer(client, live_interview, audio_payload, provider):
    interview_id, headers = live_interview
    before = client.get(f'/api/v1/interviews/{interview_id}', headers=headers).json()
    result = client.post(f'/api/v1/interviews/{interview_id}/transcribe', headers=headers, json=audio_payload)
    assert result.status_code == 200
    assert result.json() == {'text': 'Moradabad'}
    assert provider[0][1]['data']['language'] == 'en'
    assert provider[0][1]['files']['file'] == ('answer.wav', b'RIFF-test-audio', 'audio/wav')
    after = client.get(f'/api/v1/interviews/{interview_id}', headers=headers).json()
    assert after['transcript_history'] == before['transcript_history']

def test_transcription_rejects_foreign_session(client, live_interview, audio_payload, provider):
    interview_id, _ = live_interview
    session = client.post('/api/v1/sessions').json()
    response = client.post(f'/api/v1/interviews/{interview_id}/transcribe',
        headers={'X-Session-Token': session['session_token']}, json=audio_payload)
    assert response.status_code == 403
    assert not provider

def test_transcription_requires_consent(client, live_interview, audio_payload, provider):
    interview_id, headers = live_interview
    session_id = client.get(f'/api/v1/interviews/{interview_id}', headers=headers).json()['session_id']
    client.post('/api/v1/consents', headers=headers, json={
        'session_id': session_id, 'consent_type': 'ai_processing', 'granted': False})
    response = client.post(f'/api/v1/interviews/{interview_id}/transcribe', headers=headers, json=audio_payload)
    assert response.status_code == 403
    assert not provider

def test_invalid_audio_and_unconfigured_provider(client, live_interview, audio_payload, provider, monkeypatch):
    interview_id, headers = live_interview
    url = f'/api/v1/interviews/{interview_id}/transcribe'
    assert client.post(url, headers=headers, json={**audio_payload, 'audio_base64': '!'}).status_code == 422
    assert not provider
    monkeypatch.setattr(settings, 'GROQ_API_KEY', '')
    assert client.post(url, headers=headers, json=audio_payload).status_code == 503

@pytest.mark.parametrize('response_kind,expected', [('timeout', 504), ('failure', 503), ('silence', 422)])
def test_transcription_failure_keeps_interview(client, live_interview, audio_payload, monkeypatch, response_kind, expected):
    monkeypatch.setattr(settings, 'GROQ_API_KEY', 'test-key')
    class Client:
        def __init__(self, **kwargs): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *args): pass
        async def post(self, url, **kwargs):
            if response_kind == 'timeout': raise httpx.ReadTimeout('timed out')
            status = 503 if response_kind == 'failure' else 200
            return httpx.Response(status, json={'text': 'hallucinated', 'segments': [{'no_speech_prob': .99}]}, request=httpx.Request('POST', url))
    monkeypatch.setattr('app.routers.interview.httpx.AsyncClient', Client)
    interview_id, headers = live_interview
    before = client.get(f'/api/v1/interviews/{interview_id}', headers=headers).json()
    response = client.post(f'/api/v1/interviews/{interview_id}/transcribe', headers=headers, json=audio_payload)
    assert response.status_code == expected
    after = client.get(f'/api/v1/interviews/{interview_id}', headers=headers).json()
    assert after['transcript_history'] == before['transcript_history']
