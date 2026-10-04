"""ivr_callback_disposition

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-10-04 19:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    cols = [c["name"] for c in inspector.get_columns("ivr_callback_requests")]

    if "notes" not in cols:
        op.add_column("ivr_callback_requests", sa.Column("notes", sa.Text(), nullable=True))

    if "contacted_at" not in cols:
        op.add_column("ivr_callback_requests", sa.Column("contacted_at", sa.String(length=64), nullable=True))


def downgrade() -> None:
    # SQLite does not support drop column directly in older versions without batch_alter_table
    with op.batch_alter_table("ivr_callback_requests") as batch_op:
        batch_op.drop_column("contacted_at")
        batch_op.drop_column("notes")
