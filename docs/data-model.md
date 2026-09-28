# JeevanMitra 2.0 Data Model & ERD Concepts

## Core Tables
1. **users**: `id`, `auth_provider_id`, `role`, `status`
2. **roles**: `id`, `name` (beneficiary, field_worker, district_admin, etc.)
3. **beneficiaries**: `id`, `user_id`, `district_id`, `profile_status` (Sensitive fields kept separate)
4. **consents**: `id`, `beneficiary_id`, `decision`, `timestamp`
5. **interview_sessions**: `id`, `beneficiary_id`, `status`, `started_at`
6. **interview_turns**: `id`, `session_id`, `raw_transcript`, `normalized_answer`, `confidence`
7. **profile_answers**: `id`, `beneficiary_id`, `field_key`, `value_json`, `confidence`
8. **qualifications**: `id`, `nqr_id`, `title`, `sector`, `nsqf_level`, `verified_at`
9. **local_opportunities**: `id`, `qualification_id`, `provider_name`, `district_id`, `seats`, `expiry_date`, `verified_by`, `verified_at`
10. **recommendations**: `id`, `beneficiary_id`, `qualification_id`, `match_state` (Enum: INTEREST_MATCH, VERIFIED_MATCH, etc.)
11. **verification_events**: `id`, `opportunity_id`, `actor_id`, `timestamp`
12. **referrals**: `id`, `beneficiary_id`, `opportunity_id`, `assigned_worker_id`, `status`
13. **referral_status_history**: `id`, `referral_id`, `old_status`, `new_status`
14. **outcomes**: `id`, `referral_id`, `enrolment_status`, `employment_type`
15. **planning_snapshots**: `id`, `district_id`, `aggregation_json`
16. **audit_events**: `id`, `actor_id`, `action`, `entity_type`, `before_json`, `after_json`
17. **notifications**: `id`, `recipient`, `status`
18. **data_retention_jobs**: `id`, `entity_type`, `scheduled_for`, `action`

## Critical Constraints
- `recommendations.match_state` is controlled by a strict backend state machine.
- A `referral` requires `recommendation.match_state == VERIFIED_MATCH` and an unexpired `local_opportunity`.
