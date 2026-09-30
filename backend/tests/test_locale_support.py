import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db
from app.schemas.locale import SupportedLocale, ENABLED_LOCALES, resolve_locale, parse_locale, is_valid_locale, is_enabled_locale
from tests.factories.auth_factories import create_beneficiary_actor, get_auth_headers

@pytest.fixture
def client():
    return TestClient(app)

def test_locale_enum_and_enabled_registry():
    assert SupportedLocale.EN == "en"
    assert SupportedLocale.HI == "hi"
    assert SupportedLocale.BN == "bn"
    assert SupportedLocale.MR == "mr"
    assert SupportedLocale.TA == "ta"

    # Only English and Hindi enabled initially
    assert ENABLED_LOCALES == {SupportedLocale.EN, SupportedLocale.HI}
    assert is_enabled_locale("en")
    assert is_enabled_locale("hi")
    assert not is_enabled_locale("bn")
    assert not is_enabled_locale("mr")
    assert not is_enabled_locale("ta")
    assert not is_enabled_locale("unknown_lang")

def test_resolve_locale_precedence():
    # 1. Explicit valid enabled locale
    resolved = resolve_locale(explicit_locale="hi")
    assert resolved == SupportedLocale.HI

    # Explicit disabled locale falls back to default if require_enabled=True
    resolved = resolve_locale(explicit_locale="bn", require_enabled=True)
    assert resolved == SupportedLocale.EN

    # Explicit invalid locale falls back
    resolved = resolve_locale(explicit_locale="xyz")
    assert resolved == SupportedLocale.EN

    # 3. User preferred language when no explicit locale
    resolved = resolve_locale(actor_preferred_language="hi")
    assert resolved == SupportedLocale.HI

    # 4. English fallback
    resolved = resolve_locale()
    assert resolved == SupportedLocale.EN

def test_auth_update_language_validation(client):
    import uuid
    uid = f"usr_{uuid.uuid4().hex[:8]}"
    email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    with get_db() as conn:
        user = create_beneficiary_actor(conn, user_id=uid, email=email)
    
    headers = get_auth_headers(user["id"])

    # Verify initial get /me has preferred_language
    res = client.get("/api/v1/auth/me", headers=headers)
    assert res.status_code == 200
    assert res.json()["preferred_language"] == "en"

    # Update to valid enabled locale 'hi'
    res = client.patch("/api/v1/auth/me/language", json={"preferred_language": "hi"}, headers=headers)
    assert res.status_code == 200
    assert res.json()["preferred_language"] == "hi"

    # Verify persistence on /me
    res = client.get("/api/v1/auth/me", headers=headers)
    assert res.status_code == 200
    assert res.json()["preferred_language"] == "hi"

    # Reject disabled locale (e.g. bn, ta)
    res = client.patch("/api/v1/auth/me/language", json={"preferred_language": "bn"}, headers=headers)
    assert res.status_code == 400
    assert "not currently supported or enabled" in res.json()["detail"]

    # Reject invalid locale string
    res = client.patch("/api/v1/auth/me/language", json={"preferred_language": "french"}, headers=headers)
    assert res.status_code == 400
    assert "not currently supported or enabled" in res.json()["detail"]

def test_chat_ai_locale_propagation(client):
    # 1. English chat inquiry
    res = client.post("/api/v1/chat", json={"message": "What is the stipend for training?", "language": "en"})
    assert res.status_code == 200
    data = res.json()
    assert data["locale"] == "en"
    assert "DBT stipend" in data["reply"]

    # 2. Hindi chat inquiry
    res = client.post("/api/v1/chat", json={"message": "प्रशिक्षण का वजीफा क्या है?", "language": "hi"})
    assert res.status_code == 200
    data = res.json()
    assert data["locale"] == "hi"
    assert "वजीफा" in data["reply"]

    # 3. Via Accept-Language header
    res = client.get("/api/v1/chat?message=Tell me about transport", headers={"Accept-Language": "hi"})
    assert res.status_code == 200
    data = res.json()
    assert data["locale"] == "hi"
    assert "यात्रा" in data["reply"] or "किमी" in data["reply"]
