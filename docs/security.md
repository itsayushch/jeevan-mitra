# JeevanMitra 2.0 Security Guidelines

## 1. Principles
- **Verification before Action**: Only human verified opportunities map to referrals. An `INTEREST_MATCH` cannot be referred.
- **Grounded AI Only**: LLMs operate on structured, verified data with zero hallucinations. Inferred fields are never auto-confirmed.
- **Privacy by Design**: Minimum data collection. Designed to support DPDP-aligned practices with affirmative, granular, versioned consent.

---

## 2. API Security & Scoping
- **Authentication**: JWT token with rotating refresh tokens and httpOnly cookies for sessions.
- **Role-Based Access Control (RBAC)**:
  - `super_admin`: Full system oversight.
  - `catalogue_manager`: Manages verified qualifications and training providers.
  - `district_admin`: District oversight, outcome verification, case reassignment.
  - `field_worker`: Case management and referral progression strictly scoped to assigned district.
  - `beneficiary`: Access restricted strictly to own records via authenticated user ID.
- **Geographic Scoping**:
  - Field workers are assigned a district (e.g. `Moradabad`).
  - Cross-district access attempts are blocked with HTTP 403 Forbidden.

---

## 3. Isolated Audit Logging Pattern
To prevent accidental partial commits when a 403 is raised:
1. When a scope or permission check fails:
   - Roll back any pending business transaction.
   - Open a dedicated, isolated audit connection/transaction.
   - Write `SECURITY_ACCESS_DENIED` with actor ID, target resource, and attempted action.
   - Commit *only* the audit transaction.
   - Raise HTTP 403 Forbidden.
2. Under no circumstance should `conn.commit()` be called on the business session before raising an error.

---

## 4. Privacy & Beneficiary Data Isolation
- **Staff Casework Notes**: Notes flagged with `is_staff_only = 1` are strictly excluded from all `/me/*` queries.
- **Provider Private Information**: Internal contact details (private phone/email) are withheld from beneficiaries.
- **Eligibility Snapshots**: Detailed internal evaluation snapshots are accessible only to staff and auditors.
- **Right to Erasure (DPDP)**: Invoking `DELETE /api/v1/beneficiaries/me` completely anonymizes profile answers, interviews, and session data, while preserving immutable audit logs for regulatory compliance.

---

## 5. District Planning, Aggregations & Controlled Exports Security (Sprint 6)
- **Role Restrictions**: Access to `/api/v1/planning/*` is restricted exclusively to `district_admin`, `auditor`, and `super_admin`. Unprivileged roles (`beneficiary`, `field_worker`, `guest`) receive HTTP 403 Forbidden with an isolated `SECURITY_ACCESS_DENIED` audit log.
- **Geographic Scoping**: `district_admin` and `auditor` can only access their assigned district. Cross-district queries are rejected with HTTP 403 Forbidden and an isolated security audit log. `super_admin` has global multi-district visibility.
- **Small-Cell Suppression ($k=5$)**: To prevent re-identification under DPDP-aligned practices, any aggregated cell or breakdown representing fewer than 5 unique beneficiaries is automatically suppressed (`is_suppressed = true`, values masked or nullified).
- **Controlled Export Lifecycles**:
  - Exports (CSV and PDF) are generated exclusively from immutable frozen snapshots, never from live operational state.
  - Every export record is hashed with SHA-256 for cryptographic tamper-evidence.
  - **Re-authorization at Download Time**: When a download is requested via `/api/v1/planning/exports/{id}/download`, the user's current district scope is verified again before streaming the file.
  - Expired exports return HTTP 410 Gone.
  - Zero beneficiary PII, caseworker notes, or private phone numbers are ever included in planning snapshots or export outputs.
