# JeevanMitra 2.0 Pilot Operating Model & Field Guide

## 1. Pilot Context & Scope

- **Target Pilot District**: Moradabad, Uttar Pradesh
- **Key Blocks**: Chhajlet, Kundarki, Bilari, Dilari, Bhagatpur Tanda
- **Pilot Beneficiaries**: 500+ targeted rural/semi-urban beneficiaries under MoSJE PM-AJAY GIA guidelines
- **Focus Sectors**: Solar PV Installation, Electrician / Electronics Repair, Handicrafts & Textiles, Automotive Service

---

## 2. Operating Roles & Responsibilities

```
┌─────────────────────────────────────────────────────────────┐
│                 District Planning & Review                  │
│                (District Admin & Auditors)                  │
│   • Monitor weekly demand vs verified capacity gaps         │
│   • Freeze monthly immutable planning snapshots             │
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

## 5. Escalation & Support SLAs

| Event Type | Priority | Escalation Path | Resolution SLA |
| :--- | :--- | :--- | :--- |
| **System Down / Login Failure** | Sev 1 | Tech On-Call Engineer | $< 30$ minutes |
| **Suspected Fraudulent Training Provider** | Sev 2 | District Admin | $< 24$ hours |
| **Beneficiary Referral Stalled (> 7 days)**| Sev 3 | Lead Field Counselor | $< 48$ hours |
| **Translation / Voice Clarification** | Sev 4 | District Language Focal | $< 3$ business days |
