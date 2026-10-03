import json
import httpx
import pytest
from test_recommendations import client
from app.config import settings
from app.database import get_db


def session(client, consent=True):
    result = client.post('/api/v1/sessions').json()
    headers = {'X-Session-Token': result['session_token']}
    if consent:
        for kind in ['ai_processing', 'profile_storage']:
            assert client.post('/api/v1/consents', headers=headers, json={
                'session_id': result['session_id'], 'consent_type': kind, 'granted': True}).status_code == 201
    return result['session_id'], headers


def test_voice_requires_credentials_and_consent(client):
    assert client.post('/api/v1/voice/transcribe', content=b'x'*200, headers={'Content-Type': 'audio/wav'}).status_code == 401
    _, headers = session(client, False)
    assert client.post('/api/v1/voice/transcribe', content=b'x'*200, headers={**headers, 'Content-Type': 'audio/wav'}).status_code == 403


def test_groq_interview_and_correction_persist_without_confirmation(client, monkeypatch):
    monkeypatch.setattr(settings, 'GROQ_API_KEY', 'test-key')
    requests = []
    def groq(url, **kwargs):
        requests.append(kwargs['json'])
        distance = 5 if len(requests) == 1 else 3
        content = {'message': 'What kind of work do you enjoy?', 'profile': {
            'district': 'Malda', 'education': 'Class 10', 'mobility': distance}}
        return httpx.Response(200, request=httpx.Request('POST', url), json={'choices': [{'message': {'content': json.dumps(content)}}]})
    monkeypatch.setattr('Llm_nterviewer.interviwer.httpx.post', groq)
    sid, headers = session(client)
    iid = client.post('/api/v1/interviews/start', headers=headers, json={'session_id': sid, 'channel': 'voice_web', 'language': 'en'}).json()['interview_id']
    for text in ['I live in Malda, class 10, five km', 'Actually three kilometres']:
        response = client.post(f'/api/v1/interviews/{iid}/turns', headers=headers, json={'text': text, 'language': 'en', 'mode': 'voice'})
        assert response.status_code == 200, response.text
        assert response.json()['extraction_provider'] == 'groq'
        assert not response.json()['is_final']
    detail = client.get(f'/api/v1/interviews/{iid}', headers=headers).json()
    assert detail['fields']['mobility']['value'] == 3
    assert detail['fields']['mobility']['user_confirmed'] is False
    assert requests[0]['model'] == settings.GROQ_MODEL
    assert 'Actually three kilometres' in requests[1]['messages'][1]['content']
    _, other = session(client)
    assert client.get(f'/api/v1/interviews/{iid}', headers=other).status_code == 403


def test_provider_failure_rolls_back_turn(client, monkeypatch):
    def fail(*args, **kwargs): raise RuntimeError('provider unavailable')
    monkeypatch.setattr('Llm_nterviewer.interviwer.interview_turn', fail)
    sid, headers = session(client)
    iid = client.post('/api/v1/interviews/start', headers=headers, json={'session_id': sid}).json()['interview_id']
    result = client.post(f'/api/v1/interviews/{iid}/turns', headers=headers, json={'text': 'hello', 'mode': 'voice'})
    assert result.status_code == 503
    assert len(client.get(f'/api/v1/interviews/{iid}', headers=headers).json()['turns']) == 1


def test_gpt_oss_requests_enforced_profile_schema(client, monkeypatch):
    monkeypatch.setattr(settings, 'GROQ_API_KEY', 'test-key')
    monkeypatch.setattr(settings, 'GROQ_MODEL', 'openai/gpt-oss-120b')
    def groq(url, **kwargs):
        payload = kwargs['json']
        output = payload['response_format']['json_schema']
        assert output['strict'] is True
        schema = output['schema']
        assert set(schema['required']) == {'message', 'profile'}
        profile = schema['properties']['profile']
        assert set(profile['required']) == set(profile['properties'])
        assert profile['additionalProperties'] is False
        assert profile['properties']['interests']['type'] == 'array'
        assert {'type': 'null'} in profile['properties']['district']['anyOf']
        assert payload['reasoning_effort'] == 'low'
        content = {'message': 'Where do you live?', 'profile': {'current_work': 'Tailor'}}
        return httpx.Response(200, request=httpx.Request('POST', url), json={'choices': [{'finish_reason': 'stop', 'message': {'content': json.dumps(content)}}]})
    monkeypatch.setattr('Llm_nterviewer.interviwer.httpx.post', groq)
    sid, headers = session(client)
    iid = client.post('/api/v1/interviews/start', headers=headers, json={'session_id': sid}).json()['interview_id']
    result = client.post(f'/api/v1/interviews/{iid}/turns', headers=headers, json={'text': 'I work as a tailor.', 'mode': 'voice'})
    assert result.status_code == 200
    assert result.json()['inferred_profile']['district'] is None


def test_invalid_profile_reports_fields_without_personal_values(client, monkeypatch, caplog):
    def invalid(*args):
        return {'message': 'Next question', 'profile': {'interests': None, 'unexpected': 'private-test-value'}}
    monkeypatch.setattr('Llm_nterviewer.interviwer.interview_turn', invalid)
    sid, headers = session(client)
    iid = client.post('/api/v1/interviews/start', headers=headers, json={'session_id': sid}).json()['interview_id']
    result = client.post(f'/api/v1/interviews/{iid}/turns', headers=headers, json={'text': 'My answer', 'mode': 'voice'})
    assert result.status_code == 502
    assert result.json()['detail']['code'] == 'VOICE_INVALID_RESPONSE'
    assert 'profile.interests' in caplog.text
    assert 'private-test-value' not in caplog.text + result.text
    detail = client.get(f'/api/v1/interviews/{iid}', headers=headers).json()
    assert len(detail['turns']) == 1
    assert not detail['fields']


@pytest.mark.parametrize('finish,content', [('length', '{"message":"partial"}'), ('stop', '{invalid json')])
def test_incomplete_provider_json_does_not_commit(client, monkeypatch, finish, content):
    monkeypatch.setattr(settings, 'GROQ_API_KEY', 'test-key')
    def groq(url, **kwargs):
        return httpx.Response(200, request=httpx.Request('POST', url), json={'choices': [{'finish_reason': finish, 'message': {'content': content}}]})
    monkeypatch.setattr('Llm_nterviewer.interviwer.httpx.post', groq)
    sid, headers = session(client)
    iid = client.post('/api/v1/interviews/start', headers=headers, json={'session_id': sid}).json()['interview_id']
    result = client.post(f'/api/v1/interviews/{iid}/turns', headers=headers, json={'text': 'My answer', 'mode': 'voice'})
    assert result.status_code == 502
    assert result.json()['detail']['code'] == 'VOICE_INVALID_RESPONSE'
    assert len(client.get(f'/api/v1/interviews/{iid}', headers=headers).json()['turns']) == 1


@pytest.mark.parametrize('status', [401, 429])
def test_provider_errors_explain_failure_without_leaking_response(client, monkeypatch, status):
    monkeypatch.setattr(settings, 'GROQ_API_KEY', 'test-key')
    def groq(url, **kwargs):
        return httpx.Response(status, request=httpx.Request('POST', url), json={'error': {'message': 'private-test-value'}})
    monkeypatch.setattr('Llm_nterviewer.interviwer.httpx.post', groq)
    sid, headers = session(client)
    iid = client.post('/api/v1/interviews/start', headers=headers, json={'session_id': sid}).json()['interview_id']
    result = client.post(f'/api/v1/interviews/{iid}/turns', headers=headers, json={'text': 'My answer', 'mode': 'voice'})
    assert result.status_code == 503
    assert result.json()['detail']['code'] == 'VOICE_PROVIDER_ERROR'
    assert ('busy' if status == 429 else 'credentials') in result.json()['detail']['message']
    assert 'private-test-value' not in result.text


def test_audio_adapter_forwards_real_audio_and_rejects_silence(client, monkeypatch):
    monkeypatch.setattr(settings, 'GROQ_API_KEY', 'test-key')
    payload = {'text': 'नमस्ते', 'segments': [{'no_speech_prob': 0.1}]}
    class Provider:
        async def __aenter__(self): return self
        async def __aexit__(self, *args): pass
        async def post(self, url, **kwargs):
            assert kwargs['files']['file'][1] == b'a' * 500
            return httpx.Response(200, request=httpx.Request('POST', url), json=payload)
    monkeypatch.setattr('app.routers.voice.httpx.AsyncClient', lambda **kwargs: Provider())
    _, headers = session(client)
    headers['Content-Type'] = 'audio/wav'
    response = client.post('/api/v1/voice/transcribe', headers=headers, content=b'a'*500)
    assert response.json()['text'] == 'नमस्ते'
    payload['segments'][0]['no_speech_prob'] = 0.99
    assert client.post('/api/v1/voice/transcribe', headers=headers, content=b'a'*500).status_code == 422
    assert client.post('/api/v1/voice/transcribe', headers=headers, content=b'a'*(4*1024*1024+1)).status_code == 413


def test_referral_retry_does_not_duplicate(client):
    sid, headers = session(client)
    iid = client.post('/api/v1/interviews/start', headers=headers, json={'session_id': sid}).json()['interview_id']
    client.post('/api/v1/consents', headers=headers, json={'session_id': sid, 'consent_type': 'counselor_referral', 'granted': True})
    body = {'interview_id': iid, 'referral_reason': 'user_requested_human_help', 'request_id': 'voice-help-1'}
    a = client.post('/api/v1/referrals', headers=headers, json=body)
    b = client.post('/api/v1/referrals', headers=headers, json=body)
    assert a.status_code == b.status_code == 201
    assert a.json()['id'] == b.json()['id']
    with get_db() as conn:
        assert conn.execute('SELECT COUNT(*) AS n FROM referral_cases WHERE interview_id = ?', (iid,)).fetchone()['n'] == 1

    own = client.get('/api/v1/referrals/me', headers=headers)
    assert own.status_code == 200
    assert own.json()[0]['id'] == a.json()['id']
    _, other = session(client)
    assert client.get('/api/v1/referrals/me', headers=other).json() == []
