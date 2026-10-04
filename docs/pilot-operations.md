# JeevanMitra 2.0 Pilot Operating Model & Field Guide

## 1. Pilot Context & Scope

- **Target Pilot District**: Moradabad, Uttar Pradesh
- **Key Blocks**: Chhajlet, Kundarki, Bilari, Dilari, Bhagatpur Tanda
- **Pilot Beneficiaries**: 500+ targeted rural/semi-urban beneficiaries under MoSJE PM-AJAY GIA guidelines
- **Focus Sectors**: Solar PV Installation, Electrician / Electronics Repair, Handicrafts & Textiles, Automotive Service

---

## 2. Operational Ownership & Responsibilities

| Role | Primary Responsibility | Scoping Boundary |
| :--- | :--- | :--- |
| **Pilot Administrator** | Programme rollout, user onboarding, approvals, operational sign-off | State / Programme Level |
| **District Administrator** | Planning snapshots, district review, controlled exports, resource allocation | Assigned District |
| **Field Worker** | Opportunity verification, referrals, follow-ups, verified outcomes | Assigned District & Blocks |
| **Catalogue Manager** | Qualification/course mappings, NSQF alignment, and catalogue hygiene | Global Catalogue |
| **Auditor** | Read-only verification, referral, and export history review | Assigned District / State |
| **Technical Support Owner** | Incidents, deployment, background job monitoring, disaster recovery | Core Platform Infrastructure |
| **Data-Protection Owner** | Consent notices, retention schedules, DPDP-aligned correction/deletion workflows | Regulatory & Privacy Governance |

```
┌─────────────────────────────────────────────────────────────┐
│                 District Planning & Review                  │
│                (District Admin & Auditors)                  │
│   • Monitor weekly demand vs verified capacity gaps         │
│   • Freeze quarterly immutable planning snapshots           │
│   • Generate audit-logged CSV/PDF planning reports          │
└──────────────────────────────┬──────────────────────────────┘
                               │ Assigns & Oversees
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                 Field Casework & Counseling                 │
│                 (Field Workers & Counselors)                │
│   • Multimodal beneficiary intake (Bilingual Hi/En)         │
│   • Explainable recommendation delivery (Evidence-backed)   │
│   • Opportunity submission verification (Voice & Text)      │
│   • Active referral follow-up (Contact -> Enrol -> Outcome) │
└──────────────────────────────┬──────────────────────────────┘
                               │ Serves
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                 Beneficiaries & Citizens                    │
│   • Self-guided career discovery & voice assistant          │
│   • Local verified opportunity discovery                    │
│   • Transparent referral status & training tracking         │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Daily Field Worker Workflow

### Step 1: Morning Inbox Review
1. Log in to `https://jeevanmitra.gov.in/field-worker`.
2. Inspect the **Assigned Cases** inbox. Filter by priority:
   - `HIGH`: Beneficiaries with urgent livelihood needs or stalled referrals.
   - `NORMAL`: Standard ongoing counseling cases.
3. Review any newly submitted community opportunities under `/api/v1/opportunity-submissions`.

### Step 2: Beneficiary Intake & Counseling
1. Conduct guided intake session in preferred language (Hindi or English).
2. Record confirmed facts: Education (10th/12th), experience, location preferences, stipend needs.
3. Trigger grounded matching. Review generated recommendations:
   - Verify `match_state` (`VERIFIED_MATCH` vs `INTEREST_MATCH`).
   - Check evidence-backed explanation reasons.
   - Confirm local batch availability in Moradabad.

### Step 3: Referral Initiation & Tracking
1. Initiate referral to an active verified local opportunity.
2. Record contact attempt within 48 hours:
   - Call beneficiary and training centre contact.
   - Log outcome in casework diary notes (`CONTACTED` or `BENEFICIARY_ACCEPTED`).
3. Follow up weekly until training enrolment is confirmed.

### Step 4: Outcome Verification
1. Once training or employment is completed, upload verification document (completion certificate or employer offer letter).
2. Submit for outcome verification. (Separates self-reported claims from verified livelihoods).

---

## 4. Multimodal Opportunity Submission Verification

Community members, employers, or field workers can submit training leads via typed text or voice recordings.

```
[ Beneficiary / Citizen Submission ]
   ├── Voice Recording (WAV/MP3)
   └── Typed Text
         │
         ▼
[ Ingestion Pipeline: POST /api/v1/opportunity-submissions ]
   ├── Stored with status: SUBMITTED
   └── Never appears as active opportunity automatically
         │
         ▼
[ Field Worker / Admin Review ]
   ├── Verify training provider registration
   ├── Validate physical centre address in Moradabad
   ├── Confirm batch start date, seats, and stipend details
   └── Approve (creates verified local opportunity) or Reject
```

---

## 5. Escalation Protocols & Rules

Operational issues follow a strict 5-stage escalation chain:

```
[ 1. Beneficiary Support Request ]
     │
     ▼
[ 2. Field-Worker Assignment & Direct Follow-up ]
     │ (Unresolved > 48h or provider mismatch)
     ▼
[ 3. District Escalation (District Admin / Lead Counselor) ]
     │ (System errors, data discrepancies, or batch shortfalls)
     ▼
[ 4. Technical Incident (Technical Support Owner & On-Call) ]
     │ (Data corruption, scope breaches, or PII leak risk)
     ▼
[ 5. Privacy / Security Incident (Data-Protection Owner & Legal) ]
```

| Escalation Trigger | Lead Responder | Hand-off Criteria | Escalation Target |
| :--- | :--- | :--- | :--- |
| **Beneficiary Support Request** | Field Worker | Unassigned case, missing local opportunities, transport issues | Lead Field Worker |
| **Field-Worker Assignment** | Lead Field Worker | Stalled referrals (>7 days), lack of batch capacity, candidate withdrawal | District Admin |
| **District Escalation** | District Admin | System errors, data anomalies, export failures, API degradation | Technical Support Owner |
| **Technical Incident** | Tech Support Owner | Unscheduled downtime, database lock, authentication spike, failed migrations | Incident Commander |
| **Privacy / Security Incident** | Data-Protection Owner | Cross-district access breach, unauthorized data exposure, consent disputes | State Steering Committee |

---

## 6. Recommended Pilot Order & Phased Rollout Constraints

To ensure patient, evidence-backed scaling, rollout must strictly follow four gated stages:

```
Stage 1: Internal Staff-Only Staging Rehearsal
   │ • Verify all staff roles, permissions, scopes, and verification flows.
   │ • Validate disaster recovery drill and automated backup restorations.
   ▼
Stage 2: Single District with Synthetic / Demo Beneficiaries (Moradabad)
   │ • Validate bilingual intake, matching explanations, and referral transitions.
   │ • Confirm minimum cell-size privacy threshold (k = 5) on real reports.
   ▼
Stage 3: Small Supervised Field Pilot (50–100 Live Beneficiaries)
   │ • Supervised by authorized field workers across 2 selected blocks.
   │ • Direct human-assisted verification of opportunities and referral tracking.
   ▼
Stage 4: Expand Language & Channel Coverage Based on Observed Gaps
   │ • Add languages or channels only after observed demand and operational readiness.
```

> [!IMPORTANT]
> **Strict Channel Expansion Boundary**: Do not enable additional languages, WhatsApp channels, IVR integration, or automated provider integrations merely because the architecture supports them. Each must be treated as a separately tested channel release with its own consent notice, identity verification, error-handling protocols, and operational-support model.
