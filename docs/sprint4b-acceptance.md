# Sprint 4B — Verification Workflow Acceptance Test Report

## 1. Executive Summary & Objective

**Sprint 4B Objective**: Prove, from a clean database, that JeevanMitra enforces its core verification guarantee:

> **Platform Core Invariant**:
> A beneficiary can receive an **Interest Match** based on a verified national qualification, but can receive a **Verified Match** and eligibility for referral **only when an authorized, correctly scoped field worker verifies an active, non-expired local opportunity with required evidence**.

This acceptance test exercises the complete lifecycle across all system tiers:
1. Database state and integrity constraints
2. Service-layer calculations (`MatchStateService`, `RecommendationService`, `OpportunityVerificationService`, `OpportunityExpiryService`)
3. API authorization (RBAC and geographic scope checks)
4. Beneficiary-facing API response sanitization (no internal operational data leaked)
5. Audit trail completeness (append-only log of lifecycle transitions and security denials)
6. Read-time and batch verification expiry degradation

The test suite executed against a clean database initialized via Alembic migrations, achieving **100% pass rate** (`72 passed, 0 failed` overall backend suite).

---

## 2. Tested Actors & Roles

| Actor ID | Role | Geographic Scope | Purpose in Test |
|---|---|---|---|
| `usr_cat_mgr_a` | `catalogue_manager` | System-wide | Publishes verified qualifications; maps learning courses |
| `usr_ben_a` | `beneficiary` | District Alpha / Block Alpha-1 | Receives Interest Match & Verified Match recommendations |
| `usr_fw_alpha` | `field_worker` | District Alpha / Block Alpha-1 | Creates provider & opportunity, attaches evidence, verifies |
| `usr_fw_beta` | `field_worker` | District Beta / Block Beta-1 | Cross-district worker used for negative authorization tests |
| `usr_auditor_a` | `auditor` | District Alpha | Inspects opportunity details and audit trails; read-only |
| `usr_super_admin`| `super_admin` | Global | System administration |

---

## 3. The 12-Step Lifecycle Validation

### Step 1: Qualification Creation, Publishing, and Course Mapping
- **Actor**: `usr_cat_mgr_a` (`catalogue_manager`)
- **Actions**:
  1. `POST /api/v1/admin/qualifications` — Creates "Basic Electrical Repair Assistant" in sector "Electronics".
  2. `PATCH /api/v1/admin/qualifications/{id}` — Sets `verification_status = 'VERIFIED'`.
  3. `POST /api/v1/admin/qualifications/{id}/map-course` — Maps to training course `course_elec_01`.
  4. Database seed: Creates an irrelevant qualification (NSQF Level 8) for negative ranking checks.
- **Assertions Proven**:
  - Qualification appears in beneficiary catalogue `GET /api/v1/qualifications`.
  - Beneficiary response excludes internal provenance (`source_url`, `created_by_user_id`).
  - Staff detail `GET /api/v1/admin/qualifications/{id}` contains full provenance.
  - Catalogue manager is denied (`403 Forbidden`) when attempting to create local opportunities.

### Step 2: Interest Match with No Local Availability
- **Actor**: `usr_ben_a` (`beneficiary`)
- **Actions**:
  1. `GET /api/v1/opportunities/matches/{qual_id}` — Evaluates match state before local opportunities exist.
  2. `POST /api/v1/recommendations/generate` — Generates AI livelihood recommendations.
- **Assertions Proven**:
  - Match state evaluates to `INTEREST_MATCH`.
  - `canRequestReferral` is `False`.
  - `canRequestWorkerSupport` is `True`.
  - Beneficiary message indicates local batch verification is pending.
  - `recommendation_match_state` record in database holds `match_state = 'INTEREST_MATCH'`.

### Step 3: Draft Opportunity Creation
- **Actor**: `usr_fw_alpha` (`field_worker`)
- **Actions**:
  1. `POST /api/v1/staff/opportunity-providers` — Creates "Alpha Skills Training Centre" in District Alpha.
  2. `POST /api/v1/staff/opportunities` — Creates opportunity in `DRAFT` status with 25 total seats, 20 available.
- **Assertions Proven**:
  - Opportunity is NOT visible in beneficiary endpoint `GET /api/v1/opportunities`.
  - Beneficiary still receives only `INTEREST_MATCH` (`canRequestReferral == False`).
  - `audit_events` logs `LOCAL_OPPORTUNITY_CREATED` with actor `usr_fw_alpha`.

### Step 4: Invalid Verification Prevention
- **Actor**: `usr_fw_alpha` (`field_worker`)
- **Action**: `POST /api/v1/staff/opportunities/{opp_id}/verify` with no approved evidence.
- **Assertions Proven**:
  - API rejects the transition with `400 Bad Request` citing missing approved evidence.
  - Database opportunity status remains `DRAFT`.

### Step 5: Submit Evidence and Verify Opportunity
- **Actor**: `usr_fw_alpha` (`field_worker`)
- **Actions**:
  1. `POST /api/v1/staff/opportunities/{opp_id}/evidence` — Attaches approved `FIELD_VISIT` inspection report.
  2. `POST /api/v1/staff/opportunities/{opp_id}/submit` — Transitions `DRAFT -> PENDING_VERIFICATION`.
  3. `POST /api/v1/staff/opportunities/{opp_id}/verify` — Transitions `PENDING_VERIFICATION -> ACTIVE` with future expiry (60 days).
- **Assertions Proven**:
  - Status becomes `ACTIVE`; `verified_by_user_id` and `verified_at` are recorded.
  - `opportunity_verification_events` appends event `VERIFIED`.
  - `audit_events` records `OPPORTUNITY_VERIFIED`.
  - Staff detail `GET /api/v1/staff/opportunities/{opp_id}` returns attached evidence and verification history.

### Step 6: Verified Match Computation
- **Actor**: `usr_ben_a` (`beneficiary`)
- **Actions**:
  1. `GET /api/v1/opportunities/matches/{qual_id}` — Evaluates match state with active, verified opportunity.
  2. `POST /api/v1/recommendations/generate` — Regenerates recommendations.
- **Assertions Proven**:
  - `matchState` evaluates to `VERIFIED_MATCH`.
  - `canRequestReferral` is `True`.
  - `local_availability.status` is `verified_open`.
  - Database table `recommendation_match_state` updates to `VERIFIED_MATCH` referencing `opp_id`.

### Step 7: Cross-Scope Access Denial
- **Actor**: `usr_fw_beta` (`field_worker`, assigned to District Beta / Block Beta-1)
- **Actions**:
  1. `GET /api/v1/staff/opportunities/{opp_id}` (Alpha opp) -> `403 Forbidden`.
  2. `POST /api/v1/staff/opportunities/{opp_id}/evidence` -> `403 Forbidden`.
  3. `POST /api/v1/staff/opportunities/{opp_id}/verify` -> `403 Forbidden`.
  4. `PATCH /api/v1/staff/opportunities/{opp_id}` -> `403 Forbidden`.
  5. `POST /api/v1/staff/opportunities/{opp_id}/close` -> `403 Forbidden`.
- **Assertions Proven**:
  - Every mutation and staff read across district boundaries is blocked (`403`).
  - Opportunity state in District Alpha is unchanged (remains `ACTIVE`, seats = 20).
  - Security audit events (`SECURITY_ACCESS_DENIED`) are committed to `audit_events` for `usr_fw_beta`.

### Step 8: Beneficiary Data-Exposure Sanitization
- **Actor**: `usr_ben_a` (`beneficiary`)
- **Actions**: Inspect payloads across `GET /opportunities`, `GET /opportunities/{id}`, `POST /recommendations/generate`, and `GET /qualifications/{id}`.
- **Assertions Proven**:
  - Zero internal operational fields are exposed to beneficiaries.
  - Prohibited fields absent: `storage_key`, `external_url`, `note`, `contact_phone`, `contact_email`, `verified_by_user_id`, `created_by_user_id`, `actor_user_id`, `before_json`, `after_json`, `metadata_json`, `eligibility_notes`, `accessibility_notes`.

### Step 9: Capacity Depletion (Mark Full)
- **Actor**: `usr_fw_alpha` (`field_worker`)
- **Action**: `PATCH /api/v1/staff/opportunities/{opp_id}` with `seats_available = 0`.
- **Assertions Proven**:
  - Status automatically transitions from `ACTIVE` to `FULL`.
  - Beneficiary matches degrade: `matchState` becomes `INTEREST_MATCH` and `canRequestReferral` becomes `False`.
  - `opportunity_verification_events` appends `MARKED_FULL`.
  - `audit_events` records `OPPORTUNITY_MARKED_FULL`.

### Step 10: Capacity Restoration & Reverification
- **Actor**: `usr_fw_alpha` (`field_worker`)
- **Actions**:
  1. `PATCH /api/v1/staff/opportunities/{opp_id}` with `seats_available = 15`.
  2. `POST /api/v1/staff/opportunities/{opp_id}/reverify` with updated future expiry (+90 days).
- **Assertions Proven**:
  - Status returns to `ACTIVE`.
  - Verification history preserves prior events and appends `REVERIFIED`.
  - Beneficiary receives `VERIFIED_MATCH` again with `canRequestReferral == True`.

### Step 11: Read-Time Expiry Degradation
- **Actor**: System Clock / Stored Database State
- **Action**: `verification_expires_at` is set in the past directly in the database without running background jobs.
- **Assertions Proven**:
  - `GET /api/v1/opportunities` immediately omits the expired opportunity.
  - `GET /api/v1/opportunities/{opp_id}` returns `404 Not Found`.
  - Beneficiary match degrades to `INTEREST_MATCH` (`canRequestReferral == False`).
  - Stored status in the database remains `ACTIVE` until the lifecycle job runs.

### Step 12: Scheduled Expiry Job & Auditor Inspections
- **Actor**: `OpportunityExpiryService`, then `usr_auditor_a` (`auditor`)
- **Actions**:
  1. `OpportunityExpiryService.process_expiries(conn, dry_run=True)` — Identifies candidate without mutating.
  2. `OpportunityExpiryService.process_expiries(conn, dry_run=False)` — Transitions status to `EXPIRED`, appends event, recalculates matches.
  3. Second run with `dry_run=False` — Idempotent (0 modified).
  4. Auditor queries `GET /api/v1/audit/events?entity_type=local_opportunity`.
  5. Auditor queries `GET /api/v1/staff/opportunities/{opp_id}`.
  6. Auditor attempts mutations (`create`, `verify`, `patch`).
- **Assertions Proven**:
  - Stored status in DB transitions to `EXPIRED`.
  - Append-only events recorded: `opportunity_verification_events` (`EXPIRED`) and `audit_events` (`OPPORTUNITY_EXPIRED`).
  - Auditor has read-only access: reads audit trail and staff opportunity details (`200 OK`).
  - Auditor is rejected with `403 Forbidden` on create, verify, and patch attempts.

---

## 4. Test Suite Execution Metrics

```
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-8.3.4, pluggy-1.6.0
rootdir: C:\Users\DELL\JEEVAN-MITRA 2.0\backend
configfile: pytest.ini
plugins: anyio-4.12.1, langsmith-0.7.9, asyncio-0.25.3, cov-7.1.0, mock-3.15.1
collected 72 items

tests/acceptance/test_sprint4b_verification_workflow.py .                [  1%]
tests/test_audit.py .....                                                [  8%]
tests/test_auth.py ...............                                       [ 29%]
tests/test_auth_sprint2.py ............                                  [ 45%]
tests/test_auth_sprint3.py .........                                     [ 58%]
tests/test_beneficiary.py .....                                          [ 65%]
tests/test_catalogue.py .....                                            [ 72%]
tests/test_channels.py ...                                               [ 76%]
tests/test_interview.py .....                                            [ 83%]
tests/test_learning_content.py ....                                      [ 88%]
tests/test_opportunities.py .....                                        [ 95%]
tests/test_referrals.py .                                                [ 97%]
tests/test_training_service.py ..                                        [100%]

============================== 72 passed in 43.25s ==============================
```

All 72 tests passed with 0 failures and 0 errors. Sprint 4B acceptance criteria are completely satisfied.
