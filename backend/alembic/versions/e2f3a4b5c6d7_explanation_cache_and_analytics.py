"""explanation_cache_and_analytics

Revision ID: e2f3a4b5c6d7
Revises: d1e2f3a4b5c6
Create Date: 2026-09-30 17:35:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'e2f3a4b5c6d7'
down_revision: Union[str, Sequence[str], None] = 'd1e2f3a4b5c6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. Disposable explanation cache table
    op.execute('''
    CREATE TABLE IF NOT EXISTS recommendation_explanation_cache (
        id TEXT PRIMARY KEY,
        recommendation_id TEXT NOT NULL,
        locale TEXT NOT NULL,
        renderer TEXT NOT NULL CHECK(renderer IN ('template', 'llm', 'llm_grounded')),
        model_version TEXT,
        rendered_text TEXT NOT NULL,
        explanation_facts_json TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY (recommendation_id) REFERENCES recommendations(id) ON DELETE CASCADE
    );
    ''')
    op.execute('CREATE INDEX IF NOT EXISTS idx_rec_expl_cache_rec ON recommendation_explanation_cache(recommendation_id, locale);')

    # 2. Non-sensitive operational analytics telemetry table
    op.execute('''
    CREATE TABLE IF NOT EXISTS analytics_events (
        id TEXT PRIMARY KEY,
        event_name TEXT NOT NULL,
        actor_type TEXT NOT NULL,
        district_id TEXT,
        locale TEXT,
        metadata_json TEXT,
        created_at TEXT NOT NULL
    );
    ''')
    op.execute('CREATE INDEX IF NOT EXISTS idx_analytics_event_name ON analytics_events(event_name);')
    op.execute('CREATE INDEX IF NOT EXISTS idx_analytics_district ON analytics_events(district_id);')
    op.execute('CREATE INDEX IF NOT EXISTS idx_analytics_created ON analytics_events(created_at);')

def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS analytics_events;")
    op.execute("DROP TABLE IF EXISTS recommendation_explanation_cache;")
