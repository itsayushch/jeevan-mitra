import pytest
from app.config import settings
from app.database import get_db
from app.ai_layers.layer2_extraction.conversation import guided_extract, extract_conversation

def test_unknowns_are_not_invented():
    p = guided_extract([{'speaker': 'user', 'text': 'Hello, I need help'}])
    assert p.education is None and p.district is None and p.mobility is None
    assert p.current_work is None and not p.traditional_or_existing_skills

def test_distance_is_not_education_and_latest_correction_wins():
    p = guided_extract([{'speaker': 'user', 'text': 'I can travel 10 km'},
                        {'speaker': 'user', 'text': 'I studied till tenth and want to learn farming'},
                        {'speaker': 'user', 'text': 'Actually I completed class 12 and can travel 3 km'}])
    assert p.education == 'Class 12' and p.mobility == 3
    assert p.interests == ['Agriculture'] and not p.traditional_or_existing_skills

def test_hindi_profile():
    p = guided_extract([{'speaker': 'user', 'text': 'मैं मुरादाबाद छजलैट में रहता हूँ। दसवीं पास हूँ। सिलाई सीखना चाहता हूँ। 5 किलोमीटर जा सकता हूँ। नौकरी चाहिए।'}])
    assert p.education == 'Class 10' and p.mobility == 5 and p.interests == ['Sewing']
    assert p.self_employment_or_wage_preference == 'wage'

def test_provider_failure_falls_back_without_defaults(monkeypatch):
    monkeypatch.setattr(settings, 'AI_PROVIDER', 'gemini')
    monkeypatch.setattr(settings, 'GEMINI_API_KEY', 'test-only')
    def unavailable(*args, **kwargs): raise RuntimeError('offline')
    monkeypatch.setattr('app.ai_layers.layer2_extraction.conversation.httpx.post', unavailable)
    p, missing, question, provider = extract_conversation([{'speaker': 'user', 'text': 'Hello'}], 'en')
    assert provider == 'guided' and p['education'] is None and 'district' in missing

def test_gemini_structured_response(monkeypatch):
    import httpx
    monkeypatch.setattr(settings, 'AI_PROVIDER', 'gemini')
    monkeypatch.setattr(settings, 'GEMINI_API_KEY', 'test-only')
    def respond(*args, **kwargs):
        config = kwargs['json']['generationConfig']
        assert config['responseMimeType'] == 'application/json'
        assert 'education' in config['responseJsonSchema']['properties']
        return httpx.Response(200, request=httpx.Request('POST', 'https://example.test'), json={
            'candidates': [{'content': {'parts': [{'text': '{"education":"Class 10"}'}]}}]})
    monkeypatch.setattr('app.ai_layers.layer2_extraction.conversation.httpx.post', respond)
    profile, missing, _, provider = extract_conversation([{'speaker': 'user', 'text': 'I completed tenth'}], 'en')
    assert provider == 'gemini' and profile['education'] == 'Class 10'
    assert profile['mobility'] is None and 'district' in missing

def test_conversation_to_review_to_ml(client, monkeypatch):
    monkeypatch.setattr(settings, 'AI_PROVIDER', 'mock')
    session = client.post('/api/v1/sessions').json()
    headers = {'X-Session-Token': session['session_token']}
    for consent in ('ai_processing', 'profile_storage'):
        client.post('/api/v1/consents', headers=headers, json={'session_id': session['session_id'], 'consent_type': consent, 'granted': True})
    interview = client.post('/api/v1/interviews/start', headers=headers, json={'session_id': session['session_id'], 'language': 'en'}).json()['interview_id']
    url = f'/api/v1/interviews/{interview}/turns'
    response = client.post(url, headers=headers, json={'text': 'I studied till tenth and want to learn farming. I can travel 5 km.', 'language': 'en', 'mode': 'conversational'})
    assert response.status_code == 200
    result = response.json()
    assert result['inferred_profile']['education'] == 'Class 10'
    assert result['inferred_profile']['district'] is None
    from app.ai_layers.layer2_extraction.interview_language import question_field
    assert question_field({'text': result['next_question']}) == 'district'
    assert result['next_question'] != 'Which district do you live in?'
    for answer in ('Moradabad', 'Chhajlet', 'both'):
        response = client.post(url, headers=headers, json={'text': answer, 'language': 'en', 'mode': 'conversational'})
        assert response.status_code == 200
    result = response.json()
    assert result['is_final'] is True
    generate = '/api/v1/recommendations/generate'
    assert client.post(generate, headers=headers, json={'interview_id': interview}).status_code == 409
    client.post(f'/api/v1/interviews/{interview}/confirm-profile', headers=headers, json={'confirmed_fields': result['inferred_profile']})
    assert client.post(generate, headers=headers, json={'interview_id': interview}).json()['count'] == 3
    client.post(url, headers=headers, json={'text': 'Actually I completed class 8', 'language': 'en', 'mode': 'conversational'})
    assert client.post(generate, headers=headers, json={'interview_id': interview}).status_code == 409
    assert client.post(url, json={'text': 'Change profile', 'mode': 'conversational'}).status_code == 403


@pytest.mark.parametrize('field,answer,expected', [
    ('mobility', 'about ten kilometres would be okay', 10),
    ('mobility', 'पाँच किलोमीटर', 5),
    ('education', 'ten', 'Class 10'),
    ('education', 'SSC', 'Class 10'),
    ('education', 'intermediate', 'Class 12'),
    ('self_employment_or_wage_preference', 'a salaried job sounds good', 'wage'),
    ('self_employment_or_wage_preference', 'either is fine', 'both'),
])
def test_natural_short_replies(field, answer, expected):
    from app.ai_layers.layer2_extraction.conversation import QUESTIONS
    result = guided_extract([{'speaker': 'ai', 'text': QUESTIONS[field][0]},
                             {'speaker': 'user', 'text': answer}])
    assert getattr(result, field) == expected
