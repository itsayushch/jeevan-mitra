import pytest
from app.config import settings

@pytest.fixture
def live_interview(client, monkeypatch):
    monkeypatch.setattr(settings, 'AI_PROVIDER', 'mock')
    monkeypatch.setattr(settings, 'GROQ_API_KEY', '')
    monkeypatch.setattr(settings, 'GEMINI_API_KEY', '')
    monkeypatch.setattr(settings, 'AI_API_KEY', '')
    session = client.post('/api/v1/sessions').json()
    headers = {'X-Session-Token': session['session_token']}
    for consent in ('ai_processing', 'profile_storage'):
        client.post('/api/v1/consents', headers=headers, json={
            'session_id': session['session_id'], 'consent_type': consent, 'granted': True})
    start = client.post('/api/v1/interviews/start', headers=headers, json={
        'session_id': session['session_id'], 'language': 'en'})
    assert start.status_code == 201
    assert start.json()['first_question'] == 'Which district do you live in?'
    return start.json()['interview_id'], headers

def complete(client, interview):
    interview_id, headers = interview
    for index, answer in enumerate(('Moradabad', 'Chhajlet', 'Class 10', 'sewing', '5', 'both')):
        result = client.post(f'/api/v1/interviews/{interview_id}/turns', headers=headers,
            json={'text': answer, 'mode': 'voice', 'input_mode': 'voice' if index % 2 else 'text'})
        assert result.status_code == 200
        assert result.json()['is_final'] is (index == 5)
    return result.json()['inferred_profile']

@pytest.mark.parametrize('field,text,expected', [
    ('mobility', 'Actually I can travel 12 kilometres', 12),
    ('education', 'Actually I completed class 12', 'Class 12'),
    ('district', 'Change my district to Kolkata', 'Kolkata'),
    ('self_employment_or_wage_preference', 'I want my own business', 'self_employment'),
    ('traditional_or_existing_skills', 'sewing, embroidery', ['sewing', 'embroidery']),
])
def test_single_spoken_correction(client, live_interview, field, text, expected):
    complete(client, live_interview)
    interview_id, headers = live_interview
    before = client.get(f'/api/v1/interviews/{interview_id}', headers=headers).json()['fields']
    result = client.post(f'/api/v1/interviews/{interview_id}/corrections', headers=headers,
        json={'field_name': field, 'text': text})
    assert result.status_code == 200
    assert result.json() == {'field_name': field, 'value': expected}
    assert client.get(f'/api/v1/interviews/{interview_id}', headers=headers).json()['fields'] == before

def test_correction_requires_review_before_matching(client, live_interview):
    profile = complete(client, live_interview)
    interview_id, headers = live_interview
    generate = '/api/v1/recommendations/generate'
    assert client.post(generate, headers=headers, json={'interview_id': interview_id}).status_code == 409
    client.post(f'/api/v1/interviews/{interview_id}/confirm-profile', headers=headers,
        json={'confirmed_fields': profile})
    assert client.post(generate, headers=headers, json={'interview_id': interview_id}).status_code == 200
    client.patch(f'/api/v1/interviews/{interview_id}/fields/education', headers=headers,
        json={'value': 'Class 12'})
    assert client.post(generate, headers=headers, json={'interview_id': interview_id}).status_code == 409

def test_invalid_answer_and_foreign_session_are_rejected(client, live_interview):
    interview_id, headers = live_interview
    url = f'/api/v1/interviews/{interview_id}/corrections'
    assert client.post(url, headers=headers, json={'field_name': 'mobility', 'text': '900 km'}).status_code == 422
    other = client.post('/api/v1/sessions').json()
    other_headers = {'X-Session-Token': other['session_token']}
    assert client.post(url, headers=other_headers, json={'field_name': 'mobility', 'text': '10 km'}).status_code == 403

def test_provider_error_does_not_finish_interview(client, live_interview, monkeypatch):
    from fastapi import HTTPException
    interview_id, headers = live_interview
    before = client.get(f'/api/v1/interviews/{interview_id}', headers=headers).json()
    def unavailable(*args):
        raise HTTPException(503, 'Voice service temporarily unavailable')
    monkeypatch.setattr('app.routers.interview.extract_voice_conversation', unavailable)
    result = client.post(f'/api/v1/interviews/{interview_id}/turns', headers=headers,
        json={'text': 'Moradabad', 'mode': 'voice'})
    assert result.status_code == 503
    after = client.get(f'/api/v1/interviews/{interview_id}', headers=headers).json()
    assert after['status'] == before['status']
    assert after['transcript_history'] == before['transcript_history']



def test_dashboard_loads_saved_matches_for_own_session_only(client, live_interview):
    profile = complete(client, live_interview)
    interview_id, headers = live_interview
    client.post(f'/api/v1/interviews/{interview_id}/confirm-profile', headers=headers,
                json={'confirmed_fields': profile})
    result = client.post('/api/v1/recommendations/generate', headers=headers,
                         json={'interview_id': interview_id})
    assert result.status_code == 200
    saved = client.get(f'/api/v1/interviews/{interview_id}/recommendations', headers=headers)
    assert saved.status_code == 200
    assert saved.json()['count'] == result.json()['count']
    assert all(item['qualification']['title'] for item in saved.json()['recommendations'])
    other = client.post('/api/v1/sessions').json()
    assert client.get(f'/api/v1/interviews/{interview_id}/recommendations',
                      headers={'X-Session-Token': other['session_token']}).status_code == 403


def test_course_join_request_records_selected_course_and_requires_consent(client, live_interview):
    profile = complete(client, live_interview)
    interview_id, headers = live_interview
    client.post(f'/api/v1/interviews/{interview_id}/confirm-profile', headers=headers,
                json={'confirmed_fields': profile})
    matches = client.post('/api/v1/recommendations/generate', headers=headers,
                          json={'interview_id': interview_id}).json()['recommendations']
    course = matches[0]
    request = {'interview_id': interview_id, 'recommendation_id': course['recommendation_id'],
               'referral_reason': 'user_requested_human_help',
               'notes': f"Please help me register for {course['qualification']['title']}."}
    assert client.post('/api/v1/referrals', headers=headers, json=request).status_code == 403
    session_id = client.get(f'/api/v1/interviews/{interview_id}', headers=headers).json()['session_id']
    client.post('/api/v1/consents', headers=headers,
                json={'session_id': session_id, 'consent_type': 'counselor_referral', 'granted': True})
    result = client.post('/api/v1/referrals', headers=headers, json=request)
    assert result.status_code == 201
    assert result.json()['id']
    assert result.json()['recommendation_id'] == course['recommendation_id']
    assert result.json()['notes'] == request['notes']
    assert result.json()['status'] == 'new'
