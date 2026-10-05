"""Support official fractional NSQF levels without truncating them."""
from alembic import op
import sqlalchemy as sa

revision = "4c8e21a7d902"
down_revision = "7d9c2a1f4e60"
branch_labels = None
depends_on = None


def upgrade():
    # SQLite already stores REAL in this column; avoid rebuilding tables with live FKs.
    if op.get_bind().dialect.name != "sqlite":
        op.alter_column("qualifications", "nsqf_level", existing_type=sa.Integer(), type_=sa.Float())


def downgrade():
    if op.get_bind().dialect.name != "sqlite":
        op.alter_column("qualifications", "nsqf_level", existing_type=sa.Float(), type_=sa.Integer())
