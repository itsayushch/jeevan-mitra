"""ivr_tables

Revision ID: a1b2c3d4e5f6
Revises: f3a4b5c6d7e8
Create Date: 2026-10-04 19:10:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'f3a4b5c6d7e8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. ivr_sessions
    op.create_table(
        'ivr_sessions',
        sa.Column('id', sa.String(length=64), nullable=False, primary_key=True),
        sa.Column('provider', sa.String(length=32), nullable=False, server_default='mock'),
        sa.Column('provider_call_id', sa.String(length=128), nullable=True),
        sa.Column('caller_reference_hash', sa.String(length=64), nullable=True),
        sa.Column('beneficiary_id', sa.String(length=64), sa.ForeignKey('beneficiaries.id', ondelete='SET NULL'), nullable=True),
        sa.Column('current_state', sa.String(length=32), nullable=False, server_default='welcome'),
        sa.Column('language', sa.String(length=16), nullable=False, server_default='hi-IN'),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='active'),
        sa.Column('invalid_attempt_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('current_context_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('started_at', sa.String(length=64), nullable=False),
        sa.Column('updated_at', sa.String(length=64), nullable=False),
        sa.Column('ended_at', sa.String(length=64), nullable=True),
        sa.Column('expires_at', sa.String(length=64), nullable=False)
    )
    op.create_index('ix_ivr_sessions_caller', 'ivr_sessions', ['caller_reference_hash'])
    op.create_index('ix_ivr_sessions_status', 'ivr_sessions', ['status'])
    op.create_index('ix_ivr_sessions_ben_id', 'ivr_sessions', ['beneficiary_id'])
    op.create_index('ix_ivr_sessions_provider_call', 'ivr_sessions', ['provider_call_id'])

    # 2. ivr_events
    op.create_table(
        'ivr_events',
        sa.Column('id', sa.String(length=64), nullable=False, primary_key=True),
        sa.Column('session_id', sa.String(length=64), sa.ForeignKey('ivr_sessions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('event_type', sa.String(length=64), nullable=False),
        sa.Column('state_before', sa.String(length=32), nullable=False),
        sa.Column('state_after', sa.String(length=32), nullable=False),
        sa.Column('digit', sa.String(length=8), nullable=True),
        sa.Column('prompt_key', sa.String(length=64), nullable=False),
        sa.Column('idempotency_key', sa.String(length=128), nullable=True),
        sa.Column('safe_payload_json', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.String(length=64), nullable=False)
    )
    op.create_index('ix_ivr_events_session_id', 'ivr_events', ['session_id'])
    op.create_index('ix_ivr_events_idemp', 'ivr_events', ['session_id', 'idempotency_key'])
    op.create_index('ix_ivr_events_created_at', 'ivr_events', ['created_at'])

    # 3. ivr_callback_requests
    op.create_table(
        'ivr_callback_requests',
        sa.Column('id', sa.String(length=64), nullable=False, primary_key=True),
        sa.Column('session_id', sa.String(length=64), sa.ForeignKey('ivr_sessions.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('beneficiary_id', sa.String(length=64), sa.ForeignKey('beneficiaries.id', ondelete='SET NULL'), nullable=True),
        sa.Column('callback_reason', sa.String(length=64), nullable=False, server_default='general_help'),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='requested'),
        sa.Column('assigned_worker_id', sa.String(length=64), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('case_id', sa.String(length=64), sa.ForeignKey('beneficiary_cases.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.String(length=64), nullable=False),
        sa.Column('updated_at', sa.String(length=64), nullable=False)
    )
    op.create_index('ix_ivr_callback_requests_session', 'ivr_callback_requests', ['session_id'], unique=True)
    op.create_index('ix_ivr_callback_requests_status', 'ivr_callback_requests', ['status'])
    op.create_index('ix_ivr_callback_requests_ben', 'ivr_callback_requests', ['beneficiary_id'])


def downgrade() -> None:
    op.drop_table('ivr_callback_requests')
    op.drop_table('ivr_events')
    op.drop_table('ivr_sessions')
