"""locale_and_opportunity_submissions

Revision ID: d1e2f3a4b5c6
Revises: 8a14eb65296c
Create Date: 2026-09-30 17:05:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd1e2f3a4b5c6'
down_revision: Union[str, Sequence[str], None] = '8a14eb65296c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add preferred_language to users table if not exists
    conn = op.get_bind()
    cols = [r[1] for r in conn.execute(sa.text("PRAGMA table_info(users);")).fetchall()]
    if "preferred_language" not in cols:
        op.execute("ALTER TABLE users ADD COLUMN preferred_language TEXT NOT NULL DEFAULT 'en';")

    # 2. Add explanation_facts column to recommendations table if missing
    rec_cols = [r[1] for r in conn.execute(sa.text("PRAGMA table_info(recommendations);")).fetchall()]
    if "explanation_facts" not in rec_cols:
        op.execute("ALTER TABLE recommendations ADD COLUMN explanation_facts TEXT;")

    # 3. Create opportunity_submissions table for text and voice submissions
    op.execute('''
CREATE TABLE IF NOT EXISTS opportunity_submissions (
    id TEXT PRIMARY KEY,
    submitted_by_user_id TEXT,
    input_mode TEXT CHECK(input_mode IN ('text', 'voice')) NOT NULL,
    raw_text TEXT NOT NULL,
    normalized_text TEXT NOT NULL,
    locale TEXT NOT NULL,
    audio_storage_key TEXT,
    transcript_confidence REAL,
    status TEXT NOT NULL DEFAULT 'SUBMITTED',
    linked_opportunity_id TEXT,
    reviewed_by_user_id TEXT,
    review_notes TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (submitted_by_user_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (linked_opportunity_id) REFERENCES local_opportunities(id) ON DELETE SET NULL,
    FOREIGN KEY (reviewed_by_user_id) REFERENCES users(id) ON DELETE SET NULL
);
''')
    op.execute('CREATE INDEX IF NOT EXISTS idx_opp_sub_user ON opportunity_submissions(submitted_by_user_id);')
    op.execute('CREATE INDEX IF NOT EXISTS idx_opp_sub_status ON opportunity_submissions(status);')


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS opportunity_submissions;")
