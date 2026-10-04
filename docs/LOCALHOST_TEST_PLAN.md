# Jeevan Mitra - Localhost QA and Verification Test Plan

**Project:** Jeevan Mitra (PM-AJAY AI-Enabled Multilingual Livelihood Assistant)<br>
**Module:** Feature-Phone Friendly Hindi IVR Simulator (Phase 1 Local Mock)<br>
**Branch:** `feature/ivr-local-simulator`<br>
**Baseline Commit:** `593930e`<br>
**Target Environment:** Localhost / Offline / Developer Workstation (Windows/Linux/macOS)<br>
**Scope:** Standalone mock IVR simulator, DPDP consent gating, DTMF state machine, human handoff callbacks, privacy isolation, and regression verification.

> [!IMPORTANT]
> **Data Privacy Mandate:** All caller references, telephone numbers, and beneficiary profiles mentioned in this document and related test suites are **strictly synthetic test fixtures**. No production or personally identifiable data is used. The IVR API responses, logs, and database tables strictly exclude plaintext phone numbers (using salted SHA-256 hashes in `ivr_sessions.caller_reference_hash` and zero contact columns in `ivr_callback_requests`).

---

## 1. Environment Prerequisites and Architecture

### 1.1 Host Environment
- **Operating System:** Windows 10/11, macOS 12+, or Ubuntu 22.04+ (Verified on Windows with PowerShell).
- **Python Runtime:** Python 3.10+ (Recommended: Python 3.11.x).
- **Database Engine:** SQLite 3.35+ (via Python standard library `sqlite3`), production-parity SQL syntax.
- **Package Manager:** `pip` with `virtualenv` or `venv`.

### 1.2 Isolation & Zero-External-Dependency Guarantee
- **Telephony:** `IVR_PROVIDER=mock`. No live connection to Exotel, Twilio, Plivo, or cellular networks.
- **AI/LLM Services:** Offline rule-based template generation. No live calls to Google Gemini, OpenAI, or external APIs.
- **Channels:** Pure local HTTP endpoints simulating DTMF keypad inputs (`0-9`, `#`).
- **PII Protection:** Zero production data. All test fixtures use synthetic identifiers (`TEST_CALLER_A`) or unassigned test numbers (`9811000001` - `9811000008`) labeled as TEST ONLY.

---

## 2. Local Environment Configuration

### 2.1 Configuration File (`backend/.env`)
Verify or create `backend/.env` (ensure it remains untracked in `.gitignore`):

```ini
# Application Core
APP_NAME="Jeevan Mitra Backend"
ENVIRONMENT="development"
DEBUG=true
PORT=4000
HOST="127.0.0.1"

# Database Configuration (SQLite Local)
DATABASE_PATH="app.db"

# IVR Simulator Configuration
IVR_PROVIDER="mock"
IVR_DEFAULT_LANGUAGE="hi-IN"
IVR_SESSION_TIMEOUT_SECONDS=600
IVR_MAX_INVALID_ATTEMPTS=2
IVR_SIMULATOR_ENABLED=true

# Security & Compliance
DPDP_CONSENT_REQUIRED=true
MASK_PII_LOGS=true
SECRET_KEY="local-testing-secret-key-not-for-production"
```

---

## 3. Setup and Execution Commands

All commands must be executed from the `backend/` directory with the virtual environment activated.

### 3.1 Dependencies Installation
```powershell
# Windows PowerShell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

### 3.2 Database Migration and Verification
Run Alembic migrations to apply all schema updates up to the IVR head:

```powershell
# Run migrations
python -m alembic upgrade head

# Verify current revision
python -m alembic current
# Expected output: b2c3d4e5f6a7 (head)
```

### 3.3 Running Automated Test Suites

#### A. Comprehensive IVR Engine, Service, API, and Acceptance Tests
```powershell
python -m pytest tests/test_ivr_engine.py tests/test_ivr_service.py tests/test_ivr_api.py tests/test_pm_ajay_acceptance.py -v
```
*Result: 43 passed in ~55s (100% pass rate).*

#### B. Core Regression Test Suite (Consents, Referrals, Auth)
```powershell
python -m pytest tests/test_consents.py tests/test_referrals.py tests/test_auth.py -v
```
*Result: 13 passed in ~12s (100% pass rate).*

#### C. Full Repository Test Suite
```powershell
python -m pytest tests -v
```
*Result: 204 passed, 4 pre-existing legacy sprint failures on baseline branch.*

#### D. Static Code Quality & Linting
```powershell
python -m ruff check app/ivr tests/test_ivr_engine.py tests/test_ivr_service.py tests/test_ivr_api.py tests/test_pm_ajay_acceptance.py tests/factories/pm_ajay_personas.py
python -m flake8 app/ivr tests/test_ivr_engine.py tests/test_ivr_service.py tests/test_ivr_api.py tests/test_pm_ajay_acceptance.py tests/factories/pm_ajay_personas.py --max-line-length=120
```
*Result: All checks passed (0 errors).*

### 3.4 Starting the Local Backend Server
```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 4000 --reload
```
- Swagger UI / OpenAPI: `http://localhost:4000/docs`
- Healthcheck: `http://localhost:4000/api/v1/health`

---

## 4. Comprehensive Test Catalog

### 4.1 IVR Simulator Core Tests (IVR-001 to IVR-028)

| Test ID | Module / Component | Objective | Verification Criteria | Status |
| :--- | :--- | :--- | :--- | :---: |
| **IVR-001** | `IVREngine` | Welcome state initial prompt rendering | Returns `WELCOME` prompt, accepts digits `['1', '2']`, `status=active` | PASS |
| **IVR-002** | `IVREngine` | Welcome -> Consent transition | Input `1` transitions to `CONSENT` state | PASS |
| **IVR-003** | `IVREngine` | Welcome -> Exit termination | Input `2` transitions to `GOODBYE` state with `status=completed` | PASS |
| **IVR-004** | `IVREngine` | Welcome invalid digit handling | Digit `3` retains `WELCOME` state, increments retry count | PASS |
| **IVR-005** | `IVREngine` | Consent affirmative grant | Input `1` transitions to `IDENTITY`, sets `consent_granted=True` | PASS |
| **IVR-006** | `IVREngine` | Consent denial / refusal | Input `2` transitions to `GOODBYE` with `status=terminated`, prompt `CONSENT_REFUSED` | PASS |
| **IVR-007** | `IVREngine` | Identity -> Main Menu navigation | Input `1` transitions to `MAIN_MENU` | PASS |
| **IVR-008** | `IVREngine` | Identity -> Direct Worker Callback | Input `0` creates callback request with reason `general_help` | PASS |
| **IVR-009** | `IVREngine` | Main Menu -> Training Submenu | Input `1` transitions to `TRAINING` state | PASS |
| **IVR-010** | `IVREngine` | Main Menu -> Schemes Submenu | Input `2` transitions to `SCHEMES` state | PASS |
| **IVR-011** | `IVREngine` | Main Menu -> Referral Status | Input `3` transitions to `REFERRAL_STATUS` state | PASS |
| **IVR-012** | `IVREngine` | Main Menu -> Worker Callback | Input `0` transitions to `CALLBACK_REQUEST` with `general_help` | PASS |
| **IVR-013** | `IVREngine` | Training -> Item Selection | Input `1` selects first course detail, retains `TRAINING` state | PASS |
| **IVR-014** | `IVREngine` | Training -> Worker Callback Handoff | Input `0` creates callback with `callback_reason=training_support` | PASS |
| **IVR-015** | `IVREngine` | Schemes -> Item Selection | Input `1` selects first qualification/scheme detail with disclaimer | PASS |
| **IVR-016** | `IVREngine` | Schemes -> Worker Callback Handoff | Input `0` creates callback with `callback_reason=scheme_information` | PASS |
| **IVR-017** | `IVREngine` | Referral Status -> Worker Callback | Input `0` creates callback with `callback_reason=referral_status` | PASS |
| **IVR-018** | `IVREngine` | Global Navigation (Return to Menu) | Input `9` from any submenu returns to `MAIN_MENU` | PASS |
| **IVR-019** | `IVREngine` | Global Repeat Control | Input `#` repeats current prompt without modifying context/retry count | PASS |
| **IVR-020** | `IVREngine` | Max Retries Threshold Enforcement | Exceeding 2 invalid attempts transitions to `ERROR_RETRY` | PASS |
| **IVR-021** | `IVREngine` | Error state termination | Terminal error plays `ERROR_RETRY` prompt, closes session | PASS |
| **IVR-022** | `IVREngine` | Callback Submenu Completion | Input `2` from `CALLBACK_REQUEST` transitions to `GOODBYE` | PASS |
| **IVR-023** | `IVRService` | Session creation and persistence | Creates row in `ivr_sessions` with UUID, stores context and expiry | PASS |
| **IVR-024** | `IVRService` | DPDP Consent DB Registration | Granting consent writes record to `consent_records` with channel `ivr` | PASS |
| **IVR-025** | `IVRService` | Training & Schemes Top-3 Limiting | Query limits results to 3 verified records, avoids cognitive overload | PASS |
| **IVR-026** | `IVRService` | Callback Idempotency Protection | Duplicate `0` presses return existing callback request record | PASS |
| **IVR-027** | `IVRService` | Session Expiration Enforcement | Sessions past `expires_at` are rejected with `IVRSessionExpiredError` | PASS |
| **IVR-028** | `IVRService` | State Audit Logging | Every state transition records an event in `ivr_events` | PASS |

---

### 4.2 Security, Privacy, and Data Protection Tests

| Test ID | Area | Objective | Verification Criteria | Status |
| :--- | :--- | :--- | :--- | :---: |
| **PRIVACY-IVR-001** | Privacy Exclusion | Symbolic reference non-leakage | Request with `TEST_CALLER_A` yields responses with zero occurrence of `TEST_CALLER_A` | PASS |
| **PRIVACY-IVR-002** | Privacy Exclusion | Numeric phone non-leakage | Request with `9811000001` yields responses and callbacks with zero occurrence of raw phone | PASS |
| **PRIVACY-IVR-003** | Audit Minimization | Sanitization in logs/events | Internal payload logging strips phone/token keys via `sanitize_payload_for_logging` | PASS |
| **PRIVACY-IVR-004** | Diagnostic Masking | Safe masking rule | Phone masking reveals only trailing 4 digits (`******0001`); redacts all others | PASS |
| **SEC-API-001** | Simulator Gating | Gating when disabled | If `IVR_SIMULATOR_ENABLED=false`, simulator endpoints return HTTP 403 Forbidden | PASS |
| **SEC-API-002** | Input Validation | Single-digit DTMF constraint | Strings with length > 1 (e.g., `"12"`) or letters (`"A"`) return HTTP 422 | PASS |
| **SEC-API-003** | Injection Defense | SQL parameterization | SQL injection payloads in caller reference (`' OR 1=1 --`) safely escaped | PASS |
| **SEC-API-004** | Session Integrity | Non-existent session handling | Calling `/input` with fake UUID returns HTTP 404 Not Found | PASS |
| **SEC-API-005** | Closed Session Guard | Inputs on terminal sessions | Sending inputs to `completed` or `terminated` sessions returns HTTP 400 | PASS |
| **SEC-API-006** | Idempotency Header | Replay attack prevention | Identical `idempotency_key` returns cached result without reprocessing | PASS |
| **PRIV-001** | Consent Gating | No beneficiary lookup before consent | Beneficiary identity not linked or queried until consent granted | PASS |
| **PRIV-002** | DPDP Audit | Affirmative consent record | Record persisted with timestamp, channel `ivr`, and `granted` status | PASS |
| **PRIV-003** | Consent Refusal | Data purging on refusal | Refusal terminates call immediately without saving beneficiary profile | PASS |
| **PRIV-005** | Sensitive Fields | Exclusion of sensitive PII | No Aadhaar, PAN, bank account, or OTP fields stored or queried in IVR tables | PASS |
| **PRIV-006** | Anonymous Isolation | Anonymous caller data isolation | Callers without linked beneficiary cannot view any case or referral data | PASS |
| **PRIV-007** | Cross-Beneficiary Guard | Referral status isolation | Caller E cannot view Caller F's case status under any condition | PASS |
| **PRIV-008** | Callback Privacy | Null beneficiary for anonymous | Anonymous callbacks record `beneficiary_id=None` without leaking IDs | PASS |
| **PRIV-010** | Audio Storage | Zero voice recording | Phase 1 stores zero audio wav/mp3 files; only DTMF events recorded | PASS |

---

### 4.3 Database and Migration Verification (DB-001 to DB-014)

| Test ID | Area | Objective | Verification Criteria | Status |
| :--- | :--- | :--- | :--- | :---: |
| **DB-001** | Migration Script | Alembic migration file presence | `a1b2c3d4e5f6_ivr_tables.py` exists with upgrade/downgrade methods | PASS |
| **DB-002** | Table: `ivr_sessions` | Table creation & schema | Contains columns: `id`, `provider`, `provider_call_id`, `caller_reference_hash`, `beneficiary_id`, `current_state`, `language`, `status`, `invalid_attempt_count`, `current_context_json`, `started_at`, `updated_at`, `ended_at`, `expires_at` | PASS |
| **DB-003** | Table: `ivr_events` | Table creation & schema | Contains columns: `id`, `session_id`, `event_type`, `state_before`, `state_after`, `digit`, `prompt_key`, `idempotency_key`, `safe_payload_json`, `created_at` | PASS |
| **DB-004** | Table: `ivr_callback_requests` | Table creation & schema | Contains columns: `id`, `session_id`, `beneficiary_id`, `callback_reason`, `status`, `assigned_worker_id`, `case_id`, `created_at`, `updated_at` | PASS |
| **DB-005** | Foreign Keys | Session foreign key constraints | `ivr_events.session_id` references `ivr_sessions.id` | PASS |
| **DB-006** | Cascade Delete | Cleanup cascading | Deleting session removes related events and orphaned references | PASS |
| **DB-007** | Indexing | Index on `caller_reference_hash` | Index exists on `ivr_sessions.caller_reference_hash` for rapid lookups | PASS |
| **DB-008** | Indexing | Index on `status` | Index exists on `ivr_callback_requests.status` for worker queues | PASS |
| **DB-009** | JSON Serialization | Context dictionary storage | SQLite stores `context` and `payload` as valid JSON strings | PASS |
| **DB-010** | MockRow Compatibility | Row mapping protocol | `MockRow` supports `.get(key, default)` and `__iter__()` without error | PASS |
| **DB-011** | Idempotency Index | Unique callback constraint | Unique index prevents duplicate pending callbacks for same session | PASS |
| **DB-012** | Timestamp Storage | UTC ISO8601 formatting | Timestamps stored in standard UTC ISO format | PASS |
| **DB-013** | Migration Rollback | Downgrade capability | Running `alembic downgrade -1` cleanly drops the 3 IVR tables | PASS |
| **DB-014** | Migration Re-upgrade | Re-application capability | Running `alembic upgrade head` cleanly recreates the 3 IVR tables | PASS |

---

## 5. Local Manual Verification Flow

Execute the standard manual flow against `http://127.0.0.1:4000`:

1. **Start Call** (`POST /api/v1/ivr/simulate/start` with `TEST_CALLER_A`): Returns session ID, state `welcome`, Hindi greeting. (Zero caller reference in response).
2. **Press 1 at Welcome**: State moves to `consent`. Hindi DPDP consent notice delivered.
3. **Press 1 to Accept Consent**: State moves to `identity`. Affirmative consent saved in `consent_records`.
4. **Press 1 at Identity**: State moves to `main_menu`. Options 1 (Training), 2 (Schemes), 3 (Referrals), 0 (Worker) presented.
5. **Press 1 at Main Menu for Training**: State moves to `training`. Up to 3 verified courses spoken.
6. **Press 0 from Training for Callback**: State moves to `callback_request`. Worker callback request created with reason `training_support`.
7. **Press 2 to Exit**: State moves to `goodbye`. Session status `completed`.
