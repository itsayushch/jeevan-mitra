from pydantic import BaseModel, Field
from typing import List, Optional, Any
from datetime import datetime

class TrainingCourseBase(BaseModel):
    title: str
    slug: str
    short_description: str
    long_description: str
    sector: str
    nsqf_level: Optional[str] = None
    duration_hours: Optional[int] = None
    difficulty: str = "Beginner"
    language_code: str = "hi"
    thumbnail_url: Optional[str] = None
    source_name: str
    source_url: Optional[str] = None
    verification_status: str = "Draft"
    is_published: bool = False

class TrainingCourseCreate(TrainingCourseBase):
    pass

class TrainingCourseUpdate(BaseModel):
    title: Optional[str] = None
    short_description: Optional[str] = None
    long_description: Optional[str] = None
    sector: Optional[str] = None
    nsqf_level: Optional[str] = None
    duration_hours: Optional[int] = None
    difficulty: Optional[str] = None
    language_code: Optional[str] = None
    thumbnail_url: Optional[str] = None
    source_name: Optional[str] = None
    source_url: Optional[str] = None
    verification_status: Optional[str] = None
    is_published: Optional[bool] = None

class TrainingCourseResponse(TrainingCourseBase):
    id: str
    verified_at: Optional[str] = None
    last_updated_at: str

class TrainingModuleBase(BaseModel):
    course_id: str
    title: str
    sequence_number: int
    estimated_minutes: int
    learning_objectives: Any # JSON
    summary: str
    is_published: bool = False

class TrainingModuleCreate(BaseModel):
    title: str
    sequence_number: int
    estimated_minutes: int
    learning_objectives: Any
    summary: str
    is_published: bool = False

class TrainingModuleUpdate(BaseModel):
    title: Optional[str] = None
    sequence_number: Optional[int] = None
    estimated_minutes: Optional[int] = None
    learning_objectives: Optional[Any] = None
    summary: Optional[str] = None
    is_published: Optional[bool] = None

class TrainingModuleResponse(TrainingModuleBase):
    id: str

class TrainingLessonBase(BaseModel):
    module_id: str
    title: str
    sequence_number: int
    content_markdown: str
    plain_language_summary: str
    key_points: Any # JSON
    practical_steps: Any # JSON
    safety_notes: Any # JSON
    quiz_questions: Optional[Any] = None # JSON
    source_references: Any # JSON

class TrainingLessonCreate(BaseModel):
    title: str
    sequence_number: int
    content_markdown: str
    plain_language_summary: str
    key_points: Any
    practical_steps: Any
    safety_notes: Any
    quiz_questions: Optional[Any] = None
    source_references: Any

class TrainingLessonUpdate(BaseModel):
    title: Optional[str] = None
    sequence_number: Optional[int] = None
    content_markdown: Optional[str] = None
    plain_language_summary: Optional[str] = None
    key_points: Optional[Any] = None
    practical_steps: Optional[Any] = None
    safety_notes: Optional[Any] = None
    quiz_questions: Optional[Any] = None
    source_references: Optional[Any] = None

class TrainingLessonResponse(TrainingLessonBase):
    id: str
    last_reviewed_at: str
    reviewed_by: Optional[str] = None

class TrainingResourceBase(BaseModel):
    course_id: str
    lesson_id: Optional[str] = None
    resource_type: str
    title: str
    file_url: str
    language_code: str = "hi"
    is_verified: bool = False

class TrainingResourceCreate(TrainingResourceBase):
    pass

class TrainingResourceResponse(TrainingResourceBase):
    id: str
    uploaded_at: str

class CourseOverviewItem(BaseModel):
    courseId: str
    title: str
    thumbnailUrl: Optional[str] = None
    completedLessons: int
    totalLessons: int
    completionPercent: int
    lastAccessedAt: Optional[str] = None
    resumeLessonId: Optional[str] = None
    resumeLessonTitle: Optional[str] = None
    courseStatus: str

class LearningOverviewResponse(BaseModel):
    inProgressCourses: int
    completedCourses: int
    bookmarkedLessons: int
    recentCourses: List[CourseOverviewItem]

class UserLessonProgressResponse(BaseModel):
    id: str
    lesson_id: str
    course_id: str
    status: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    last_accessed_at: str

class CourseProgressDetailResponse(BaseModel):
    courseId: str
    title: str
    completedLessons: int
    totalLessons: int
    completionPercent: int
    courseStatus: str
    lastAccessedAt: Optional[str] = None
    resumeLessonId: Optional[str] = None
    lessons_progress: List[UserLessonProgressResponse]
    bookmarked_lesson_ids: List[str]

class ContentFeedbackCreate(BaseModel):
    course_id: str
    lesson_id: Optional[str] = None
    rating: int = Field(ge=1, le=5)
    feedback_type: str
    comment: Optional[str] = None
