from copy import deepcopy
import pytest
from app.ai_layers.layer3_matching import ml_adapter
from app.config import settings


@pytest.fixture
def candidates():
    return [{
        'qualification': {'internal_id': 'verified_q'}, 'score': 80.0,
        'ranking_factors': {'interest_score': 30}, 'match_state': 'Interest Match',
        'best_opp': None, 'local_availability': {'status': 'unknown'},
    }]


QUALIFICATIONS = {'verified_q': {
    'title': 'Sewing', 'sector': 'Apparel', 'nsqf_level': 2,
    'duration_hours': 200, 'min_education': 'Class 5',
}}


def test_disabled_model_does_not_import_or_call_ml(monkeypatch, candidates):
    monkeypatch.setattr(settings, 'ML_RANKING_ENABLED', False)
    def forbidden(*args):
        pytest.fail('disabled ML must not be loaded')
    monkeypatch.setattr(ml_adapter, '_predict', forbidden)
    original = deepcopy(candidates)
    ml_adapter.rerank_candidates(candidates, {}, QUALIFICATIONS)
    assert candidates == original


@pytest.mark.ml
def test_packaged_model_scores_verified_candidate(monkeypatch, candidates):
    pytest.importorskip('sklearn')
    pytest.importorskip('pandas')
    monkeypatch.setattr(settings, 'ML_RANKING_ENABLED', True)
    ml_adapter.rerank_candidates(candidates, {'education': 'Class 10', 'interests': ['Apparel']}, QUALIFICATIONS)
    assert candidates[0]['ranking_factors']['ml_training_data'] == 'synthetic'
    assert 0 <= candidates[0]['ranking_factors']['ml_score'] <= 1
    assert candidates[0]['match_state'] == 'Interest Match'


@pytest.mark.ml
def test_model_empty_catalogue_and_education_aliases():
    pd = pytest.importorskip('pandas')
    pytest.importorskip('sklearn')
    from ml_model.src.prediction.predict import predict
    from ml_model.src.ranking.eligibility import filter_eligible_courses
    assert predict({}, courses_df=pd.DataFrame())['recommendations'] == []
    courses = pd.DataFrame([
        {'course_id': 'primary', 'age_min': 18, 'age_max': 60,
         'minimum_education': 'Primary', 'required_skill_level': 'Beginner'},
        {'course_id': 'graduate', 'age_min': 18, 'age_max': 60,
         'minimum_education': 'Graduate', 'required_skill_level': 'Beginner'},
    ])
    eligible = filter_eligible_courses({'age': 25, 'education_level': 'Class 10'}, courses)
    assert eligible['course_id'].tolist() == ['primary']


def test_model_only_scores_existing_candidates(monkeypatch, candidates):
    monkeypatch.setattr(settings, 'ML_RANKING_ENABLED', True)
    def predictor(profile, courses):
        assert [course['course_id'] for course in courses] == ['verified_q']
        assert courses[0]['minimum_education'] == 'Primary'
        assert profile['education_level'] == 'Secondary'
        return {'method': 'ml_model', 'recommendations': [{'course_id': 'verified_q', 'score': 0.9}]}
    monkeypatch.setattr(ml_adapter, '_predict', predictor)
    ml_adapter.rerank_candidates(candidates, {'education': 'Class 10'}, QUALIFICATIONS)
    assert candidates[0]['score'] == 82
    assert candidates[0]['match_state'] == 'Interest Match'
    assert candidates[0]['best_opp'] is None
    assert candidates[0]['local_availability']['status'] == 'unknown'
    assert candidates[0]['ranking_factors']['ml_training_data'] == 'synthetic'


@pytest.mark.parametrize('result', [
    {'method': 'content_based_fallback', 'recommendations': []},
    {'method': 'ml_model', 'recommendations': [{'course_id': 'synthetic_course', 'score': 1}]},
    {'method': 'ml_model', 'recommendations': [{'course_id': 'verified_q', 'score': float('nan')}]},
    {'method': 'ml_model', 'recommendations': [{'course_id': 'verified_q', 'score': 2}]},
    {'method': 'ml_model', 'recommendations': []},
])
def test_invalid_or_fallback_model_output_preserves_ranking(monkeypatch, candidates, result):
    monkeypatch.setattr(settings, 'ML_RANKING_ENABLED', True)
    monkeypatch.setattr(ml_adapter, '_predict', lambda *args: result)
    original = deepcopy(candidates)
    ml_adapter.rerank_candidates(candidates, {}, QUALIFICATIONS)
    assert candidates == original


def test_missing_ml_dependency_preserves_ranking(monkeypatch, candidates):
    monkeypatch.setattr(settings, 'ML_RANKING_ENABLED', True)
    def unavailable(*args):
        raise ImportError('ML dependencies absent')
    monkeypatch.setattr(ml_adapter, '_predict', unavailable)
    original = deepcopy(candidates)
    ml_adapter.rerank_candidates(candidates, {}, QUALIFICATIONS)
    assert candidates == original
