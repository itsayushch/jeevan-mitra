import pytest
import uuid
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db

from tests.factories.auth_factories import create_user
from app.core.security import create_access_token

client = TestClient(app)

def create_test_actor(role: str = "beneficiary", district: str = "Moradabad"):
    unique = uuid.uuid4().hex[:8]
    user_id = f"usr_{role}_{unique}"
    email = f"{role}_{unique}@test.com"
    with get_db() as conn:
        create_user(
            conn,
            user_id=user_id,
            email=email,
            display_name=f"Test {role.title()}",
            role_key=role,
            district_id=district
        )
        conn.commit()

    token = create_access_token(subject=user_id, session_id=f"sess_{unique}")
    headers = {"Authorization": f"Bearer {token}"}
    return user_id, headers

def test_opportunity_text_submission_success():
    user_id, headers = create_test_actor(role="beneficiary")

    payload = {
        "input_mode": "text",
        "text": "A new solar panel maintenance workshop opening next month at Moradabad Industrial Estate.",
        "locale": "en"
    }

    res = client.post("/api/v1/opportunity-submissions", json=payload, headers=headers)
    assert res.status_code == 201
    data = res.json()
    assert data["id"].startswith("sub_")
    assert data["input_mode"] == "text"
    assert data["status"] == "SUBMITTED"
    assert data["locale"] == "en"
    assert data["submitted_by_user_id"] == user_id
    assert "solar panel maintenance" in data["normalized_text"]

def test_opportunity_voice_submission_success():
    user_id, headers = create_test_actor(role="beneficiary")

    payload = {
        "input_mode": "voice",
        "text": "हैंडीक्राफ्ट और सिलाई का नया प्रशिक्षण केंद्र सिविल लाइन्स में शुरू हो रहा है।",
        "locale": "hi",
        "audio_storage_key": "audio/2026/09/sample_voice.wav",
        "transcript_confidence": 0.94
    }

    res = client.post("/api/v1/opportunity-submissions", json=payload, headers=headers)
    assert res.status_code == 201
    data = res.json()
    assert data["input_mode"] == "voice"
    assert data["status"] == "SUBMITTED"
    assert data["locale"] == "hi"
    assert data["audio_storage_key"] == "audio/2026/09/sample_voice.wav"
    assert data["transcript_confidence"] == 0.94

def test_submission_normalization_and_whitespace():
    _, headers = create_test_actor(role="beneficiary")

    # Excessive whitespaces, tabs, newlines
    payload = {
        "input_mode": "text",
        "text": "   New   carpentry   training   facility   near   bus stand.   \n\n  "
    }

    res = client.post("/api/v1/opportunity-submissions", json=payload, headers=headers)
    assert res.status_code == 201
    data = res.json()
    assert data["normalized_text"] == "New carpentry training facility near bus stand."

def test_submission_empty_or_too_short_rejected():
    _, headers = create_test_actor(role="beneficiary")

    # Empty text
    res_empty = client.post("/api/v1/opportunity-submissions", json={"input_mode": "text", "text": "   "}, headers=headers)
    assert res_empty.status_code == 400
    assert "EMPTY_SUBMISSION" in str(res_empty.json())

    # Text < 3 chars
    res_short = client.post("/api/v1/opportunity-submissions", json={"input_mode": "text", "text": "ab"}, headers=headers)
    assert res_short.status_code == 400
    assert "EMPTY_SUBMISSION" in str(res_short.json())

def test_submission_too_long_rejected():
    _, headers = create_test_actor(role="beneficiary")

    long_text = "Opportunity description " * 100 # > 2000 characters
    res_long = client.post("/api/v1/opportunity-submissions", json={"input_mode": "text", "text": long_text}, headers=headers)
    assert res_long.status_code == 400
    assert "SUBMISSION_TOO_LONG" in str(res_long.json())

def test_verification_first_invariant_no_direct_activation():
    """
    Submissions enter SUBMITTED state and NEVER directly alter active opportunities
    or recommendations without staff verification.
    """
    _, headers = create_test_actor(role="beneficiary")

    payload = {
        "input_mode": "text",
        "text": "Automotive repair shop hiring 5 apprentices immediately."
    }
    res = client.post("/api/v1/opportunity-submissions", json=payload, headers=headers)
    assert res.status_code == 201
    sub_id = res.json()["id"]

    # Verify that this submission is in SUBMITTED state
    with get_db() as conn:
        row = conn.execute("SELECT status, linked_opportunity_id FROM opportunity_submissions WHERE id = ?", (sub_id,)).fetchone()
        assert row["status"] == "SUBMITTED"
        assert row["linked_opportunity_id"] is None

        # Verify it has NOT been inserted directly into local_opportunities
        opp = conn.execute("SELECT id FROM local_opportunities WHERE title LIKE '%Automotive repair%'").fetchone()
        assert opp is None

def test_beneficiary_my_submissions():
    ben_id, headers = create_test_actor(role="beneficiary")

    # Submit 2 items
    client.post("/api/v1/opportunity-submissions", json={"input_mode": "text", "text": "Submission 1 for my list"}, headers=headers)
    client.post("/api/v1/opportunity-submissions", json={"input_mode": "text", "text": "Submission 2 for my list"}, headers=headers)

    res = client.get("/api/v1/opportunity-submissions/me", headers=headers)
    assert res.status_code == 200
    items = res.json()
    assert len(items) >= 2
    assert all(it["submitted_by_user_id"] == ben_id for it in items)

def test_staff_review_lifecycle_and_linking():
    ben_id, ben_headers = create_test_actor(role="beneficiary")
    staff_id, staff_headers = create_test_actor(role="field_worker")

    # Create submission
    res_create = client.post("/api/v1/opportunity-submissions", json={
        "input_mode": "text",
        "text": "Electronics service centre needing 3 junior technicians."
    }, headers=ben_headers)
    sub_id = res_create.json()["id"]

    # Staff list submissions
    res_list = client.get("/api/v1/staff/opportunity-submissions?status=SUBMITTED", headers=staff_headers)
    assert res_list.status_code == 200
    assert any(s["id"] == sub_id for s in res_list.json())

    # Staff transition to UNDER_REVIEW
    res_reviewing = client.patch(f"/api/v1/staff/opportunity-submissions/{sub_id}", json={
        "status": "UNDER_REVIEW",
        "review_notes": "Contacting centre manager to verify vacancy authenticity."
    }, headers=staff_headers)
    assert res_reviewing.status_code == 200
    assert res_reviewing.json()["status"] == "UNDER_REVIEW"
    assert res_reviewing.json()["reviewed_by_user_id"] == staff_id

    # Linking to non-existent opportunity returns 400
    res_bad_link = client.patch(f"/api/v1/staff/opportunity-submissions/{sub_id}", json={
        "status": "LINKED_TO_OPPORTUNITY",
        "linked_opportunity_id": "non_existent_opp_id"
    }, headers=staff_headers)
    assert res_bad_link.status_code == 400

    # Create a real opportunity to link to
    now = datetime.now(timezone.utc).isoformat()
    real_opp_id = f"opp_{uuid.uuid4().hex[:8]}"
    with get_db() as conn:
        conn.execute("""
            INSERT INTO local_opportunities (
                id, provider_id, qualification_id, title, summary, district_id,
                delivery_mode, status, created_by_user_id, updated_by_user_id, created_at, updated_at
            ) VALUES (?, 'prov_test', 'qual_test', 'Junior Electronics Tech', 'Apprenticeship', 'Moradabad', 'OFFLINE', 'VERIFIED', ?, ?, ?, ?);
        """, (real_opp_id, staff_id, staff_id, now, now))
        conn.commit()

    # Link submission to verified opportunity
    res_link = client.patch(f"/api/v1/staff/opportunity-submissions/{sub_id}", json={
        "status": "LINKED_TO_OPPORTUNITY",
        "linked_opportunity_id": real_opp_id,
        "review_notes": "Verified in person and linked to active batch."
    }, headers=staff_headers)
    assert res_link.status_code == 200
    assert res_link.json()["status"] == "LINKED_TO_OPPORTUNITY"
    assert res_link.json()["linked_opportunity_id"] == real_opp_id
