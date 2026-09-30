"""sprint_6_planning_and_exports

Revision ID: f3a4b5c6d7e8
Revises: e2f3a4b5c6d7
Create Date: 2026-09-30 17:40:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f3a4b5c6d7e8'
down_revision: Union[str, Sequence[str], None] = 'e2f3a4b5c6d7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. planning_snapshots table
    op.execute("""
        CREATE TABLE IF NOT EXISTS planning_snapshots (
            id VARCHAR(64) PRIMARY KEY,
            district_id VARCHAR(64) NOT NULL,
            block_id VARCHAR(64),
            period_start VARCHAR(32) NOT NULL,
            period_end VARCHAR(32) NOT NULL,
            generated_by_user_id VARCHAR(64),
            generated_at VARCHAR(64) NOT NULL,
            metric_version VARCHAR(32) NOT NULL DEFAULT 'v1',
            filter_snapshot_json TEXT NOT NULL DEFAULT '{}',
            aggregation_snapshot_json TEXT NOT NULL DEFAULT '{}',
            data_freshness_at VARCHAR(64) NOT NULL,
            status VARCHAR(32) NOT NULL DEFAULT 'GENERATED',
            reviewed_by_user_id VARCHAR(64),
            reviewed_at VARCHAR(64),
            approved_by_user_id VARCHAR(64),
            approved_at VARCHAR(64),
            notes TEXT,
            FOREIGN KEY (generated_by_user_id) REFERENCES users(id) ON DELETE SET NULL,
            FOREIGN KEY (reviewed_by_user_id) REFERENCES users(id) ON DELETE SET NULL,
            FOREIGN KEY (approved_by_user_id) REFERENCES users(id) ON DELETE SET NULL
        );
    """)

    # 2. planning_snapshot_metrics table
    op.execute("""
        CREATE TABLE IF NOT EXISTS planning_snapshot_metrics (
            id VARCHAR(64) PRIMARY KEY,
            snapshot_id VARCHAR(64) NOT NULL,
            metric_group VARCHAR(64) NOT NULL,
            metric_key VARCHAR(128) NOT NULL,
            dimension_json TEXT NOT NULL DEFAULT '{}',
            metric_value REAL NOT NULL DEFAULT 0.0,
            numerator REAL,
            denominator REAL,
            is_suppressed INTEGER NOT NULL DEFAULT 0,
            created_at VARCHAR(64) NOT NULL,
            FOREIGN KEY (snapshot_id) REFERENCES planning_snapshots(id) ON DELETE CASCADE
        );
    """)

    # 3. planning_exports table
    op.execute("""
        CREATE TABLE IF NOT EXISTS planning_exports (
            id VARCHAR(64) PRIMARY KEY,
            snapshot_id VARCHAR(64) NOT NULL,
            export_type VARCHAR(16) NOT NULL,
            export_scope VARCHAR(64) NOT NULL DEFAULT 'FULL_REPORT',
            requested_by_user_id VARCHAR(64) NOT NULL,
            generated_at VARCHAR(64),
            expires_at VARCHAR(64),
            status VARCHAR(32) NOT NULL DEFAULT 'GENERATED',
            storage_key VARCHAR(255),
            file_content TEXT,
            checksum VARCHAR(64),
            download_count INTEGER NOT NULL DEFAULT 0,
            last_downloaded_at VARCHAR(64),
            created_at VARCHAR(64) NOT NULL,
            FOREIGN KEY (snapshot_id) REFERENCES planning_snapshots(id) ON DELETE CASCADE,
            FOREIGN KEY (requested_by_user_id) REFERENCES users(id) ON DELETE CASCADE
        );
    """)

    # 4. Indexes for planning performance
    try:
        op.execute("CREATE INDEX IF NOT EXISTS idx_planning_snapshots_district ON planning_snapshots(district_id);")
        op.execute("CREATE INDEX IF NOT EXISTS idx_planning_snapshots_period ON planning_snapshots(period_start, period_end);")
        op.execute("CREATE INDEX IF NOT EXISTS idx_planning_snapshot_metrics_snap ON planning_snapshot_metrics(snapshot_id);")
        op.execute("CREATE INDEX IF NOT EXISTS idx_planning_exports_snap ON planning_exports(snapshot_id);")
    except Exception:
        pass


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS planning_exports;")
    op.execute("DROP TABLE IF EXISTS planning_snapshot_metrics;")
    op.execute("DROP TABLE IF EXISTS planning_snapshots;")
