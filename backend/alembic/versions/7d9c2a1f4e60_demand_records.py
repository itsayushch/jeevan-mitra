"""add anonymised demand records

Revision ID: 7d9c2a1f4e60
Revises: f3a4b5c6d7e8
Create Date: 2026-10-04 10:00:00.000000
"""
from typing import Sequence, Union

from alembic import op


revision: str = "7d9c2a1f4e60"
down_revision: Union[str, Sequence[str], None] = "f3a4b5c6d7e8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE audit_events ADD COLUMN timestamp VARCHAR(64);")
    op.execute("UPDATE audit_events SET timestamp = created_at WHERE timestamp IS NULL;")
    op.execute(
        "ALTER TABLE local_opportunities "
        "ADD COLUMN is_archived INTEGER NOT NULL DEFAULT 0;"
    )
    op.execute("""
        CREATE TABLE IF NOT EXISTS demand_records (
            id VARCHAR(64) PRIMARY KEY,
            qualification_id VARCHAR(64) NOT NULL,
            district VARCHAR(128) NOT NULL,
            block VARCHAR(128) NOT NULL,
            mobility_radius_km REAL,
            work_preference VARCHAR(64),
            had_verified_match INTEGER NOT NULL DEFAULT 0,
            period VARCHAR(32) NOT NULL,
            created_at VARCHAR(64) NOT NULL,
            FOREIGN KEY (qualification_id) REFERENCES qualifications(id) ON DELETE CASCADE
        );
    """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_demand_records_district "
        "ON demand_records(district, period);"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_demand_records_block "
        "ON demand_records(district, block, qualification_id);"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_demand_records_qual "
        "ON demand_records(qualification_id);"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS demand_records;")
