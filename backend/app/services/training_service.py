import uuid
import json
from datetime import datetime, timezone
from sqlite3 import Connection
from app.schemas.training import (
    TrainingCourseCreate, TrainingCourseUpdate,
    ContentFeedbackCreate
)

class TrainingService:
    @staticmethod
    def _now():
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def list_courses(conn: Connection, sector: str = None, language: str = None):
        query = "SELECT * FROM training_courses WHERE is_published = 1"
        params = []
        if sector:
            query += " AND sector = ?"
            params.append(sector)
        if language:
            query += " AND language_code = ?"
            params.append(language)
            
        cursor = conn.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def get_course(conn: Connection, course_id: str):
        row = conn.execute("SELECT * FROM training_courses WHERE id = ? AND is_published = 1", (course_id,)).fetchone()
        return dict(row) if row else None

    @staticmethod
    def get_course_modules(conn: Connection, course_id: str):
        cursor = conn.execute("SELECT * FROM training_modules WHERE course_id = ? AND is_published = 1 ORDER BY sequence_number", (course_id,))
        modules = [dict(row) for row in cursor.fetchall()]
        for m in modules:
            m['learning_objectives'] = json.loads(m['learning_objectives']) if isinstance(m['learning_objectives'], str) else m['learning_objectives']
        return modules

    @staticmethod
    def get_module_lessons(conn: Connection, module_id: str):
        cursor = conn.execute("SELECT * FROM training_lessons WHERE module_id = ? ORDER BY sequence_number", (module_id,))
        lessons = [dict(row) for row in cursor.fetchall()]
        for l in lessons:
            l['key_points'] = json.loads(l['key_points']) if isinstance(l['key_points'], str) else l['key_points']
            l['practical_steps'] = json.loads(l['practical_steps']) if isinstance(l['practical_steps'], str) else l['practical_steps']
            l['safety_notes'] = json.loads(l['safety_notes']) if isinstance(l['safety_notes'], str) else l['safety_notes']
            l['quiz_questions'] = json.loads(l['quiz_questions']) if l['quiz_questions'] else None
            l['source_references'] = json.loads(l['source_references']) if isinstance(l['source_references'], str) else l['source_references']
        return lessons

    @staticmethod
    def get_lesson(conn: Connection, lesson_id: str):
        row = conn.execute("SELECT * FROM training_lessons WHERE id = ?", (lesson_id,)).fetchone()
        if not row:
            return None
        l = dict(row)
        l['key_points'] = json.loads(l['key_points']) if isinstance(l['key_points'], str) else l['key_points']
        l['practical_steps'] = json.loads(l['practical_steps']) if isinstance(l['practical_steps'], str) else l['practical_steps']
        l['safety_notes'] = json.loads(l['safety_notes']) if isinstance(l['safety_notes'], str) else l['safety_notes']
        l['quiz_questions'] = json.loads(l['quiz_questions']) if l['quiz_questions'] else None
        l['source_references'] = json.loads(l['source_references']) if isinstance(l['source_references'], str) else l['source_references']
        return l

    @staticmethod
    def get_lesson_resources(conn: Connection, lesson_id: str):
        cursor = conn.execute("SELECT * FROM training_resources WHERE lesson_id = ?", (lesson_id,))
        return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def submit_feedback(conn: Connection, beneficiary_id: str, data: ContentFeedbackCreate):
        fid = f"fb_{uuid.uuid4().hex[:8]}"
        conn.execute("""
            INSERT INTO content_feedback (id, beneficiary_id, course_id, lesson_id, rating, feedback_type, comment, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (fid, beneficiary_id, data.course_id, data.lesson_id, data.rating, data.feedback_type, data.comment, TrainingService._now()))
        return {"success": True, "id": fid}

    @staticmethod
    def create_course(conn: Connection, data: TrainingCourseCreate):
        cid = f"course_{uuid.uuid4().hex[:8]}"
        now = TrainingService._now()
        conn.execute("""
            INSERT INTO training_courses (
                id, title, slug, short_description, long_description, sector,
                nsqf_level, duration_hours, difficulty, language_code, thumbnail_url,
                source_name, source_url, verification_status, verified_at, last_updated_at, is_published
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            cid, data.title, data.slug, data.short_description, data.long_description, data.sector,
            data.nsqf_level, data.duration_hours, data.difficulty, data.language_code, data.thumbnail_url,
            data.source_name, data.source_url, data.verification_status, now if data.verification_status == 'Verified' else None, now, 1 if data.is_published else 0
        ))
        return TrainingService.get_course(conn, cid)
