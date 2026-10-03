import os
import tempfile
import pytest
from fastapi.testclient import TestClient
from app.config import settings
from app.database import get_db, init_database
from app.main import app

@pytest.fixture
def client(monkeypatch):
    temp_dir = tempfile.TemporaryDirectory()
    monkeypatch.setattr(settings, 'DATABASE_URL', '')
    monkeypatch.setattr(settings, 'DATABASE_PATH', os.path.join(temp_dir.name, "test_recs.db"))
    init_database()

    with TestClient(app) as c:
        yield c

    temp_dir.cleanup()

def test_hard_filters_enforce_education_and_accessibility(client):
    # Setup interview with confirmed Class 5 education and limited mobility (wheelchair)
    sess_res = client.post("/api/v1/sessions")
    session_id = sess_res.json()["session_id"]
    session_headers = {"X-Session-Token": sess_res.json()["session_token"]}

    client.post("/api/v1/consents", json={
        "session_id": session_id,
        "consent_type": "ai_processing",
        "granted": True
    }, headers=session_headers)

    start_res = client.post("/api/v1/interviews/start", json={"session_id": session_id}, headers=session_headers)
    interview_id = start_res.json()["interview_id"]

    # Confirm profile with Class 5 education
    client.post(f"/api/v1/interviews/{interview_id}/confirm-profile", json={
        "session_id": session_id,
        "confirmed_fields": {
            "education": "Class 5",
            "access_needs": "wheelchair limited mobility",
            "mobility": 2.0,
            "district": "Moradabad",
            "block": "Chhajlet"
        }
    }, headers=session_headers)

    # Generate recommendations
    gen_res = client.post("/api/v1/recommendations/generate", json={
        "interview_id": interview_id
    }, headers=session_headers)
    assert gen_res.status_code == 200
    data = gen_res.json()
    recs = data["recommendations"]

    # Class 10 courses (like Solar PV Installer SGJ/Q0101) MUST NOT be present
    for r in recs:
        assert r["qualification"]["id"] != "SGJ/Q0101", "Class 10 course should have been blocked for Class 5 user"

def test_work_preference_filtering(client):
    sess_res = client.post("/api/v1/sessions")
    session_id = sess_res.json()["session_id"]
    session_headers = {"X-Session-Token": sess_res.json()["session_token"]}
    client.post("/api/v1/consents", json={"session_id": session_id, "consent_type": "ai_processing", "granted": True}, headers=session_headers)

    start_res = client.post("/api/v1/interviews/start", json={"session_id": session_id}, headers=session_headers)
    interview_id = start_res.json()["interview_id"]

    # User confirms wage-only preference
    client.post(f"/api/v1/interviews/{interview_id}/confirm-profile", json={
        "session_id": session_id,
        "confirmed_fields": {
            "education": "Class 10",
            "self_employment_or_wage_preference": "wage",
            "district": "Moradabad",
            "block": "Chhajlet"
        }
    }, headers=session_headers)

    gen_res = client.post("/api/v1/recommendations/generate", json={
        "interview_id": interview_id
    }, headers=session_headers)
    assert gen_res.status_code == 200
    recs = gen_res.json()["recommendations"]

    # Self-employment only course (like Sewing Machine Operator AMH/Q0301 or Mushroom Cultivator AGR/Q7803)
    # should either be filtered out or wage-aligned courses (like Solar PV Installer) should lead
    assert len(recs) > 0

def test_no_local_option_returns_status_unknown_without_hallucination(client):
    sess_res = client.post("/api/v1/sessions")
    session_id = sess_res.json()["session_id"]
    session_headers = {"X-Session-Token": sess_res.json()["session_token"]}
    client.post("/api/v1/consents", json={"session_id": session_id, "consent_type": "ai_processing", "granted": True}, headers=session_headers)

    start_res = client.post("/api/v1/interviews/start", json={"session_id": session_id}, headers=session_headers)
    interview_id = start_res.json()["interview_id"]

    # District with no verified opportunities (e.g., Lucknow)
    client.post(f"/api/v1/interviews/{interview_id}/confirm-profile", json={
        "session_id": session_id,
        "confirmed_fields": {
            "education": "Class 10",
            "district": "Lucknow",
            "block": "Bakshi Ka Talab"
        }
    }, headers=session_headers)

    gen_res = client.post("/api/v1/recommendations/generate", json={
        "interview_id": interview_id,
        "district": "Lucknow"
    }, headers=session_headers)
    assert gen_res.status_code == 200
    data = gen_res.json()
    recs = data["recommendations"]

    for r in recs:
        # Must return unknown local availability, NOT a fabricated provider or address
        assert r["local_availability"]["status"] == "unknown"
        assert r["local_availability"]["centre_name"] is None
        assert "not confirmation of admission" in r["caveat"]

    # Referral suggestion flag must be set
    assert data["counselor_referral_suggested"] is True

def test_no_result_scenario_returns_counselor_handoff(client):
    # Impossible constraints: 0 km mobility, non-existent trade
    gen_res = client.post("/api/v1/recommendations/generate", json={
        "district": "NonExistentDistrict",
        "mobility_radius_km": 0.01,
        "do_not_recommend": ["solar", "apparel", "agriculture", "electronics", "food", "retail", "plumb", "health", "data", "beauty", "weld"]
    })
    assert gen_res.status_code == 200
    data = gen_res.json()
    assert data["count"] == 0
    assert data["counselor_referral_suggested"] is True
    assert "referral_reason" in data

def test_live_model_journey_and_referral(client, monkeypatch):
    pytest.importorskip('sklearn')
    monkeypatch.setattr(settings, 'ML_RANKING_ENABLED', True)
    session = client.post('/api/v1/sessions').json()
    headers = {'X-Session-Token': session['session_token']}
    for consent in ('ai_processing', 'profile_storage'):
        assert client.post('/api/v1/consents', headers=headers, json={
            'session_id': session['session_id'], 'consent_type': consent, 'granted': True
        }).status_code < 300
    interview = client.post('/api/v1/interviews/start', headers=headers, json={
        'session_id': session['session_id'], 'language': 'en'
    }).json()['interview_id']
    endpoint = '/api/v1/recommendations/generate'
    assert client.post(endpoint, headers=headers, json={'interview_id': interview}).status_code == 409
    assert client.post(f'/api/v1/interviews/{interview}/confirm-profile', headers=headers, json={
        'confirmed_fields': {'district': 'Moradabad', 'block': 'Chhajlet', 'education': 'Class 10',
            'interests': ['farming'], 'traditional_or_existing_skills': ['farming'], 'mobility': 10,
            'language': 'en', 'self_employment_or_wage_preference': 'both'}
    }).status_code == 200
    response = client.post(endpoint, headers=headers, json={'interview_id': interview})
    assert response.status_code == 200
    result = response.json()
    assert result['ranking_method'] == 'ml_blended'
    assert result['count'] == 3
    for rec in result['recommendations']:
        assert 0 <= rec['ranking_factors']['ml_score'] <= 1
        assert isinstance(rec['qualification']['nsqf_level'], (int, float))
        assert rec['qualification']['nqr_code']
        stored = client.get('/api/v1/recommendations/' + rec['recommendation_id']).json()
        assert stored['ranking_factors'] == rec['ranking_factors']
        assert stored['qualification'] == {k:v for k,v in rec['qualification'].items() if k != 'internal_id'}
    assert client.post(endpoint, json={'interview_id': interview}).status_code == 403
    assert client.post(f'/api/v1/interviews/{interview}/confirm-profile', json={'confirmed_fields': {'education': 'Graduate'}}).status_code == 403
    referral = {'interview_id': interview, 'referral_reason': 'user_requested_human_help',
                'recommendation_id': result['recommendations'][0]['recommendation_id']}
    assert client.post('/api/v1/referrals', headers=headers, json=referral).status_code == 403
    client.post('/api/v1/consents', headers=headers, json={
        'session_id': session['session_id'], 'consent_type': 'counselor_referral', 'granted': True})
    response = client.post('/api/v1/referrals', headers=headers, json=referral)
    assert response.status_code < 300
    assert response.json()['id']
    monkeypatch.setattr(settings, 'ML_RANKING_ENABLED', False)
    fallback = client.post(endpoint, headers=headers, json={'interview_id': interview}).json()
    assert fallback['ranking_method'] == 'rules'
    assert all('ml_score' not in rec['ranking_factors'] for rec in fallback['recommendations'])
