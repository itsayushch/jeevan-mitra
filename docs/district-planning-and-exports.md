# PM-AJAY District Planning, Aggregations, and Controlled Exports

## 1. Overview & Core Planning Invariants

JeevanMitra 2.0 provides district administrators, state planners, and auditors with evidence-based decision support for the Pradhan Mantri Anusuchit Jaati Abhyuday Yojana (PM-AJAY).

### Foundational Invariants:
1. **Authoritative Grounding Only**: Planning indicators are aggregated strictly from verified database records (confirmed profile answers, active and non-expired local opportunities, affirmative consents, and verified referral outcomes). No speculative numbers or unconfirmed claims are included.
2. **Strict Privacy Safeguards (DPDP Act Alignment)**:
   - Planning dashboards apply a minimum cell-size privacy threshold of k = 5. Any grouped metric involving fewer than five unique beneficiaries is suppressed and returned as null with is_suppressed = true. (Note: A minimum cell-size suppression rule is a valuable privacy control, but does not by itself constitute formal k-anonymity or legal compliance).
   - Exports contain **zero** beneficiary names, phone numbers, contact details, caseworker diary notes, or evidence file references.
   - All exports and reports display mandatory privacy and disclaimer statements.
3. **Prevention of Metric Conflation**:
   - **Expressed Demand vs Verified Supply**: Demand reflects beneficiary profile confirmations; supply reflects only currently active, unexpired, non-archived capacity in approved local batches.
   - **Funnel Integrity**: Verified match $\neq$ Referral $\neq$ Enrolment $\neq$ Completion $\neq$ Verified Outcome.
   - **Reported vs Verified Outcomes**: Self-reported claims and verified wage/self-employment outcomes are maintained as separate metrics.
4. **Immutable Snapshots for Reproducibility**:
   - Annual Action Plan (AAP) submissions and committee presentations reference immutable snapshots. Once generated, snapshot data cannot be modified.
   - Controlled exports (CSV and PDF) are generated exclusively from immutable snapshots, never from live mutating operational state.

---

## 2. API Endpoints

All planning routes require authentication (`Bearer` token) and staff authorization (`district_admin`, `auditor`, or `super_admin`).

### Aggregations
| Endpoint | Method | Role Required | Scope Check | Description |
|---|---|---|---|---|
| `/api/v1/planning/overview` | `GET` | District Staff | Yes | Executive narrative brief, totals, and freshness timestamp |
| `/api/v1/planning/demand` | `GET` | District Staff | Yes | Demand broken down by qualification and NSQF level |
| `/api/v1/planning/supply` | `GET` | District Staff | Yes | Active verified capacity, providers, enrolled seats, upcoming expiries |
| `/api/v1/planning/gaps` | `GET` | District Staff | Yes | Demand vs supply gap status (`CAPACITY_SURPLUS`, `BALANCED`, `DEFICIT`, `NO_VERIFIED_SUPPLY`) |
| `/api/v1/planning/referral-funnel` | `GET` | District Staff | Yes | Stage-by-stage funnel counts and conversion rates |
| `/api/v1/planning/outcomes` | `GET` | District Staff | Yes | Verified vs reported training completion and livelihood placements |
| `/api/v1/planning/data-quality` | `GET` | District Staff | Yes | Catalog hygiene, overdue follow-ups, language distribution, multimodal submissions, and explainability quality |
| `/api/v1/planning/geographic-coverage` | `GET` | District Staff | Yes | Block-level capacity coverage and supply status |

### Immutable Snapshots & Controlled Exports
| Endpoint | Method | Role Required | Description |
|---|---|---|---|
| `/api/v1/planning/snapshots` | `POST` | `district_admin`, `super_admin` | Freezes current aggregations into an immutable snapshot |
| `/api/v1/planning/snapshots` | `GET` | District Staff | Lists historical snapshots for the district |
| `/api/v1/planning/snapshots/{id}` | `GET` | District Staff | Retrieves full snapshot aggregation payload |
| `/api/v1/planning/snapshots/{id}/review` | `POST` | District Staff | Transitions snapshot to `REVIEWED` status |
| `/api/v1/planning/snapshots/{id}/approve` | `POST` | District Staff | Transitions snapshot to `APPROVED` status |
| `/api/v1/planning/snapshots/{id}/exports/csv` | `POST` | District Staff | Generates reproducible CSV export with SHA-256 checksum |
| `/api/v1/planning/snapshots/{id}/exports/pdf` | `POST` | District Staff | Generates reproducible text-formatted PDF export |
| `/api/v1/planning/exports/{id}` | `GET` | District Staff | Checks export metadata, checksum, and download count |
| `/api/v1/planning/exports/{id}/download` | `GET` | District Staff | Downloads file; re-verifies district scope; logs audit event |

---

## 3. Data Quality, Accessibility & Explainability Dimensions

Sprint 6 extends planning telemetry with three key operational and accessibility dimensions:

1. **Multilingual Distribution**:
   - Tracks beneficiary preferred languages (`en`, `hi`, etc.) to inform local language skilling mobilization.
   - Strictly applies $k$-threshold suppression if any language cohort in the district has $< 5$ beneficiaries.
2. **Multimodal Opportunity Intake**:
   - Aggregates submissions received via typed web forms versus field voice submissions.
   - Monitors review throughput (`SUBMITTED`, `REVIEWED`, `LINKED`, `REJECTED`) without exposing raw submission texts or transcripts.
3. **Recommendation Explainability Quality**:
   - Quantifies the proportion of recommendations backed by confirmed facts (`explanation_facts`).
   - Tracks renderer breakdown (`template` vs `llm` / `llm_grounded`).
   - Strictly excludes beneficiary-specific raw explanation text from planning aggregates.

---

## 4. Security & Audit Logging

Every sensitive planning action generates tamper-evident audit records:
- `PLANNING_SNAPSHOT_GENERATED`: Logs creator ID, district, period, and snapshot ID.
- `PLANNING_SNAPSHOT_REVIEWED`: Logs reviewer ID and review notes.
- `PLANNING_SNAPSHOT_APPROVED`: Logs approver ID and approval notes.
- `PLANNING_EXPORT_GENERATED`: Logs export type (`CSV` or `PDF`), snapshot ID, and SHA-256 checksum.
- `PLANNING_EXPORT_DOWNLOADED`: Logs downloader ID, timestamp, and increments download counter.
- `SECURITY_ACCESS_DENIED`: Logs isolated audit events for unauthorized roles or cross-district access attempts.

---

## 5. Maintenance Scripts

The backend includes standalone CLI utilities for cron jobs and operational maintenance:

1. **Data Quality Check**:
   ```bash
   python scripts/check_planning_data_quality.py --district-id Moradabad
   ```
2. **Automated Snapshot Generation**:
   ```bash
   python scripts/generate_planning_snapshot.py --district-id Moradabad --period-start 2026-01-01 --period-end 2026-12-31
   ```
3. **Export Retention & Cleanup**:
   ```bash
   python scripts/expire_planning_exports.py --dry-run
   python scripts/expire_planning_exports.py
   ```
