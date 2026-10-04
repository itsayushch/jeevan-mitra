"""sprint_5_cases_and_referrals

Revision ID: 8a14eb65296c
Revises: cc684dbee384
Create Date: 2026-09-30 16:53:59.732040

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8a14eb65296c'
down_revision: Union[str, Sequence[str], None] = 'cc684dbee384'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Safely drop only Sprint 5 specific tables if previously created
    op.execute("DROP TABLE IF EXISTS referral_outcomes;")
    op.execute("DROP TABLE IF EXISTS referral_documents;")
    op.execute("DROP TABLE IF EXISTS referral_contact_attempts;")
    op.execute("DROP TABLE IF EXISTS referral_status_history;")
    op.execute("DROP TABLE IF EXISTS case_notes;")
    op.execute("DROP TABLE IF EXISTS case_assignments;")
    op.execute("DROP TABLE IF EXISTS beneficiary_cases;")

    # 1. beneficiary_cases
    op.create_table(
        'beneficiary_cases',
        sa.Column('id', sa.String(), nullable=False, primary_key=True),
        sa.Column('beneficiary_id', sa.String(), nullable=False),
        sa.Column('district_id', sa.String(), nullable=False),
        sa.Column('block_id', sa.String(), nullable=True),
        sa.Column('assigned_worker_id', sa.String(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('case_status', sa.String(), nullable=False, server_default='NEW'),
        sa.Column('priority', sa.String(), nullable=False, server_default='NORMAL'),
        sa.Column('intake_source', sa.String(), nullable=False, server_default='WEB'),
        sa.Column('latest_recommendation_id', sa.String(), nullable=True),
        sa.Column('latest_referral_id', sa.String(), nullable=True),
        sa.Column('next_follow_up_at', sa.DateTime(), nullable=True),
        sa.Column('last_contacted_at', sa.DateTime(), nullable=True),
        sa.Column('closed_at', sa.DateTime(), nullable=True),
        sa.Column('closed_reason', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False)
    )
    op.create_index('ix_beneficiary_cases_ben_id', 'beneficiary_cases', ['beneficiary_id'])
    op.create_index('ix_beneficiary_cases_scope', 'beneficiary_cases', ['district_id', 'block_id'])
    op.create_index('ix_beneficiary_cases_worker', 'beneficiary_cases', ['assigned_worker_id'])

    # 2. case_assignments
    op.create_table(
        'case_assignments',
        sa.Column('id', sa.String(), nullable=False, primary_key=True),
        sa.Column('case_id', sa.String(), sa.ForeignKey('beneficiary_cases.id'), nullable=False),
        sa.Column('worker_id', sa.String(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('assigned_by_user_id', sa.String(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('assignment_reason', sa.Text(), nullable=True),
        sa.Column('assigned_at', sa.DateTime(), nullable=False),
        sa.Column('unassigned_at', sa.DateTime(), nullable=True)
    )
    op.create_index('ix_case_assignments_case_id', 'case_assignments', ['case_id'])

    # 3. case_notes
    op.create_table(
        'case_notes',
        sa.Column('id', sa.String(), nullable=False, primary_key=True),
        sa.Column('case_id', sa.String(), sa.ForeignKey('beneficiary_cases.id'), nullable=False),
        sa.Column('author_user_id', sa.String(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('note_text', sa.Text(), nullable=False),
        sa.Column('note_type', sa.String(), nullable=False, server_default='GENERAL'),
        sa.Column('visibility', sa.String(), nullable=False, server_default='STAFF_ONLY'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True)
    )
    op.create_index('ix_case_notes_case_id', 'case_notes', ['case_id'])

    # 4. Drop and recreate referrals with BOTH canonical Sprint 5 and legacy compatibility columns
    op.execute("DROP TABLE IF EXISTS referrals;")
    op.create_table(
        'referrals',
        sa.Column('id', sa.String(), nullable=False, primary_key=True),
        sa.Column('case_id', sa.String(), sa.ForeignKey('beneficiary_cases.id'), nullable=True),
        sa.Column('beneficiary_id', sa.String(), nullable=False),
        sa.Column('recommendation_id', sa.String(), nullable=False),
        sa.Column('qualification_id', sa.String(), sa.ForeignKey('qualifications.id'), nullable=True),
        sa.Column('local_opportunity_id', sa.String(), sa.ForeignKey('local_opportunities.id'), nullable=False),
        sa.Column('provider_id', sa.String(), sa.ForeignKey('opportunity_providers.id'), nullable=True),
        sa.Column('created_by_worker_id', sa.String(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('assigned_worker_id', sa.String(), nullable=True),
        sa.Column('referral_status', sa.String(), nullable=False, server_default='DRAFT'),
        # Legacy status alias
        sa.Column('status', sa.String(), nullable=True, server_default='pending'),
        sa.Column('referral_reason', sa.Text(), nullable=True),
        sa.Column('beneficiary_consent_confirmed_at', sa.DateTime(), nullable=True),
        sa.Column('eligibility_snapshot_json', sa.Text(), nullable=True),
        sa.Column('referred_at', sa.DateTime(), nullable=True),
        sa.Column('next_follow_up_at', sa.DateTime(), nullable=True),
        sa.Column('last_contact_attempt_at', sa.DateTime(), nullable=True),
        sa.Column('closed_at', sa.DateTime(), nullable=True),
        sa.Column('closure_reason', sa.String(), nullable=True),
        # Legacy compatibility columns
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('caste_document_verified', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('income_criteria_verified', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('residence_proof_verified', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('sms_sent', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('whatsapp_sent', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('next_follow_up', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False)
    )
    op.create_index('ix_referrals_case_id', 'referrals', ['case_id'])
    op.create_index('ix_referrals_beneficiary_id', 'referrals', ['beneficiary_id'])
    op.create_index('ix_referrals_opportunity_id', 'referrals', ['local_opportunity_id'])
    op.create_index('ix_referrals_status', 'referrals', ['referral_status'])

    # 5. referral_status_history
    op.create_table(
        'referral_status_history',
        sa.Column('id', sa.String(), nullable=False, primary_key=True),
        sa.Column('referral_id', sa.String(), sa.ForeignKey('referrals.id'), nullable=False),
        sa.Column('previous_status', sa.String(), nullable=True),
        sa.Column('new_status', sa.String(), nullable=False),
        sa.Column('actor_user_id', sa.String(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('reason', sa.String(), nullable=True),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('metadata_json', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False)
    )
    op.create_index('ix_ref_status_hist_ref_id', 'referral_status_history', ['referral_id'])

    # 6. referral_contact_attempts
    op.create_table(
        'referral_contact_attempts',
        sa.Column('id', sa.String(), nullable=False, primary_key=True),
        sa.Column('referral_id', sa.String(), sa.ForeignKey('referrals.id'), nullable=False),
        sa.Column('actor_user_id', sa.String(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('channel', sa.String(), nullable=False),
        sa.Column('attempt_outcome', sa.String(), nullable=False),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('attempted_at', sa.DateTime(), nullable=False),
        sa.Column('next_follow_up_at', sa.DateTime(), nullable=True)
    )
    op.create_index('ix_ref_contact_attempts_ref_id', 'referral_contact_attempts', ['referral_id'])

    # 7. referral_documents
    op.create_table(
        'referral_documents',
        sa.Column('id', sa.String(), nullable=False, primary_key=True),
        sa.Column('referral_id', sa.String(), sa.ForeignKey('referrals.id'), nullable=False),
        sa.Column('document_type', sa.String(), nullable=False),
        sa.Column('storage_key', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, server_default='REQUESTED'),
        sa.Column('uploaded_by_user_id', sa.String(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('reviewed_by_user_id', sa.String(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True)
    )
    op.create_index('ix_ref_docs_ref_id', 'referral_documents', ['referral_id'])

    # 8. referral_outcomes
    op.create_table(
        'referral_outcomes',
        sa.Column('id', sa.String(), nullable=False, primary_key=True),
        sa.Column('referral_id', sa.String(), sa.ForeignKey('referrals.id'), nullable=False),
        sa.Column('outcome_type', sa.String(), nullable=False),
        sa.Column('outcome_status', sa.String(), nullable=False, server_default='REPORTED'),
        sa.Column('occurred_at', sa.DateTime(), nullable=True),
        sa.Column('recorded_by_user_id', sa.String(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('verified_by_user_id', sa.String(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('evidence_summary', sa.Text(), nullable=True),
        sa.Column('follow_up_due_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False)
    )
    op.create_index('ix_ref_outcomes_ref_id', 'referral_outcomes', ['referral_id'])


def downgrade() -> None:
    op.drop_table('referral_outcomes')
    op.drop_table('referral_documents')
    op.drop_table('referral_contact_attempts')
    op.drop_table('referral_status_history')
    op.drop_table('referrals')
    op.drop_table('case_notes')
    op.drop_table('case_assignments')
    op.drop_table('beneficiary_cases')
