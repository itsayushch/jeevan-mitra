import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from fastapi import HTTPException
from app.utils.audit_events import log_audit_event

class LearningProgressService:

    @staticmethod
    def get_user_learning_overview(conn, user_id: str) -> Dict[str, Any]:
        # Count in-progress courses (using the new user_course_learning_state table)
        in_prog_count = conn.execute(
            "SELECT count(*) as c FROM user_course_learning_state WHERE user_id = ? AND completed_at IS NULL",
            (user_id,)
        ).fetchone()["c"]
        
        # Count completed courses
        comp_count = conn.execute(
            "SELECT count(*) as c FROM user_course_learning_state WHERE user_id = ? AND completed_at IS NOT NULL",
            (user_id,)
        ).fetchone()["c"]
        
        # Count bookmarked lessons
        bm_count = conn.execute(
            "SELECT count(*) as c FROM user_lesson_bookmarks WHERE user_id = ?",
            (user_id,)
        ).fetchone()["c"]
        
        # Get recent courses
        recent_states = conn.execute(
            "SELECT course_id, last_accessed_at, completed_at FROM user_course_learning_state WHERE user_id = ? ORDER BY last_accessed_at DESC LIMIT 5",
            (user_id,)
        ).fetchall()
        
        recent_courses = []
        for state in recent_states:
            course_id = state["course_id"]
            
            # Recompute on the fly or just use the formula
            course = conn.execute("SELECT title, thumbnail_url FROM training_courses WHERE id = ?", (course_id,)).fetchone()
            if not course:
                continue
                
            total_lessons = conn.execute(
                "SELECT count(*) as c FROM training_lessons l JOIN training_modules m ON l.module_id = m.id WHERE m.course_id = ? AND m.is_published = 1",
                (course_id,)
            ).fetchone()["c"]
            
            completed_lessons = conn.execute(
                "SELECT count(*) as c FROM user_lesson_progress WHERE user_id = ? AND course_id = ? AND status = 'COMPLETED'",
                (user_id, course_id)
            ).fetchone()["c"]
            
            percent = (completed_lessons * 100 // total_lessons) if total_lessons > 0 else 0
            
            # Determine resume lesson
            resume_lesson = LearningProgressService.get_resume_lesson(conn, user_id, course_id)
            resume_title = None
            if resume_lesson:
                lesson_row = conn.execute("SELECT title FROM training_lessons WHERE id = ?", (resume_lesson,)).fetchone()
                if lesson_row:
                    resume_title = lesson_row["title"]
                    
            status = "COMPLETED" if state["completed_at"] else "IN_PROGRESS"
            if percent == 100 and total_lessons > 0:
                status = "COMPLETED"
            
            recent_courses.append({
                "courseId": course_id,
                "title": course["title"],
                "thumbnailUrl": course["thumbnail_url"],
                "completedLessons": completed_lessons,
                "totalLessons": total_lessons,
                "completionPercent": percent,
                "lastAccessedAt": state["last_accessed_at"],
                "resumeLessonId": resume_lesson,
                "resumeLessonTitle": resume_title,
                "courseStatus": status
            })

        return {
            "inProgressCourses": in_prog_count,
            "completedCourses": comp_count,
            "bookmarkedLessons": bm_count,
            "recentCourses": recent_courses
        }
        
    @staticmethod
    def get_course_progress(conn, user_id: str, course_id: str) -> Dict[str, Any]:
        course = conn.execute("SELECT title FROM training_courses WHERE id = ?", (course_id,)).fetchone()
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")
            
        total_lessons = conn.execute(
            "SELECT count(*) as c FROM training_lessons l JOIN training_modules m ON l.module_id = m.id WHERE m.course_id = ? AND m.is_published = 1",
            (course_id,)
        ).fetchone()["c"]
        
        completed_lessons = conn.execute(
            "SELECT count(*) as c FROM user_lesson_progress WHERE user_id = ? AND course_id = ? AND status = 'COMPLETED'",
            (user_id, course_id)
        ).fetchone()["c"]
        
        percent = (completed_lessons * 100 // total_lessons) if total_lessons > 0 else 0
        status = "COMPLETED" if (percent == 100 and total_lessons > 0) else "IN_PROGRESS"
        if total_lessons == 0:
            status = "NOT_STARTED"
            
        state = conn.execute("SELECT last_accessed_at FROM user_course_learning_state WHERE user_id = ? AND course_id = ?", (user_id, course_id)).fetchone()
        
        lessons_prog = conn.execute(
            "SELECT * FROM user_lesson_progress WHERE user_id = ? AND course_id = ?",
            (user_id, course_id)
        ).fetchall()
        
        bookmarks = conn.execute(
            "SELECT lesson_id FROM user_lesson_bookmarks b JOIN training_lessons l ON b.lesson_id = l.id JOIN training_modules m ON l.module_id = m.id WHERE b.user_id = ? AND m.course_id = ?",
            (user_id, course_id)
        ).fetchall()
        
        return {
            "courseId": course_id,
            "title": course["title"],
            "completedLessons": completed_lessons,
            "totalLessons": total_lessons,
            "completionPercent": percent,
            "courseStatus": status,
            "lastAccessedAt": state["last_accessed_at"] if state else None,
            "resumeLessonId": LearningProgressService.get_resume_lesson(conn, user_id, course_id),
            "lessons_progress": [dict(lp) for lp in lessons_prog],
            "bookmarked_lesson_ids": [b["lesson_id"] for b in bookmarks]
        }

    @staticmethod
    def get_resume_lesson(conn, user_id: str, course_id: str) -> Optional[str]:
        # 1. Most recently accessed incomplete lesson in the course
        recent_incomplete = conn.execute("""
            SELECT l.id FROM user_lesson_progress up
            JOIN training_lessons l ON up.lesson_id = l.id
            JOIN training_modules m ON l.module_id = m.id
            WHERE up.user_id = ? AND m.course_id = ? AND up.status != 'COMPLETED' AND m.is_published = 1
            ORDER BY up.last_accessed_at DESC LIMIT 1
        """, (user_id, course_id)).fetchone()
        
        if recent_incomplete:
            return recent_incomplete["id"]
            
        # 2. First incomplete active/published lesson ordered by module position then lesson position
        all_lessons = conn.execute("""
            SELECT l.id, up.status 
            FROM training_lessons l
            JOIN training_modules m ON l.module_id = m.id
            LEFT JOIN user_lesson_progress up ON l.id = up.lesson_id AND up.user_id = ?
            WHERE m.course_id = ? AND m.is_published = 1
            ORDER BY m.sequence_number ASC, l.sequence_number ASC
        """, (user_id, course_id)).fetchall()
        
        if not all_lessons:
            return None
            
        for l in all_lessons:
            if not l["status"] or l["status"] != 'COMPLETED':
                return l["id"]
                
        # 3. Most recently completed lesson if every lesson is complete
        recent_complete = conn.execute("""
            SELECT l.id FROM user_lesson_progress up
            JOIN training_lessons l ON up.lesson_id = l.id
            JOIN training_modules m ON l.module_id = m.id
            WHERE up.user_id = ? AND m.course_id = ? AND up.status = 'COMPLETED' AND m.is_published = 1
            ORDER BY up.completed_at DESC LIMIT 1
        """, (user_id, course_id)).fetchone()
        
        if recent_complete:
            return recent_complete["id"]
            
        return None

    @staticmethod
    def _validate_lesson_and_get_course(conn, lesson_id: str) -> str:
        res = conn.execute("""
            SELECT m.course_id, m.is_published, c.is_published as course_published 
            FROM training_lessons l 
            JOIN training_modules m ON l.module_id = m.id 
            JOIN training_courses c ON m.course_id = c.id
            WHERE l.id = ?
        """, (lesson_id,)).fetchone()
        
        if not res:
            raise HTTPException(status_code=404, detail="Lesson not found")
        if not res["is_published"] or not res["course_published"]:
            raise HTTPException(status_code=400, detail="Lesson or course is not active/published")
            
        return res["course_id"]

    @staticmethod
    def _update_course_state(conn, user_id: str, course_id: str, now: str, lesson_id: Optional[str] = None):
        state = conn.execute("SELECT * FROM user_course_learning_state WHERE user_id = ? AND course_id = ?", (user_id, course_id)).fetchone()
        
        # Calculate completion
        total_lessons = conn.execute(
            "SELECT count(*) as c FROM training_lessons l JOIN training_modules m ON l.module_id = m.id WHERE m.course_id = ? AND m.is_published = 1",
            (course_id,)
        ).fetchone()["c"]
        
        completed_lessons = conn.execute(
            "SELECT count(*) as c FROM user_lesson_progress WHERE user_id = ? AND course_id = ? AND status = 'COMPLETED'",
            (user_id, course_id)
        ).fetchone()["c"]
        
        is_completed = (total_lessons > 0 and completed_lessons == total_lessons)
        completed_at = now if is_completed else None
        
        if not state:
            conn.execute("""
                INSERT INTO user_course_learning_state (user_id, course_id, first_started_at, last_accessed_at, last_lesson_id, completed_at, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (user_id, course_id, now, now, lesson_id, completed_at, now, now))
        else:
            # Only update completed_at if transitioning to completed
            new_completed_at = state["completed_at"]
            if is_completed and not new_completed_at:
                new_completed_at = now
            elif not is_completed:
                new_completed_at = None
                
            conn.execute("""
                UPDATE user_course_learning_state 
                SET last_accessed_at = ?, last_lesson_id = COALESCE(?, last_lesson_id), completed_at = ?, updated_at = ?
                WHERE user_id = ? AND course_id = ?
            """, (now, lesson_id, new_completed_at, now, user_id, course_id))

    @staticmethod
    def record_lesson_access(conn, user_id: str, lesson_id: str):
        course_id = LearningProgressService._validate_lesson_and_get_course(conn, lesson_id)
        now = datetime.now(timezone.utc).isoformat()
        
        prog = conn.execute("SELECT status FROM user_lesson_progress WHERE user_id = ? AND lesson_id = ?", (user_id, lesson_id)).fetchone()
        if not prog:
            conn.execute("""
                INSERT INTO user_lesson_progress (id, user_id, lesson_id, course_id, status, started_at, last_accessed_at, created_at, updated_at)
                VALUES (?, ?, ?, ?, 'IN_PROGRESS', ?, ?, ?, ?)
            """, (f"ulp_{uuid.uuid4().hex[:12]}", user_id, lesson_id, course_id, now, now, now, now))
            log_audit_event(conn, user_id, "User", "beneficiary", "learning.lesson_started", "user_lesson_progress", lesson_id, metadata={"course_id": course_id})
        else:
            conn.execute("""
                UPDATE user_lesson_progress SET last_accessed_at = ?, updated_at = ? WHERE user_id = ? AND lesson_id = ?
            """, (now, now, user_id, lesson_id))
            
        LearningProgressService._update_course_state(conn, user_id, course_id, now, lesson_id)
        conn.commit()
        return {"status": "success"}

    @staticmethod
    def mark_lesson_complete(conn, user_id: str, lesson_id: str):
        course_id = LearningProgressService._validate_lesson_and_get_course(conn, lesson_id)
        now = datetime.now(timezone.utc).isoformat()
        
        prog = conn.execute("SELECT status, completed_at FROM user_lesson_progress WHERE user_id = ? AND lesson_id = ?", (user_id, lesson_id)).fetchone()
        
        if not prog:
            conn.execute("""
                INSERT INTO user_lesson_progress (id, user_id, lesson_id, course_id, status, started_at, completed_at, last_accessed_at, completion_source, created_at, updated_at)
                VALUES (?, ?, ?, ?, 'COMPLETED', ?, ?, ?, 'USER_MARKED', ?, ?)
            """, (f"ulp_{uuid.uuid4().hex[:12]}", user_id, lesson_id, course_id, now, now, now, now, now))
            log_audit_event(conn, user_id, "User", "beneficiary", "learning.lesson_completed", "user_lesson_progress", lesson_id, metadata={"course_id": course_id})
        elif prog["status"] != "COMPLETED":
            conn.execute("""
                UPDATE user_lesson_progress SET status = 'COMPLETED', completed_at = ?, last_accessed_at = ?, completion_source = 'USER_MARKED', updated_at = ?
                WHERE user_id = ? AND lesson_id = ?
            """, (now, now, now, user_id, lesson_id))
            log_audit_event(conn, user_id, "User", "beneficiary", "learning.lesson_completed", "user_lesson_progress", lesson_id, metadata={"course_id": course_id})
        else:
            # Already completed, update last_accessed_at only
            conn.execute("""
                UPDATE user_lesson_progress SET last_accessed_at = ?, updated_at = ? WHERE user_id = ? AND lesson_id = ?
            """, (now, now, user_id, lesson_id))
            
        LearningProgressService._update_course_state(conn, user_id, course_id, now, lesson_id)
        conn.commit()
        return {"status": "success"}

    @staticmethod
    def reset_lesson_completion(conn, user_id: str, lesson_id: str):
        course_id = LearningProgressService._validate_lesson_and_get_course(conn, lesson_id)
        now = datetime.now(timezone.utc).isoformat()
        
        prog = conn.execute("SELECT status FROM user_lesson_progress WHERE user_id = ? AND lesson_id = ?", (user_id, lesson_id)).fetchone()
        if prog and prog["status"] == "COMPLETED":
            conn.execute("""
                UPDATE user_lesson_progress SET status = 'IN_PROGRESS', completed_at = NULL, last_accessed_at = ?, updated_at = ?
                WHERE user_id = ? AND lesson_id = ?
            """, (now, now, user_id, lesson_id))
            log_audit_event(conn, user_id, "User", "beneficiary", "learning.lesson_completion_reset", "user_lesson_progress", lesson_id, metadata={"course_id": course_id})
            
        LearningProgressService._update_course_state(conn, user_id, course_id, now, lesson_id)
        conn.commit()
        return LearningProgressService.get_course_progress(conn, user_id, course_id)

    @staticmethod
    def add_bookmark(conn, user_id: str, lesson_id: str):
        LearningProgressService._validate_lesson_and_get_course(conn, lesson_id)
        now = datetime.now(timezone.utc).isoformat()
        
        exist = conn.execute("SELECT id FROM user_lesson_bookmarks WHERE user_id = ? AND lesson_id = ?", (user_id, lesson_id)).fetchone()
        if not exist:
            b_id = f"bm_{uuid.uuid4().hex[:12]}"
            conn.execute("INSERT INTO user_lesson_bookmarks (id, user_id, lesson_id, created_at) VALUES (?, ?, ?, ?)", (b_id, user_id, lesson_id, now))
            log_audit_event(conn, user_id, "User", "beneficiary", "learning.bookmark_added", "user_lesson_bookmarks", lesson_id)
            conn.commit()
        return {"status": "success"}

    @staticmethod
    def remove_bookmark(conn, user_id: str, lesson_id: str):
        exist = conn.execute("SELECT id FROM user_lesson_bookmarks WHERE user_id = ? AND lesson_id = ?", (user_id, lesson_id)).fetchone()
        if exist:
            conn.execute("DELETE FROM user_lesson_bookmarks WHERE id = ?", (exist["id"],))
            log_audit_event(conn, user_id, "User", "beneficiary", "learning.bookmark_removed", "user_lesson_bookmarks", lesson_id)
            conn.commit()
        return {"status": "success"}
