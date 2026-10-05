import pytest
from app.ai_layers.layer2_extraction.conversation import (
    ConversationProfile, QUESTIONS, guided_extract, extract_voice_conversation,
)
from app.ai_layers.layer2_extraction.interview_language import next_question
from app.ai_layers.layer2_extraction.validation import education_to_rank
from tests.test_live_interview import live_interview


@pytest.mark.parametrize('field,question,reply,expected', [
    ('interests', 'What work would you enjoy trying?', 'sewing', ['sewing']),
    ('interests', 'आपको कौन सा काम अच्छा लगता है?', 'सिलाई', ['सिलाई']),
    ('interests', 'What would you enjoy learning to do?', 'repairing bicycles', ['repairing bicycles']),
    ('self_employment_or_wage_preference', QUESTIONS['self_employment_or_wage_preference'][0], 'Both.', 'both'),
    ('self_employment_or_wage_preference', QUESTIONS['self_employment_or_wage_preference'][0], 'dono', 'both'),
    ('self_employment_or_wage_preference', QUESTIONS['self_employment_or_wage_preference'][0], 'koi bhi', 'both'),
    ('self_employment_or_wage_preference', QUESTIONS['self_employment_or_wage_preference'][0], 'anything is fine', 'both'),
    ('mobility', QUESTIONS['mobility'][0], '0.5km', .5),
    ('mobility', QUESTIONS['mobility'][0], 'I cannot travel', 0),
    ('education', QUESTIONS['education'][0], 'I passed ninth', 'Class 9'),
    ('education', QUESTIONS['education'][0], 'ITI', 'ITI / Diploma'),
])
def test_fragments_after_rephrased_questions(field, question, reply, expected):
    profile = guided_extract([{'speaker': 'ai', 'text': question}, {'speaker': 'user', 'text': reply}])
    assert getattr(profile, field) == expected


def test_retry_wording_varies_and_rephrasing_keeps_short_reply_context(client, live_interview):
    interview, headers = live_interview
    url = f'/api/v1/interviews/{interview}/turns'
    def answer(text):
        response = client.post(url, headers=headers, json={'text': text, 'mode': 'voice'})
        assert response.status_code == 200
        return response.json()
    first = answer('I live in Moradabad, Chhajlet, passed tenth and can travel 5 km.')
    second = answer('not sure')
    third = answer('not sure')
    assert len({first['next_question'], second['next_question'], third['next_question']}) == 3
    assert answer('sewing')['inferred_profile']['interests'] == ['sewing']
    result = answer('both')
    assert result['inferred_profile']['self_employment_or_wage_preference'] == 'both'
    assert result['is_final'] is True


def test_provider_repeating_question_gets_a_different_followup(monkeypatch):
    from app.config import settings
    monkeypatch.setattr(settings, 'AI_PROVIDER', 'groq')
    monkeypatch.setattr(settings, 'GROQ_API_KEY', 'test-only')
    question = QUESTIONS['interests'][0]
    monkeypatch.setattr('app.ai_layers.layer1_intake.interviwer.interview_turn', lambda *args: {
        'message': question,
        'profile': {'district': 'Moradabad', 'block': 'Chhajlet', 'education': 'Class 10',
                    'mobility': 5, 'self_employment_or_wage_preference': 'both'},
    })
    profile, missing, followup, _ = extract_voice_conversation([
        {'speaker': 'ai', 'text': question, 'field': 'interests'},
        {'speaker': 'user', 'text': 'not sure'},
    ], 'en')
    assert missing == ['interests']
    assert followup != question
    assert profile['interests'] == []


def test_provider_string_answers_are_normalised_without_rejecting_the_turn():
    profile = ConversationProfile.model_validate({'interests': 'sewing',
        'self_employment_or_wage_preference': 'either is fine', 'education': 'ninth', 'mobility': 'five km'})
    assert profile.interests == ['sewing']
    assert profile.self_employment_or_wage_preference == 'both'
    assert profile.education == 'Class 9' and profile.mobility == 5


def test_unknown_answers_are_not_guessed_or_invalidated_as_a_whole():
    profile = ConversationProfile.model_validate({'education': 'not sure', 'mobility': 'nearby',
        'self_employment_or_wage_preference': 'not sure', 'interests': ['sewing']})
    assert profile.education is None and profile.mobility is None
    assert profile.self_employment_or_wage_preference is None and profile.interests == ['sewing']
    assert guided_extract([{'speaker': 'ai', 'text': QUESTIONS['mobility'][0]},
                           {'speaker': 'user', 'text': '5 to 10 km'}]).mobility is None


def test_schooling_rank_never_rounds_up_and_current_schooling_is_not_completion():
    assert education_to_rank('Class 9') == education_to_rank('Class 8')
    assert education_to_rank('Class 11') == education_to_rank('Class 10')
    assert guided_extract([{'speaker': 'ai', 'text': QUESTIONS['education'][0]},
                           {'speaker': 'user', 'text': 'I am currently studying in class 10'}]).education is None
