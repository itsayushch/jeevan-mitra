"""auth_sprint_3_learning_progress

Revision ID: 929f87ab56cc
Revises: 2d449511aa26
Create Date: 2026-09-30 13:29:06.238954

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '929f87ab56cc'
down_revision: Union[str, Sequence[str], None] = '2d449511aa26'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop legacy tables to replace with new normalized schema
    op.execute("DROP TABLE IF EXISTS learner_lesson_progress;")
    op.execute("DROP TABLE IF EXISTS learner_course_progress;")
    
    op.execute('''
    CREATE TABLE user_lesson_progress (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        lesson_id TEXT NOT NULL,
        course_id TEXT NOT NULL,
        status TEXT NOT NULL,
        started_at TEXT,
        completed_at TEXT,
        last_accessed_at TEXT NOT NULL,
        completion_source TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY(lesson_id) REFERENCES training_lessons(id) ON DELETE CASCADE,
        FOREIGN KEY(course_id) REFERENCES training_courses(id) ON DELETE CASCADE,
        UNIQUE(user_id, lesson_id),
        CHECK(status IN ('NOT_STARTED', 'IN_PROGRESS', 'COMPLETED')),
        CHECK((status = 'COMPLETED' AND completed_at IS NOT NULL) OR (status != 'COMPLETED' AND completed_at IS NULL))
    );
    ''')
    
    op.execute('''
    CREATE TABLE user_lesson_bookmarks (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        lesson_id TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY(lesson_id) REFERENCES training_lessons(id) ON DELETE CASCADE,
        UNIQUE(user_id, lesson_id)
    );
    ''')
    
    op.execute('''
    CREATE TABLE user_course_learning_state (
        user_id TEXT NOT NULL,
        course_id TEXT NOT NULL,
        first_started_at TEXT,
        last_accessed_at TEXT,
        last_lesson_id TEXT,
        completed_at TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        PRIMARY KEY(user_id, course_id),
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY(course_id) REFERENCES training_courses(id) ON DELETE CASCADE,
        FOREIGN KEY(last_lesson_id) REFERENCES training_lessons(id) ON DELETE SET NULL
    );
    ''')
    
    # Indexes
    op.execute("CREATE INDEX idx_user_lesson_prog_user ON user_lesson_progress(user_id);")
    op.execute("CREATE INDEX idx_user_lesson_prog_course ON user_lesson_progress(course_id);")
    op.execute("CREATE INDEX idx_user_course_state_user ON user_course_learning_state(user_id);")

def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS user_course_learning_state;")
    op.execute("DROP TABLE IF EXISTS user_lesson_bookmarks;")
    op.execute("DROP TABLE IF EXISTS user_lesson_progress;")
