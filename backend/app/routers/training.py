from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from app.database import get_db
from app.schemas.training import (
    TrainingCourseCreate, TrainingCourseUpdate,
    TrainingModuleCreate, TrainingModuleUpdate,
    TrainingLessonCreate, TrainingLessonUpdate,
    TrainingResourceCreate,
    ContentFeedbackCreate
)
from app.services.training_service import TrainingService
from app.dependencies.auth import require_authenticated_user, require_roles, Actor

router = APIRouter(prefix="/training", tags=["Skill Training"])
learning_router = APIRouter(
    prefix="/learning", 
    tags=["Skill Training - Learning"],
    dependencies=[Depends(require_authenticated_user)]
)
admin_router = APIRouter(
    prefix="/admin/training", 
    tags=["Skill Training - Admin"],
    dependencies=[Depends(require_roles(["catalogue_manager", "super_admin"]))]
)

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

from app.services.learning_progress_service import LearningProgressService
from app.schemas.training import LearningOverviewResponse, CourseProgressDetailResponse

@learning_router.get("/me/overview", response_model=LearningOverviewResponse)
def get_user_learning_overview(actor: Actor = Depends(require_authenticated_user)):
    with get_db() as conn:
        return LearningProgressService.get_user_learning_overview(conn, actor.actor_id)

@learning_router.get("/me/courses/{course_id}", response_model=CourseProgressDetailResponse)
def get_course_progress(course_id: str, actor: Actor = Depends(require_authenticated_user)):
    with get_db() as conn:
        return LearningProgressService.get_course_progress(conn, actor.actor_id, course_id)

@learning_router.post("/me/lessons/{lesson_id}/access")
def record_lesson_access(lesson_id: str, actor: Actor = Depends(require_authenticated_user)):
    with get_db() as conn:
        return LearningProgressService.record_lesson_access(conn, actor.actor_id, lesson_id)

@learning_router.put("/me/lessons/{lesson_id}/completion")
def mark_lesson_complete(lesson_id: str, actor: Actor = Depends(require_authenticated_user)):
    with get_db() as conn:
        return LearningProgressService.mark_lesson_complete(conn, actor.actor_id, lesson_id)

@learning_router.delete("/me/lessons/{lesson_id}/completion")
def reset_lesson_completion(lesson_id: str, actor: Actor = Depends(require_authenticated_user)):
    with get_db() as conn:
        return LearningProgressService.reset_lesson_completion(conn, actor.actor_id, lesson_id)

@learning_router.put("/me/lessons/{lesson_id}/bookmark")
def add_bookmark(lesson_id: str, actor: Actor = Depends(require_authenticated_user)):
    with get_db() as conn:
        return LearningProgressService.add_bookmark(conn, actor.actor_id, lesson_id)

@learning_router.delete("/me/lessons/{lesson_id}/bookmark")
def remove_bookmark(lesson_id: str, actor: Actor = Depends(require_authenticated_user)):
    with get_db() as conn:
        return LearningProgressService.remove_bookmark(conn, actor.actor_id, lesson_id)

@learning_router.post("/feedback")
def submit_feedback(data: ContentFeedbackCreate, actor: Actor = Depends(require_authenticated_user)):
    with get_db() as conn:
        return TrainingService.submit_feedback(conn, actor.beneficiary_id, data)

# ============================================================================
# Admin Endpoints (Skipping auth for mock)
# ============================================================================

@admin_router.post("/courses")
def create_course(data: TrainingCourseCreate):
    with get_db() as conn:
        return TrainingService.create_course(conn, data)
