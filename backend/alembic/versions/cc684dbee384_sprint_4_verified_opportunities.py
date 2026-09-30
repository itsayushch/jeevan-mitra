"""sprint_4_verified_opportunities

Revision ID: cc684dbee384
Revises: 929f87ab56cc
Create Date: 2026-09-30 13:43:20.434918

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cc684dbee384'
down_revision: Union[str, Sequence[str], None] = '929f87ab56cc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Drop existing legacy tables that conflict
    op.drop_table('referral_cases')
    op.drop_table('recommendations')
    op.drop_table('evidence_sources')
    op.drop_table('local_opportunities')
    op.drop_table('qualifications')

    # 2. Create qualifications
    op.create_table(
        'qualifications',
        sa.Column('id', sa.String(), nullable=False, primary_key=True),
        sa.Column('external_reference', sa.String(), nullable=True, unique=True),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('sector', sa.String(), nullable=False),
        sa.Column('nsqf_level', sa.Integer(), nullable=True),
        sa.Column('duration_hours', sa.Integer(), nullable=True),
        sa.Column('entry_requirements_json', sa.Text(), nullable=True),
        sa.Column('skills_json', sa.Text(), nullable=True),
        sa.Column('source_name', sa.String(), nullable=False),
        sa.Column('source_url', sa.String(), nullable=True),
        sa.Column('source_version', sa.String(), nullable=True),
        sa.Column('source_verified_at', sa.DateTime(), nullable=False),
        sa.Column('verification_status', sa.String(), nullable=False), # DRAFT, VERIFIED, ARCHIVED, REJECTED
        sa.Column('created_by_user_id', sa.String(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('verified_by_user_id', sa.String(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('verified_at', sa.DateTime(), nullable=True),
        sa.Column('archived_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False)
    )

    # 3. Create training_course_qualifications
    op.create_table(
        'training_course_qualifications',
        sa.Column('training_course_id', sa.String(), sa.ForeignKey('training_courses.id'), nullable=False),
        sa.Column('qualification_id', sa.String(), sa.ForeignKey('qualifications.id'), nullable=False),
        sa.Column('relationship_type', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('training_course_id', 'qualification_id')
    )

    # 4. Create opportunity_providers
    op.create_table(
        'opportunity_providers',
        sa.Column('id', sa.String(), nullable=False, primary_key=True),
        sa.Column('provider_type', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('contact_name', sa.String(), nullable=True),
        sa.Column('contact_phone', sa.String(), nullable=True),
        sa.Column('contact_email', sa.String(), nullable=True),
        sa.Column('address_line', sa.Text(), nullable=True),
        sa.Column('district_id', sa.String(), nullable=True),
        sa.Column('block_id', sa.String(), nullable=True),
        sa.Column('pincode', sa.String(), nullable=True),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('source_name', sa.String(), nullable=True),
        sa.Column('source_reference', sa.String(), nullable=True),
        sa.Column('created_by_user_id', sa.String(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False)
    )

    # 5. Create local_opportunities
    op.create_table(
        'local_opportunities',
        sa.Column('id', sa.String(), nullable=False, primary_key=True),
        sa.Column('qualification_id', sa.String(), sa.ForeignKey('qualifications.id'), nullable=False),
        sa.Column('provider_id', sa.String(), sa.ForeignKey('opportunity_providers.id'), nullable=False),
        sa.Column('opportunity_type', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('district_id', sa.String(), nullable=False),
        sa.Column('block_id', sa.String(), nullable=True),
        sa.Column('location_text', sa.Text(), nullable=True),
        sa.Column('delivery_mode', sa.String(), nullable=False),
        sa.Column('start_date', sa.DateTime(), nullable=True),
        sa.Column('end_date', sa.DateTime(), nullable=True),
        sa.Column('application_deadline', sa.DateTime(), nullable=True),
        sa.Column('seats_total', sa.Integer(), nullable=True),
        sa.Column('seats_available', sa.Integer(), nullable=True),
        sa.Column('vacancies_total', sa.Integer(), nullable=True),
        sa.Column('vacancies_available', sa.Integer(), nullable=True),
        sa.Column('stipend_amount', sa.Float(), nullable=True),
        sa.Column('fee_amount', sa.Float(), nullable=True),
        sa.Column('travel_support_available', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column('hostel_available', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column('eligibility_notes', sa.Text(), nullable=True),
        sa.Column('accessibility_notes', sa.Text(), nullable=True),
        sa.Column('evidence_summary', sa.Text(), nullable=True),
        sa.Column('source_url', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('verified_by_user_id', sa.String(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('verified_at', sa.DateTime(), nullable=True),
        sa.Column('verification_expires_at', sa.DateTime(), nullable=True),
        sa.Column('created_by_user_id', sa.String(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('updated_by_user_id', sa.String(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('closed_at', sa.DateTime(), nullable=True),
        sa.Column('archived_at', sa.DateTime(), nullable=True)
    )

    # 6. Create opportunity_evidence
    op.create_table(
        'opportunity_evidence',
        sa.Column('id', sa.String(), nullable=False, primary_key=True),
        sa.Column('opportunity_id', sa.String(), sa.ForeignKey('local_opportunities.id'), nullable=False),
        sa.Column('evidence_type', sa.String(), nullable=False),
        sa.Column('storage_key', sa.String(), nullable=True),
        sa.Column('external_url', sa.String(), nullable=True),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('submitted_by_user_id', sa.String(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('reviewed_by_user_id', sa.String(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('is_approved', sa.Boolean(), nullable=False, server_default=sa.text('0'))
    )

    # 7. Create opportunity_verification_events
    op.create_table(
        'opportunity_verification_events',
        sa.Column('id', sa.String(), nullable=False, primary_key=True),
        sa.Column('opportunity_id', sa.String(), sa.ForeignKey('local_opportunities.id'), nullable=False),
        sa.Column('actor_user_id', sa.String(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('previous_status', sa.String(), nullable=False),
        sa.Column('new_status', sa.String(), nullable=False),
        sa.Column('verification_action', sa.String(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('verification_expires_at', sa.DateTime(), nullable=True),
        sa.Column('metadata_json', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False)
    )

    # 8. Create recommendation_match_state
    op.create_table(
        'recommendation_match_state',
        sa.Column('id', sa.String(), nullable=False, primary_key=True),
        sa.Column('beneficiary_id', sa.String(), nullable=False), # Assuming string beneficiary ID
        sa.Column('qualification_id', sa.String(), sa.ForeignKey('qualifications.id'), nullable=False),
        sa.Column('local_opportunity_id', sa.String(), sa.ForeignKey('local_opportunities.id'), nullable=True),
        sa.Column('match_state', sa.String(), nullable=False),
        sa.Column('calculation_version', sa.Integer(), nullable=False, server_default=sa.text('1')),
        sa.Column('eligibility_snapshot_json', sa.Text(), nullable=False),
        sa.Column('score_snapshot_json', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False)
    )

def downgrade() -> None:
    op.drop_table('recommendation_match_state')
    op.drop_table('opportunity_verification_events')
    op.drop_table('opportunity_evidence')
    op.drop_table('local_opportunities')
    op.drop_table('opportunity_providers')
    op.drop_table('training_course_qualifications')
    op.drop_table('qualifications')
