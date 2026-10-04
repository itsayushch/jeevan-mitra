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

### Planning, Aggregations & Controlled Exports (Sprint 6)
19. **planning_snapshots**:
    - `id` (PK, VARCHAR)
    - `district_id` (VARCHAR, Indexed)
    - `block_id` (VARCHAR, Nullable)
    - `period_start` (VARCHAR)
    - `period_end` (VARCHAR)
    - `generated_by_user_id` (FK -> users.id)
    - `generated_at` (DATETIME)
    - `status` (`GENERATED`, `REVIEWED`, `APPROVED`, `ARCHIVED`)
    - `metric_version` (VARCHAR, default `v1`)
    - `aggregation_snapshot_json` (TEXT: Full JSON payload of frozen aggregations)
    - `reviewed_by_user_id` (FK -> users.id, Nullable)
    - `reviewed_at` (DATETIME, Nullable)
    - `approved_by_user_id` (FK -> users.id, Nullable)
    - `approved_at` (DATETIME, Nullable)
    - `notes` (TEXT)
    - `created_at`, `updated_at`

20. **planning_snapshot_metrics**:
    - `id` (PK, VARCHAR)
    - `snapshot_id` (FK -> planning_snapshots.id ON DELETE CASCADE)
    - `metric_group` (`DEMAND`, `SUPPLY`, `GAP`, `REFERRAL_FUNNEL`, `OUTCOME`, `DATA_QUALITY`)
    - `metric_key` (VARCHAR)
    - `dimension_json` (TEXT)
    - `metric_value` (FLOAT)
    - `is_suppressed` (BOOLEAN, default 0)
    - `created_at` (DATETIME)

21. **planning_exports**:
    - `id` (PK, VARCHAR)
    - `snapshot_id` (FK -> planning_snapshots.id ON DELETE RESTRICT)
    - `export_type` (`CSV`, `PDF`)
    - `export_scope` (`FULL_REPORT`, `EXECUTIVE_BRIEF`, `GAP_MATRIX_ONLY`, `FUNNEL_ONLY`)
    - `requested_by_user_id` (FK -> users.id)
    - `generated_at` (DATETIME)
    - `expires_at` (DATETIME)
    - `status` (`GENERATED`, `EXPIRED`, `REVOKED`)
    - `file_content` (TEXT / BLOB)
    - `checksum` (VARCHAR: SHA-256 hex string)
    - `download_count` (INTEGER, default 0)
    - `last_downloaded_at` (DATETIME, Nullable)
    - `created_at` (DATETIME)

---

## Critical Invariants Enforced

1. **Verified Match Invariant**:
   - A referral requires `recommendation.match_state == 'VERIFIED_MATCH'`.
   - The associated `local_opportunity` must have `status == 'ACTIVE'`, unexpired date (`verification_expires_at > NOW()`), and open capacity (`seats_available > 0`).
2. **Geographic Scoping Invariant**:
   - Field workers and district planners can only access, modify, or create cases/referrals/snapshots in their assigned district.
   - Cross-district actions trigger `SECURITY_ACCESS_DENIED` written via an isolated audit transaction before returning HTTP 403 Forbidden.
3. **Data Isolation Invariant**:
   - Beneficiary-facing APIs (`/me/cases`, `/me/referrals`) strictly filter by authenticated user ID.
   - Staff casework notes (`is_staff_only = 1`), internal eligibility snapshots, and provider private phone numbers are never returned in beneficiary read models.
4. **Planning Privacy & Aggregation Invariants (Sprint 6)**:
   - Aggregations are strictly computed from authoritative verified records. `DRAFT`, `PENDING_VERIFICATION`, or `EXPIRED` opportunities are excluded from verified capacity.
   - Designed to support DPDP-aligned practices: cells representing $< 5$ unique beneficiaries are suppressed (`is_suppressed = true`).
   - Planning exports and snapshots are derived exclusively from immutable snapshots and strictly contain zero beneficiary PII, casework diaries, or provider private contacts.
   - Export download access is re-verified at download time against the caller's geographic scope.
