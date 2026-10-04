# PM-AJAY Acceptance Tests and Quality Assurance Matrix

**Project:** Jeevan Mitra PM-AJAY AI-Enabled Multilingual Livelihood Assistant<br>
**Module:** Feature-Phone Hindi IVR Simulator<br>
**Branch:** `feature/ivr-local-simulator`<br>
**Test Suite File:** `backend/tests/test_pm_ajay_acceptance.py`<br>
**Personas Fixture:** `backend/tests/factories/pm_ajay_personas.py`<br>
**Status:** All 10 PM-AJAY Acceptance Tests PASSED (100% Pass Rate)

> [!IMPORTANT]
> **Synthetic Test Data & Privacy Guarantee:** All beneficiary personas (Personas A through H) and associated telephone references (`9811000001` - `9811000008`) are **100% synthetic test fixtures**. They are used exclusively as test inputs to exercise backend database lookups. The IVR simulator strictly enforces privacy: raw telephone numbers and references are **never returned in API responses, event histories, or callback request payloads**, and are stored in the database exclusively as salted SHA-256 hashes.

---

## 1. Traceability Matrix: PM-AJAY Problem Statement to Verification

The table below links PM-AJAY core policy objectives to the implementation mechanisms and automated acceptance test suites.

| PM-AJAY Objective / Goal | Implementation Mechanism in IVR | Automated Acceptance Test | Pass/Fail |
| :--- | :--- | :--- | :---: |
| **1. Digital Barrier Elimination** | Pure DTMF audio prompts (0-9, #) in clear spoken Hindi without digital/app prerequisites | `test_pmajay_001_persona_a_training_seeker_journey` | **PASS** |
| **2. DPDP Act Compliance** | Explicit affirmative audio consent requested upfront; recorded in `consent_records` before profile linking | `test_pmajay_001_persona_a_training_seeker_journey` | **PASS** |
| **3. Aspiration Capture (Wage Employment)** | Training submenu with verified NSQF job roles (sewing, electrical, retail) | `test_pmajay_001_persona_a_training_seeker_journey` | **PASS** |
| **4. Aspiration Capture (Self-Employment)** | Schemes & Qualifications submenu connecting artisans to welfare and credit schemes | `test_pmajay_002_persona_b_self_employment_scheme_journey` | **PASS** |
| **5. Cognitive Overload Prevention** | Strict database-level SQL `LIMIT 3` on recommendations to keep feature-phone menus manageable | `test_pmajay_001`, `test_pmajay_002` | **PASS** |
| **6. Non-Discrimination & Inclusion** | Equal access for beneficiaries with accessibility needs without exclusionary branching | `test_pmajay_003_persona_c_accessibility_non_discrimination` | **PASS** |
| **7. Privacy of Unlinked Callers** | Anonymous callers receive generic guidance with zero PII or referral cross-contamination | `test_pmajay_004_persona_d_anonymous_caller_privacy` | **PASS** |
| **8. Multi-Beneficiary Data Isolation** | Complete tenant isolation between callers; caller F cannot inspect or infer caller E's case | `test_pmajay_005_persona_e_and_f_referral_isolation` | **PASS** |
| **9. Hallucination / Fabrication Defense** | Fallback to safe Hindi explanation (`NO_RESULTS`) when no verified match exists | `test_pmajay_006_persona_g_no_verified_matches_fallback` | **PASS** |
| **10. Human Field Worker Coordination** | Keypad '0' generates dedicated callback record in `ivr_callback_requests` with contextual reason | `test_pmajay_001`, `test_pmajay_002`, `test_pmajay_004` | **PASS** |
| **11. Repeated Keypress & Idempotency** | Duplicate submissions or repeated keypresses reuse existing callback; `#` repeats prompt safely | `test_pmajay_007_persona_h_callback_idempotency_replay`, `test_pmajay_008` | **PASS** |
| **12. Error Tolerance & Graceful Exit** | 2-attempt invalid retry policy with Hindi guidance, preventing infinite caller confusion | `test_pmajay_009_invalid_input_and_max_retries` | **PASS** |
| **13. Zero PII Exposure & Injection Defense** | SQL parameterization, phone redaction in logs/events, exclusion of sensitive identity numbers | `test_pmajay_010_security_and_privacy_checks` | **PASS** |

---

## 2. Detailed PM-AJAY Acceptance Test Specifications

---

### PMAJAY-001: Wage-Employment Training Seeker Journey
- **Test ID:** `PMAJAY-001`
- **Objective:** Validate end-to-end journey for a rural SC youth seeking wage employment training via feature phone.
- **Classification:** Functional / Core Journey
- **Risk Level:** High
- **Related Module:** `app.ivr.service`, `app.ivr.engine`, `app.ivr.repository`
- **Synthetic Persona / Input:**
  - Persona A: Rural youth, 10th pass, seeking sewing/garment skill training (`TEST_BENEFICIARY_A`).
  - Phone Reference: `9811000001`
- **Preconditions:**
  - Beneficiary profile seeded in `beneficiaries`.
  - 5 verified NSQF training courses seeded in `training_courses`.
- **Execution Steps:**
  1. Call `IVRService.start_session(caller="9811000001", language="hi-IN")`.
  2. Send digit `"1"` from `welcome` $\rightarrow$ transitions to `consent`.
  3. Send digit `"1"` from `consent` $\rightarrow$ records affirmative consent in `consent_records`.
  4. Send digit `"1"` from `identity` $\rightarrow$ reaches `main_menu`.
  5. Send digit `"1"` from `main_menu` $\rightarrow$ reaches `training`.
  6. Send digit `"1"` from `training` $\rightarrow$ inspects Course 1 details.
  7. Send digit `"0"` from `training` $\rightarrow$ requests field worker assistance.
  8. Send digit `"2"` from `callback_request` $\rightarrow$ concludes call at `goodbye`.
- **Expected Result:**
  - Prompt text delivered in clear Hindi.
  - `consent_records` row created with `capture_channel='ivr'`, `status='granted'`.
  - Maximum 3 verified training courses returned in context.
  - Callback record created with `callback_reason='training_support'`, `beneficiary_id='TEST_BENEFICIARY_A'`.
  - Final session status `completed`.
- **Actual Result:** All assertions passed. Exact match on Hindi prompts, limits, and callback reason.
- **Status:** **PASS**

---

### PMAJAY-002: Self-Employment & Welfare Scheme Seeker Journey
- **Test ID:** `PMAJAY-002`
- **Objective:** Validate journey for a traditional artisan seeking government livelihood schemes and credit assistance.
- **Classification:** Functional / Core Journey
- **Risk Level:** High
- **Related Module:** `app.ivr.service`, `app.ivr.engine`
- **Synthetic Persona / Input:**
  - Persona B: Leather artisan, traditional occupation, seeking PM-AJAY microcredit / capital equipment (`TEST_BENEFICIARY_B`).
  - Phone Reference: `9811000002`
- **Preconditions:**
  - 4 verified qualifications/schemes seeded in `qualifications` with `verification_status='VERIFIED'`.
- **Execution Steps:**
  1. Start session with caller `9811000002`.
  2. Grant affirmative consent and proceed to `main_menu`.
  3. Send digit `"2"` to enter `schemes` submenu.
  4. Send digit `"1"` to inspect Scheme 1 detail.
  5. Send digit `"0"` to request field worker guidance.
- **Expected Result:**
  - Verification disclaimer present in audio prompt: *"सत्यापन आवश्यक है"*.
  - Callback request generated with `callback_reason='scheme_information'`.
  - Linked to `TEST_BENEFICIARY_B`.
- **Actual Result:** Disclaimer rendered, callback created with exact `scheme_information` reason.
- **Status:** **PASS**

---

### PMAJAY-003: Accessibility & Non-Discrimination Verification
- **Test ID:** `PMAJAY-003`
- **Objective:** Ensure beneficiaries with accessibility or mobility challenges receive full access without exclusion.
- **Classification:** Inclusive UX / Equity
- **Risk Level:** Medium
- **Related Module:** `app.ivr.service`, `app.ivr.engine`
- **Synthetic Persona / Input:**
  - Persona C: Beneficiary with mobility challenges seeking nearby training (`TEST_BENEFICIARY_C`).
  - Phone Reference: `9811000003`
- **Preconditions:**
  - Beneficiary profile seeded with accessibility preference metadata.
- **Execution Steps:**
  1. Start session with caller `9811000003`.
  2. Grant consent and enter `training` menu.
  3. Validate unobstructed access to training items and worker handoff.
- **Expected Result:**
  - System presents standard training catalog without barriers or forced exit.
  - Full access to field worker handoff.
- **Actual Result:** Verified. All training items accessible, zero discriminatory logic.
- **Status:** **PASS**

---

### PMAJAY-004: Anonymous Caller Data Isolation and Privacy
- **Test ID:** `PMAJAY-004`
- **Objective:** Verify that an unregistered caller cannot access any beneficiary data, cases, or referrals.
- **Classification:** Security / Privacy / DPDP
- **Risk Level:** Critical
- **Related Module:** `app.ivr.service`, `app.ivr.repository`
- **Synthetic Persona / Input:**
  - Persona D: Anonymous caller with unlinked telephone (`9811000004`).
- **Preconditions:**
  - Unrelated beneficiary case seeded in database.
- **Execution Steps:**
  1. Start session with unlinked caller `9811000004`.
  2. Grant consent and navigate to `referral_status` (digit `"3"`).
  3. Send digit `"0"` to request callback.
- **Expected Result:**
  - Generic fallback prompt displayed: *"यदि आपका कोई पूर्व आवेदन है, तो उसकी जानकारी के लिए फील्ड वर्कर आपसे संपर्क करेंगे।"*
  - Zero PII or case IDs belonging to other beneficiaries revealed.
  - Callback request created with `beneficiary_id=None` and `callback_reason='referral_status'`.
- **Actual Result:** Zero PII leakage detected. Safe generic prompt played. Callback stored with null beneficiary ID.
- **Status:** **PASS**

---

### PMAJAY-005: Multi-Beneficiary Case and Referral Isolation
- **Test ID:** `PMAJAY-005`
- **Objective:** Guarantee strict multi-beneficiary data isolation between callers with active cases.
- **Classification:** Security / Tenant Isolation
- **Risk Level:** Critical
- **Related Module:** `app.ivr.service`, `app.ivr.repository`
- **Synthetic Persona / Input:**
  - Persona E: Active beneficiary (`TEST_BENEFICIARY_E`, `9811000005`) with active case in `"Under Review"` status.
  - Persona F: Separate caller (`9811000006`) with no active case.
- **Preconditions:**
  - `beneficiary_cases` seeded for Persona E.
- **Execution Steps:**
  1. Start session for Persona E $\rightarrow$ navigate to `referral_status`.
  2. Verify Persona E hears their own case status: *"आवेदन की स्थिति: Under Review"*.
  3. Start independent session for Persona F $\rightarrow$ navigate to `referral_status`.
  4. Verify Persona F does NOT hear Persona E's status and receives generic prompt.
- **Expected Result:** Strict isolation. Persona F has zero visibility into Persona E's status.
- **Actual Result:** Verified. Dynamic status delivered to E; generic prompt delivered to F.
- **Status:** **PASS**

---

### PMAJAY-006: Fallback When No Verified Matches Exist
- **Test ID:** `PMAJAY-006`
- **Objective:** Verify system behavior when zero verified training courses exist in the caller's district/sector.
- **Classification:** Resilience / Anti-Hallucination
- **Risk Level:** High
- **Related Module:** `app.ivr.service`, `app.ivr.engine`
- **Synthetic Persona / Input:**
  - Persona G: Caller in district with zero published courses (`9811000007`).
- **Preconditions:**
  - Database contains 0 published courses.
- **Execution Steps:**
  1. Start session for Persona G and grant consent.
  2. Navigate to `training` menu.
- **Expected Result:**
  - System does NOT crash or hallucinate fake courses.
  - Plays safe Hindi prompt: *"वर्तमान में कोई सत्यापित विकल्प उपलब्ध नहीं है। मुख्य मेन्यू के लिए 9 दबाएं या फील्ड वर्कर से सहायता के लिए 0 दबाएं।"*
- **Actual Result:** Verified. Prompt delivered with allowed digits `['0', '9', '#']`.
- **Status:** **PASS**

---

### PMAJAY-007: Callback Request Idempotency and Replay Protection
- **Test ID:** `PMAJAY-007`
- **Objective:** Prevent duplicate worker callback records when a caller repeatedly presses '0'.
- **Classification:** Integrity / Anti-Replay
- **Risk Level:** Medium
- **Related Module:** `app.ivr.service`, `app.ivr.repository`
- **Synthetic Persona / Input:**
  - Persona H: Caller repeatedly pressing keypad options (`9811000008`).
- **Preconditions:**
  - Clean database state.
- **Execution Steps:**
  1. Start session for Persona H and enter `training` menu.
  2. Send digit `"0"` (creates first callback request).
  3. Send digit `"0"` again within the same session.
  4. Query `ivr_callback_requests` table count for session.
- **Expected Result:**
  - System returns existing callback request without creating duplicate record.
  - Exactly 1 row in `ivr_callback_requests`.
- **Actual Result:** Verified. Count equals 1. Callback ID is identical.
- **Status:** **PASS**

---

### PMAJAY-008: Audio Repeat and Menu Navigation Controls
- **Test ID:** `PMAJAY-008`
- **Objective:** Verify feature-phone navigation ergonomics: repeat audio (`#`) and return to main menu (`9`).
- **Classification:** Usability / Ergonomics
- **Risk Level:** Medium
- **Related Module:** `app.ivr.engine`
- **Execution Steps:**
  1. Navigate to `schemes` submenu.
  2. Send digit `"#"` $\rightarrow$ verify prompt text repeated, state unchanged (`schemes`), retry count unchanged (`0`).
  3. Send digit `"9"` $\rightarrow$ verify immediate return to `main_menu`.
- **Expected Result:** Predictable navigation without unintended state corruption or penalty.
- **Actual Result:** Verified. `#` maintains state; `9` safely returns to `main_menu`.
- **Status:** **PASS**

---

### PMAJAY-009: Invalid Input Handling and Maximum Retry Threshold
- **Test ID:** `PMAJAY-009`
- **Objective:** Prevent callers from getting trapped by miskeying; enforce 2-retry limit before graceful exit.
- **Classification:** Resilience / Error Handling
- **Risk Level:** Medium
- **Related Module:** `app.ivr.engine`
- **Execution Steps:**
  1. At `welcome` state (accepted digits: `['1', '2']`), send digit `"7"`.
  2. Verify retry count = 1, prompt contains invalid input explanation (`INVALID_INPUT`).
  3. Send digit `"8"` (second invalid input).
  4. Verify state transitions to `ERROR_RETRY`, status `completed`, and session terminated gracefully.
- **Expected Result:** No infinite loops; caller received audio explanation before termination.
- **Actual Result:** Verified. Exactly 2 retries allowed; state transitioned to `ERROR_RETRY`.
- **Status:** **PASS**

---

### PMAJAY-010: Security, Injection Defense, and Data Minimization
- **Test ID:** `PMAJAY-010`
- **Objective:** Validate SQL injection safety, phone number masking in audit logs, and absence of sensitive PII.
- **Classification:** Security / Compliance / DPDP
- **Risk Level:** Critical
- **Related Module:** `app.ivr.repository`, `app.ivr.service`, `app.ivr.schemas`
- **Execution Steps:**
  1. Start session with malicious SQL injection caller reference: `"' OR 1=1; --"`.
  2. Inspect database query execution and session row.
  3. Inspect audit events in `ivr_events` for caller reference masking.
  4. Verify absence of Aadhaar, PAN, OTP, or biometric fields in IVR tables.
- **Expected Result:**
  - SQL payload parameterized safely; no syntax error or unauthorized data access.
  - Phone number masked in audit trails.
  - Zero sensitive identity fields in schema.
- **Actual Result:** Verified. Safe parameterization, masked phone representation, zero prohibited columns.
- **Status:** **PASS**
