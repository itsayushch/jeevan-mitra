# JeevanMitra 2.0 Security Architecture & Test Plan

## 1. Security Architecture & Threat Boundaries

JeevanMitra 2.0 processes sensitive citizen socio-economic profiles, livelihood aspirations, and casework notes. The system implements defense-in-depth across six distinct trust zones:

```
[ Beneficiary Device ]
         │ (TLS 1.3 / Strict CSP)
         ▼
[ Ingress Reverse Proxy ] ── Rate Limiting, Request ID, Security Headers
         │
         ▼
[ FastAPI Backend Application ]
   ├── Authentication Layer: JWT + Refresh Token Rotation
   ├── Authorization Layer: RBAC + Geographic Scoping Filter
   ├── Privacy Layer: k=5 Minimum Cell-Size Suppression
   └── Redaction Filter: Zero PII / Credentials in Logs
         │
         ▼
[ Isolated Storage / Database ] ── Parameterized Queries, Encrypted Backups
```

---

## 2. Role-Based Access Control (RBAC) & Scope Matrix

| Role | Beneficiary Profile | Staff Inbox | Case Notes | Planning Dashboards | Immutable Snapshots | Catalogue Admin |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **beneficiary** | Own record only | DENIED | Own safe notes only | DENIED | DENIED | DENIED |
| **field_worker** | Scoped district | Assigned cases | Full staff notes | DENIED | DENIED | DENIED |
| **district_admin**| Scoped district | District cases | Full staff notes | Scoped district | Scoped district | Read-only |
| **auditor** | Scoped district | Read-only inbox| Read-only notes | Scoped district | Scoped district | Read-only |
| **super_admin** | National/All | All cases | Full staff notes | National / All | National / All | Full Admin |

---

## 3. Vulnerability Mitigation & Test Validation

### A. Insecure Direct Object References (IDOR)
- **Vulnerability**: Beneficiary A guessing or specifying Beneficiary B's case ID or profile ID in URL paths.
- **Defense**: All `/me/*` routes resolve beneficiary identity strictly from the authenticated JWT token subject. Attempting to access another beneficiary's case ID returns HTTP 404 (does not leak existence).
- **Test**: `test_idor_beneficiary_cannot_read_another_beneficiary_case` (Verified PASSED).

### B. Cross-District Data Access
- **Vulnerability**: District staff from District X attempting to query or modify cases or planning summaries in District Y.
- **Defense**: `user_scopes` database table binds staff to specific districts. SQL queries automatically inject `AND district_id IN (:user_scopes)` or raise HTTP 403 when out-of-scope parameters are supplied.
- **Test**: `test_cross_district_isolation_for_district_admin` (Verified PASSED).

### C. Privilege & Role Escalation
- **Vulnerability**: Field workers or beneficiaries attempting to trigger administrative endpoints like snapshot generation or catalogue modifications.
- **Defense**: Dependency injection checks role membership before entering route handlers.
- **Test**: `test_role_escalation_worker_cannot_create_planning_snapshot`, `test_role_escalation_beneficiary_cannot_access_staff_cases` (Verified PASSED).

### D. Token Security & Cryptographic Validation
- **Vulnerability**: JWT forgery, token tampering, replay attacks, or expired token usage.
- **Defense**:
  - Signatures validated with HS256 using cryptographically strong keys ($\ge 32$ chars).
  - Expired tokens immediately rejected (HTTP 401).
  - Malformed or garbage strings rejected (HTTP 401).
  - Refresh tokens rotated upon use; revoked tokens tracked in `refresh_tokens` table.
- **Tests**: `test_jwt_forged_signature_rejected`, `test_jwt_expired_token_rejected`, `test_jwt_garbage_token_rejected` (Verified PASSED).

### E. Injection & XSS Defense
- **Vulnerability**: SQL injection in query filters or stored XSS in opportunity descriptions/submissions.
- **Defense**:
  - 100% parameterized SQLAlchemy queries (zero raw SQL string concatenation).
  - Free-form text fields sanitized and rendered safely via React virtual DOM without `dangerouslySetInnerHTML`.
- **Tests**: `test_sql_injection_resilience_in_district_parameter`, `test_xss_payload_in_submission_stored_safely` (Verified PASSED).

---

## 4. Automated Security Test Results Summary

```
================================ test session starts =================================
backend/tests/test_security_validation.py .........                           [100%]
================================= 9 passed in 2.73s ==================================
```
- Total Security Tests Executed: 9
- Pass Rate: 100% (0 failures, 0 vulnerabilities detected)
