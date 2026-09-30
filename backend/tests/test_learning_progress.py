import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db, init_database
import os
import tempfile
from app.config import settings
from app.core.security import hasher

@pytest.fixture(scope="module")
def client():
    orig_db = settings.DATABASE_PATH
    temp_dir = tempfile.TemporaryDirectory()
    settings.DATABASE_PATH = os.path.join(temp_dir.name, "test_learning.db")
    init_database()

    with get_db() as conn:
        pw_hash = hasher.hash("SecurePassword123!")
        conn.execute("""
            INSERT INTO users (id, email, password_hash, display_name, is_active, is_superuser, created_at, updated_at)
            VALUES ('usr_learn1', 'learn@example.com', ?, 'Learner 1', 1, 0, '2026-09-30T00:00:00Z', '2026-09-30T00:00:00Z')
        """, (pw_hash,))
        
        conn.execute("""
            INSERT INTO users (id, email, password_hash, display_name, is_active, is_superuser, created_at, updated_at)
            VALUES ('usr_learn2', 'learn2@example.com', ?, 'Learner 2', 1, 0, '2026-09-30T00:00:00Z', '2026-09-30T00:00:00Z')
        """, (pw_hash,))
        
        role = conn.execute("SELECT id FROM roles WHERE key = 'beneficiary'").fetchone()["id"]
        conn.execute("INSERT INTO user_roles (user_id, role_id, assigned_at) VALUES ('usr_learn1', ?, '2026-09-30T00:00:00Z')", (role,))
        conn.execute("INSERT INTO user_roles (user_id, role_id, assigned_at) VALUES ('usr_learn2', ?, '2026-09-30T00:00:00Z')", (role,))

        # Create a course with 2 lessons
        conn.execute("""
            INSERT INTO training_courses (id, title, slug, short_description, long_description, sector, source_name, is_published, verification_status, last_updated_at)
            VALUES ('course_1', 'Course 1', 'course-1', 'desc', 'desc', 'Tech', 'Internal', 1, 'Verified', '2026-09-30T00:00:00Z')
        """)
        conn.execute("""
            INSERT INTO training_modules (id, course_id, title, sequence_number, estimated_minutes, summary, is_published, learning_objectives)
            VALUES ('mod_1', 'course_1', 'Module 1', 1, 30, 'summary', 1, '{}')
        """)
        conn.execute("""
            INSERT INTO training_lessons (id, module_id, title, sequence_number, content_markdown, plain_language_summary, key_points, practical_steps, safety_notes, source_references, last_reviewed_at)
            VALUES ('les_1', 'mod_1', 'Lesson 1', 1, 'Content', 'Summary', '{}', '{}', '{}', '{}', '2026-09-30T00:00:00Z')
        """)
        conn.execute("""
            INSERT INTO training_lessons (id, module_id, title, sequence_number, content_markdown, plain_language_summary, key_points, practical_steps, safety_notes, source_references, last_reviewed_at)
            VALUES ('les_2', 'mod_1', 'Lesson 2', 2, 'Content', 'Summary', '{}', '{}', '{}', '{}', '2026-09-30T00:00:00Z')
        """)
        # Create an unpublished module in the same course to test unpublished lessons don't affect progress
        conn.execute("""
            INSERT INTO training_modules (id, course_id, title, sequence_number, estimated_minutes, summary, is_published, learning_objectives)
            VALUES ('mod_2_unpub', 'course_1', 'Module 2 (Unpub)', 2, 30, 'summary', 0, '{}')
        """)
        conn.execute("""
            INSERT INTO training_lessons (id, module_id, title, sequence_number, content_markdown, plain_language_summary, key_points, practical_steps, safety_notes, source_references, last_reviewed_at)
            VALUES ('les_4_unpub', 'mod_2_unpub', 'Lesson 4 (Unpub)', 1, 'Content', 'Summary', '{}', '{}', '{}', '{}', '2026-09-30T00:00:00Z')
        """)

    with TestClient(app) as c:
        yield c

    settings.DATABASE_PATH = orig_db
    temp_dir.cleanup()

@pytest.fixture
def auth_header(client):
    res = client.post("/api/v1/auth/login", json={
        "email_or_phone": "learn@example.com",
        "password": "SecurePassword123!"
    })
    return {"Authorization": f"Bearer {res.json()['access_token']}"}

@pytest.fixture
def auth_header_2(client):
    res = client.post("/api/v1/auth/login", json={
        "email_or_phone": "learn2@example.com",
        "password": "SecurePassword123!"
    })
    return {"Authorization": f"Bearer {res.json()['access_token']}"}

def test_unauthenticated_access_denied(client):
    assert client.get("/api/v1/learning/me/overview").status_code == 401
    assert client.post("/api/v1/learning/me/lessons/les_1/access").status_code == 401

def test_record_lesson_access(client, auth_header):
    res = client.post("/api/v1/learning/me/lessons/les_1/access", headers=auth_header)
    assert res.status_code == 200
    
    # Check overview
    overview = client.get("/api/v1/learning/me/overview", headers=auth_header).json()
    assert overview["inProgressCourses"] == 1
    assert overview["completedCourses"] == 0
    
    course = overview["recentCourses"][0]
    assert course["courseId"] == "course_1"
    assert course["completionPercent"] == 0
    assert course["resumeLessonId"] == "les_1"

def test_mark_lesson_complete(client, auth_header):
    res = client.put("/api/v1/learning/me/lessons/les_1/completion", headers=auth_header)
    assert res.status_code == 200
    
    # Course should now be 50% (1 out of 2 published lessons)
    detail = client.get("/api/v1/learning/me/courses/course_1", headers=auth_header).json()
    assert detail["completionPercent"] == 50
    assert detail["completedLessons"] == 1
    assert detail["totalLessons"] == 2
    assert detail["courseStatus"] == "IN_PROGRESS"
    # Resume should move to les_2 automatically
    assert detail["resumeLessonId"] == "les_2"

def test_mark_lesson_complete_idempotent(client, auth_header):
    res = client.put("/api/v1/learning/me/lessons/les_1/completion", headers=auth_header)
    assert res.status_code == 200
    
    # Still 50%
    detail = client.get("/api/v1/learning/me/courses/course_1", headers=auth_header).json()
    assert detail["completedLessons"] == 1

def test_mark_second_lesson_complete_completes_course(client, auth_header):
    client.put("/api/v1/learning/me/lessons/les_2/completion", headers=auth_header)
    
    detail = client.get("/api/v1/learning/me/courses/course_1", headers=auth_header).json()
    assert detail["completionPercent"] == 100
    assert detail["courseStatus"] == "COMPLETED"
    
    # Resume should point to the last completed lesson when course is done
    assert detail["resumeLessonId"] == "les_2"

def test_reset_lesson_completion(client, auth_header):
    res = client.delete("/api/v1/learning/me/lessons/les_2/completion", headers=auth_header)
    assert res.status_code == 200
    
    detail = client.get("/api/v1/learning/me/courses/course_1", headers=auth_header).json()
    assert detail["completionPercent"] == 50
    assert detail["courseStatus"] == "IN_PROGRESS"
    assert detail["resumeLessonId"] == "les_2"

def test_bookmark_lifecycle(client, auth_header):
    res = client.put("/api/v1/learning/me/lessons/les_1/bookmark", headers=auth_header)
    assert res.status_code == 200
    
    detail = client.get("/api/v1/learning/me/courses/course_1", headers=auth_header).json()
    assert "les_1" in detail["bookmarked_lesson_ids"]
    
    res = client.delete("/api/v1/learning/me/lessons/les_1/bookmark", headers=auth_header)
    assert res.status_code == 200
    
    detail = client.get("/api/v1/learning/me/courses/course_1", headers=auth_header).json()
    assert "les_1" not in detail["bookmarked_lesson_ids"]

def test_unpublished_lesson_access_blocked(client, auth_header):
    res = client.post("/api/v1/learning/me/lessons/les_4_unpub/access", headers=auth_header)
    assert res.status_code == 400

def test_user_data_isolation(client, auth_header, auth_header_2):
    # User 1 has progress. User 2 should see empty.
    overview = client.get("/api/v1/learning/me/overview", headers=auth_header_2).json()
    assert overview["inProgressCourses"] == 0
    assert overview["completedCourses"] == 0
    assert len(overview["recentCourses"]) == 0
    
    # If user 2 accesses les_2, it doesn't affect user 1
    client.put("/api/v1/learning/me/lessons/les_2/completion", headers=auth_header_2)
    detail2 = client.get("/api/v1/learning/me/courses/course_1", headers=auth_header_2).json()
    assert detail2["completionPercent"] == 50
    
    detail1 = client.get("/api/v1/learning/me/courses/course_1", headers=auth_header).json()
    assert detail1["completionPercent"] == 50
