from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from app.database import get_db
from app.schemas.training import (
    TrainingCourseCreate, TrainingCourseUpdate,
    TrainingModuleCreate, TrainingModuleUpdate,
    TrainingLessonCreate, TrainingLessonUpdate,
    TrainingResourceCreate,
    LearnerCourseProgressUpdate, LearnerLessonProgressUpdate,
    ContentFeedbackCreate
)
from app.services.training_service import TrainingService

router = APIRouter(prefix="/api/v1/training", tags=["Skill Training"])
learning_router = APIRouter(prefix="/api/v1/learning", tags=["Skill Training - Learning"])
admin_router = APIRouter(prefix="/api/v1/admin/training", tags=["Skill Training - Admin"])

# ============================================================================
# Public Catalogue Endpoints
# ============================================================================

@router.get("/courses")
def list_courses(sector: Optional[str] = None, language: Optional[str] = None):
    with get_db() as conn:
        return TrainingService.list_courses(conn, sector=sector, language=language)

@router.get("/courses/{course_id}")
def get_course(course_id: str):
    with get_db() as conn:
        course = TrainingService.get_course(conn, course_id)
        if not course:
            raise HTTPException(status_code=404, detail="This course is currently unavailable.")
        return course

@router.get("/courses/{course_id}/modules")
def get_course_modules(course_id: str):
    with get_db() as conn:
        return TrainingService.get_course_modules(conn, course_id)

@router.get("/modules/{module_id}")
def get_module_lessons(module_id: str):
    with get_db() as conn:
        return TrainingService.get_module_lessons(conn, module_id)

@router.get("/lessons/{lesson_id}")
def get_lesson(lesson_id: str):
    with get_db() as conn:
        lesson = TrainingService.get_lesson(conn, lesson_id)
        if not lesson:
            raise HTTPException(status_code=404, detail="Lesson not found.")
        return lesson

@router.get("/lessons/{lesson_id}/resources")
def get_lesson_resources(lesson_id: str):
    with get_db() as conn:
        return TrainingService.get_lesson_resources(conn, lesson_id)

# ============================================================================
# Learning Progress Endpoints
# ============================================================================

@learning_router.get("/me/courses")
def get_my_courses(beneficiary_id: str = "ben_rajesh_kumar"):
    # Hardcoding ben_rajesh_kumar for demo
    with get_db() as conn:
        return TrainingService.get_user_courses(conn, beneficiary_id)

@learning_router.get("/me/courses/{course_id}/progress")
def get_course_progress(course_id: str, beneficiary_id: str = "ben_rajesh_kumar"):
    with get_db() as conn:
        return TrainingService.get_course_progress(conn, beneficiary_id, course_id)

@learning_router.post("/courses/{course_id}/start")
def start_course(course_id: str, beneficiary_id: str = "ben_rajesh_kumar"):
    with get_db() as conn:
        return TrainingService.start_course(conn, beneficiary_id, course_id)

@learning_router.patch("/lessons/{lesson_id}/progress")
def update_lesson_progress(lesson_id: str, data: LearnerLessonProgressUpdate, beneficiary_id: str = "ben_rajesh_kumar"):
    with get_db() as conn:
        return TrainingService.update_lesson_progress(conn, beneficiary_id, lesson_id, data)

@learning_router.post("/lessons/{lesson_id}/bookmark")
def bookmark_lesson(lesson_id: str, beneficiary_id: str = "ben_rajesh_kumar"):
    with get_db() as conn:
        return TrainingService.bookmark_lesson(conn, beneficiary_id, lesson_id, bookmark=True)

@learning_router.delete("/lessons/{lesson_id}/bookmark")
def unbookmark_lesson(lesson_id: str, beneficiary_id: str = "ben_rajesh_kumar"):
    with get_db() as conn:
        return TrainingService.bookmark_lesson(conn, beneficiary_id, lesson_id, bookmark=False)

@learning_router.post("/feedback")
def submit_feedback(data: ContentFeedbackCreate, beneficiary_id: str = "ben_rajesh_kumar"):
    with get_db() as conn:
        return TrainingService.submit_feedback(conn, beneficiary_id, data)

# ============================================================================
# Admin Endpoints (Skipping auth for mock)
# ============================================================================

@admin_router.post("/courses")
def create_course(data: TrainingCourseCreate):
    with get_db() as conn:
        return TrainingService.create_course(conn, data)
