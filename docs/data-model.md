# JeevanMitra 2.0 Data Model & ERD Concepts

## Core Tables (Sprints 1–5)

### Identity & Consent
1. **users**: `id`, `auth_provider_id`, `role`, `status`, `preferred_language`
2. **roles**: `id`, `key`, `display_name`, `description`, `created_at`
3. **beneficiaries**: `id`, `user_id`, `district`, `state`, `profile_status`, `owner_type`, `owner_id`
4. **consent_records**: `id`, `beneficiary_id`, `session_id`, `consent_type`, `policy_version`, `user_language`, `capture_channel`, `status`, `created_at`

### AI Interview & Catalogue
5. **interview_sessions**: `id`, `session_id`, `beneficiary_id`, `status`, `started_at`, `language`
6. **interview_turns**: `id`, `session_id`, `raw_transcript`, `normalized_answer`, `confidence`
7. **qualifications**: `id`, `nqr_code`, `title`, `sector`, `nsqf_level`, `official_source_url`, `last_verified_at`
8. **opportunity_providers**: `id`, `name`, `district`, `state`, `contact_person`, `phone`, `email`, `address_line`
9. **local_opportunities**: `id`, `qualification_id`, `provider_id`, `title`, `district`, `state`, `total_capacity`, `enrolled_count`, `stipend_amount_inr`, `status`, `expiry_date`, `verified_by_user_id`, `verified_at`
10. **recommendations**: `id`, `interview_id`, `beneficiary_id`, `qualification_id`, `match_state` (`INTEREST_MATCH`, `VERIFIED_MATCH`), `score`, `explanation_text`, `ranking_factors`, `caveat`

### Case Management & Referrals (Sprint 5)
11. **cases**:
    - `id` (PK)
    - `beneficiary_id` (FK -> beneficiaries.id)
    - `assigned_worker_id` (FK -> users.id)
    - `status` (`OPEN`, `IN_PROGRESS`, `REFERRED`, `CLOSED`)
    - `priority` (`LOW`, `MEDIUM`, `HIGH`, `URGENT`)
    - `district` (Geographic scope anchor)
    - `state`
    - `target_sector`
    - `notes_count`
    - `follow_up_due_at`
    - `created_at`, `updated_at`

12. **case_notes**:
    - `id` (PK)
    - `case_id` (FK -> cases.id)
    - `author_user_id` (FK -> users.id)
    - `author_name`
    - `author_role`
    - `note_type` (`INITIAL_INTAKE`, `FIELD_VISIT`, `COUNSELLING`, `FOLLOW_UP`, `FIELD_UPDATE`)
    - `content`
    - `is_staff_only` (BOOLEAN: if 1, strictly hidden from beneficiary queries)
    - `created_at`

13. **case_assignments**:
    - `id` (PK)
    - `case_id` (FK -> cases.id)
    - `from_worker_id` (FK -> users.id, nullable)
    - `to_worker_id` (FK -> users.id)
    - `assigned_by_id` (FK -> users.id)
    - `reason`
    - `assigned_at`

14. **referrals**:
    - `id` (PK)
    - `case_id` (FK -> cases.id)
    - `recommendation_id` (FK -> recommendations.id)
    - `opportunity_id` (FK -> local_opportunities.id)
    - `beneficiary_id` (FK -> beneficiaries.id)
    - `field_worker_id` (FK -> users.id)
    - `district`
    - `status` (`READY_TO_SEND`, `REFERRED`, `CONTACTED`, `ENROLLED`, `TRAINING_STARTED`, `COMPLETED`, `DROPPED_OUT`, `REJECTED`, `BENEFICIARY_DECLINED`, `CLOSED`)
    - `notes`
    - `eligibility_snapshot` (JSON snapshot of match state & opportunity at creation)
    - `created_at`, `updated_at`

15. **referral_status_history**:
    - `id` (PK)
    - `referral_id` (FK -> referrals.id)
    - `from_status`
    - `to_status`
    - `changed_by_user_id` (FK -> users.id)
    - `reason`
    - `changed_at`

16. **referral_contact_attempts**:
    - `id` (PK)
    - `referral_id` (FK -> referrals.id)
    - `worker_user_id` (FK -> users.id)
    - `channel` (`PHONE`, `IN_PERSON`, `SMS`, `WHATSAPP`)
    - `successful` (BOOLEAN)
    - `notes`
    - `attempted_at`

17. **referral_outcomes**:
    - `id` (PK)
    - `referral_id` (FK -> referrals.id)
    - `reported_by_user_id` (FK -> users.id)
    - `outcome_type` (`ENROLLED`, `COMPLETED`, `JOB_OFFER`, `SELF_EMPLOYMENT_STARTED`, `DROPPED_OUT`)
    - `status` (`REPORTED`, `VERIFIED`, `REJECTED`)
    - `evidence_summary`
    - `reported_at`, `verified_at`, `verified_by_user_id`

### Audit & Security
18. **audit_events**: `id`, `actor_user_id`, `actor_role`, `action`, `resource_type`, `resource_id`, `before_state`, `after_state`, `ip_address`, `timestamp`

---

## Critical Invariants Enforced

1. **Verified Match Invariant**:
   - A referral requires `recommendation.match_state == 'VERIFIED_MATCH'`.
   - The associated `local_opportunity` must have `status == 'ACTIVE'`, unexpired date (`expiry_date > NOW()`), and open capacity (`enrolled_count < total_capacity`).
2. **Geographic Scoping Invariant**:
   - Field workers can only access, modify, or create cases/referrals in their assigned district.
   - Cross-district actions trigger `SECURITY_ACCESS_DENIED` written via an isolated audit transaction before returning HTTP 403 Forbidden.
3. **Data Isolation Invariant**:
   - Beneficiary-facing APIs (`/me/cases`, `/me/referrals`) strictly filter by authenticated user ID.
   - Staff casework notes (`is_staff_only = 1`), internal eligibility snapshots, and provider private phone numbers are never returned in beneficiary read models.
