# JeevanMitra 2.0 Backend Core

**A Verification-First, Multi-Layer Generative AI System for PM-AJAY Livelihood Matching & District Planning**  
*Ministry of Social Justice & Empowerment (MoSJE) | Department of Social Justice & Empowerment | Grant-in-Aid (GIA) Component*  
*Problem Statement ID: 26097*

---

## 1. Executive Summary & Core Invariants

JeevanMitra 2.0 addresses the systemic failure modes of conventional voice chatbots in rural government skilling schemes:
1. **The Trust Problem:** Chatbots often recommend theoretical courses that lack open local batches or available seats, causing disillusioned beneficiaries to travel long distances for non-existent courses.
2. **The Planning Problem:** Grassroot beneficiary conversations remain locked in chat logs and are never channeled into district Annual Action Plans (AAPs).

### The Two Core Claims

* **Claim 1 — The Verified Match Protocol:**  
  Every recommendation enforces a strict state machine with only two visible states:
  * `Interest Match`: Qualification aligns with the beneficiary's aspirations and education according to official NQR standards, but local batch availability has **not** been verified by a field worker. Beneficiary sees: *"Qualification match — local batch not confirmed. No apply button."*
  * `Verified Match`: Qualification matches **AND** a human field worker has verified a live local batch, seat, or employer opening within the stated date window. *"Apply now" / "Request enrolment"* becomes active.
  * **Hard Data-Layer Guardrail:** No AI model or generative layer can upgrade an `Interest Match` to a `Verified Match`. That transition is strictly restricted to authenticated human field workers and immutably recorded in `audit_events`.

* **Claim 2 — The Planning Loop:**  
  Every beneficiary conversation is simultaneously an anonymized demand data point. Aggregated demand signals are compared against sanctioned seats per trade and block, producing plain-language, block-level supply-gap briefs for district planning officers before Annual Action Plan meetings. Numbers are strictly injected from database queries (no hallucinated figures).

---

## 2. Six Accountable Generative AI Layers

| Layer | Generative / Intelligence Task | Strict Guardrail / Failure Mode Mitigation |
| :--- | :--- | :--- |
| **Layer 1: Conversational Intake** | 8-question turn-by-turn spoken dialogue management in Hindi, Awadhi, Bhojpuri, English; empathetic re-prompting on unclear responses. | Intake **never** proposes qualifications, availability, or advice. It only collects and confirms. |
| **Layer 2: Structured Extraction** | Converts raw, code-mixed transcripts into a validated JSON profile (`education_level`, `interests`, `skills`, `mobility_radius_km`, `accessibility_needs`, `work_preference`). | Calculates per-field confidence (0.0 to 1.0). Any field with confidence `< 0.75` is flagged for mandatory read-back verification before matching runs. |
| **Layer 3: Grounded Matching (RAG)** | Deterministic hard filters (education rank, physical limits, travel radius) + 5-factor weighted scoring (30% interest, 20% prior skills, 20% access, 20% demand, 10% preference) against verified NQR catalog. | Closed document set RAG. The system cannot invent courses, centres, salaries, or jobs. Assigns initial `Interest Match` vs `Verified Match` state based on live batch records. |
| **Layer 4: Field-Worker Co-Pilot** | Drafts a 3-line case summary for VLEs/CSC operators, flags low-confidence discrepancy fields, drafts SMS/WhatsApp confirmation after referral. | All profile corrections and referral approvals require an explicit human worker action. |
| **Layer 5: Planning Narrative Layer** | Aggregates demand vs capacity into a written supply-gap brief for District Collectors and Annual Action Plans. | **Strict numeric grounding:** The model writes prose, but every cited number is directly inserted from database query aggregations. |
| **Layer 6: Outcome & Drift Monitoring** | Audits recommendation logs for demographic skew (e.g. gender stereotyping in technical trades vs apparel) and unconfirmed batch spikes. | Output is advisory-only, routed to a human administrator's review queue. |

---

## 3. Database Architecture (11 Core Tables)

The database runs on SQLite with Write-Ahead Logging (WAL) and foreign keys enabled out-of-the-box (zero cloud friction), with schemas 100% compatible with PostgreSQL/Supabase:

1. `beneficiaries`: Identity, demographic details, language preference, district, block, contact preference.
2. `consents`: DPDP Act compliant affirmative consent, notice versioning, voice retention choice (`do_not_keep` vs `keep_for_quality`).
3. `interview_sessions`: Stateful multi-turn interview sessions, channel (`web_app`, `kiosk`, `whatsapp`, `ivr`), transcript history.
4. `profile_answers`: Extracted entity fields, confidence scores, confirmation status, and update audit trail.
5. `qualifications`: Closed NQR catalog (NQR code, NSQF level, duration, minimum education rank, work type, physical intensity, skills).
6. `local_opportunities`: Dated local training batches, centres (RSETI, PMKK, ITI), lat/long coordinates, total & SC-reserved seats, status, amenities (free toolkit, stipend, hostel).
7. `recommendations`: Ranked pathways (top 3), explainable score breakdowns, `Interest Match` / `Verified Match` state, grounded explanations, frozen data snapshots.
8. `referrals`: Field worker case allocations, status lifecycle (`pending` -> `counselor_contacted` -> `enrolled`), document verification checks (caste, income, residence).
9. `outcomes`: Post-skilling outcome tracking (enrolled, completed, wage employed, self-employed, monthly income, toolkit distribution).
10. `planning_briefs`: District supply-gap reports, demand vs capacity snapshots, policy recommendations, and officer sign-offs.
11. `audit_events`: Immutable audit ledger recording actor, role, action, old/new states, and timestamps.
12. `drift_advisories`: Human reviewer queue for bias alerts and unconfirmed batch spikes.

---

## 4. API Endpoints Reference

### Health & System Status
* `GET /api/health` — Returns system status, DB health, active district, and status of all 6 AI layers.

### Beneficiaries & DPDP Consent
* `POST /api/beneficiaries` — Registers or updates a beneficiary record.
* `GET /api/beneficiaries` — Lists beneficiaries filtered by district or block.
* `GET /api/beneficiaries/:id` — Gets beneficiary profile and consent history.
* `POST /api/consents` — Records affirmative audio or digital consent under DPDP Act principles.
* `GET /api/consents/beneficiary/:beneficiaryId` — Gets consent records.

### Conversational Intake & Extraction (Layers 1 & 2)
* `POST /api/interview/start` — Initializes a new 8-question interview session; returns the first question with synthesized audio.
* `POST /api/interview/turn` — Submits a user voice/text answer; processes transcription, evaluates clarification need, and returns the next question.
* `GET /api/interview/extract/:sessionId` — Runs Layer 2 extraction; returns validated JSON profile with per-field confidence scores and read-back script.
* `POST /api/interview/confirm` — Records beneficiary confirmation of their profile facts and saves into `profile_answers`.
* `GET /api/interview/session/:id` — Retrieves session transcript history and extracted answers.

### Grounded Recommendations & RAG (Layer 3)
* `POST /api/recommendations/match` — Executes Layer 3 grounded matching; applies hard filters, calculates 5-factor weighted scores, sets `Interest Match` or `Verified Match`, and generates plain-language explanations.
* `GET /api/recommendations/beneficiary/:beneficiaryId` — Returns top 3 ranked recommendations.
* `GET /api/recommendations/:id/details` — Detailed recommendation breakdown with frozen data snapshot.
* `GET /api/recommendations/:id/opportunity` — Returns verified training centre logistics, transit time, and amenities (Screen 8).
* `GET /api/recommendations/compare/:id1/:id2` — Returns side-by-side pathway comparison matrix (Screen 7).

### Field Worker Co-Pilot & Operations (Layer 4)
* `GET /api/worker/cases` — Lists cases awaiting review with count badges (Screen 6).
* `GET /api/worker/cases/:id` — Returns 3-line case summary, low-confidence discrepancy flags, transcript, and current recommendations (Screen 11).
* `PATCH /api/worker/cases/:id/profile` — Field worker corrects misheard facts; immediately re-runs grounded matching with updated facts.
* `POST /api/worker/cases/:id/verify-batch` — **Claim 1 Invariant:** Field worker verifies live batch/seats, upgrading `Interest Match` to `Verified Match` and logging an immutable audit event.
* `POST /api/worker/cases/:id/referral` — Verifies eligibility documents (SC certificate, residence proof, income) and submits referral to training partner roster.

### Referrals & Progress Tracker
* `GET /api/referrals` — Lists referrals filtered by status, worker, or beneficiary.
* `PATCH /api/referrals/:id` — Updates referral status and milestone stages.
* `POST /api/referrals/outcomes` — Records post-skilling outcome (wage/self-employed, toolkit received, monthly income).
* `GET /api/referrals/progress/:beneficiaryId` — Returns 5-step milestone progress tracker for candidate (Screen 9).

### District Perspective Planning Loop (Layer 5)
* `GET /api/planning/supply-gap-matrix?district=Moradabad` — Real-time trade demand vs sanctioned seats matrix with deficit alerts (Screen 12).
* `POST /api/planning/generate-brief` — Runs Layer 5 strictly grounded narrative brief generator.
* `GET /api/planning/briefs` — Lists past planning briefs.
* `GET /api/planning/briefs/:id` — Retrieves planning brief details.
* `POST /api/planning/briefs/:id/sign-off` — District Officer reviews and signs off on brief for AAP submission.
* `GET /api/planning/export?district=Moradabad&format=csv` — Exports perspective plan as CSV or JSON.

### Outcome & Drift Governance (Layer 6)
* `POST /api/monitoring/audit-drift` — Executes automated drift detection scan across district records.
* `GET /api/monitoring/advisories` — Retrieves open advisories in the human reviewer queue.
* `PATCH /api/monitoring/advisories/:id` — Acknowledges or marks advisory as resolved.

### Multi-Channel Simulation Adapters
* `POST /api/channels/whatsapp/simulate` — Simulates WhatsApp incoming voice notes in regional dialects (Awadhi, Bhojpuri, Hindi); replies with spoken voice note, action pills, and PDF card (Screen 10).
* `POST /api/channels/ivr/simulate` — Simulates IVR telephony call flow with voice prompts and DTMF keypad input fallback.

### Public Catalogue & Governance Ledger
* `GET /api/catalogue/qualifications` — Browses verified NQR qualifications.
* `GET /api/catalogue/qualifications/:id` — Detailed qualification view with active batches.
* `GET /api/catalogue/opportunities` — Lists verified local centres and batches.
* `GET /api/audit-events` — Immutable audit log of all system transitions and human worker verifications.

---

## 5. Development & Testing Commands

### Prerequisites
* Python 3.10+ (tested on Python 3.11.9)

### Quick Start
```bash
# Create and activate virtual environment
python -m venv .venv
# On Windows: .venv\Scripts\activate
# On macOS/Linux: source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start server
python run.py
# Server starts on http://localhost:4000
```

### Running Test Suite
```bash
pytest tests/
```
### Plan A — Trust, Consent, and Recommendation Capabilities (`/api/v1/` & `/api/`)

#### 1. Versioned Consent Enforcement (A1)
* `POST /api/v1/consents` — Records versioned consent records under DPDP Act requirements (`ai_processing`, `profile_storage`, `counselor_referral`, `analytics`, `export_summary`).
* `GET /api/v1/consents/{session_or_beneficiary_id}` — Lists all granted and revoked consents for an anonymous session or beneficiary.
* `POST /api/v1/consents/{consent_id}/revoke` — Revokes consent, stopping protected operations immediately. Revocation triggers post-revocation cascade:
  - `ai_processing`: future user messages fallback to guided questions.
  - `profile_storage`: saved beneficiary details anonymized/deleted.
  - `counselor_referral`: active open referral cases are paused/closed.

#### 2. Anonymous Sessions & Beneficiary Lifecycle (A2)
* `POST /api/v1/sessions` — Generates a signed, short-lived anonymous session token (24h TTL) allowing guest users to complete an interview and get recommendations without creating an account.
* `GET /api/v1/beneficiaries/me` — Fetches current caller profile (works for anonymous session or authenticated beneficiary).
* `PATCH /api/v1/beneficiaries/me` — Updates profile fields for the active caller.
* `DELETE /api/v1/beneficiaries/me` — **DPDP Right to Erasure:** Permanently purges all interview turns, extracted profile fields, recommendations, referrals, and consents, logging only a minimal non-identifying audit event.
* `POST /api/v1/beneficiaries/me/export-summary` — Generates a clean, privacy-safe printable summary.

#### 3. Interview State Machine & Provenance Engine (A3)
* **Lifecycle States:** `not_started` ➔ `collecting` ➔ `awaiting_confirmation` ➔ `ready_for_matching` ➔ `recommendations_generated` ➔ `referred` ➔ `completed`.
* **Field Provenance:** Every collected field stores `value`, `source` (`user`, `ai_inferred`, `counselor`, `system`), `confidence`, `user_confirmed` boolean, and version history.
* **Confirmation Rule:** Deterministic matching will **only** execute hard constraints against `user_confirmed` fields.
* `POST /api/v1/interviews/start` — Starts stateful interview under active session.
* `POST /api/v1/interviews/{interview_id}/turns` — Submits interview turns with multi-field extraction and low-confidence clarification detection.
* `GET /api/v1/interviews/{interview_id}` — Returns transcript history, turns, and field provenance state.
* `POST /api/v1/interviews/{interview_id}/confirm-profile` — Locks confirmed profile values and transitions state to `ready_for_matching`.
* `PATCH /api/v1/interviews/{interview_id}/fields/{field_name}` — Allows individual field corrections with version tracking.
* `POST /api/v1/interviews/{interview_id}/complete` — Marks interview completed.
* `POST /api/v1/interviews/{interview_id}/summary` — Exports printable summary.

#### 4. Verified Catalog & Opportunity Separation (A4)
* **Separation of Concerns:** Official NQR Qualifications (curriculum, NSQF level, eligibility) are separated from Local Opportunities (active batches, centres, seats, dates).
* **Stale-Data Rule:** If an opportunity's `last_verified_at` exceeds 90 days, its availability is automatically reported as `unknown` or `expired`.
* `GET /api/v1/catalogue/qualifications` — Public verified qualification pathways.
* `GET /api/v1/catalogue/qualifications/{qualification_id}` — Detail view with active verified batches.
* `GET /api/v1/catalogue/opportunities?district=...` — Lists verified local opportunities.
* `POST /api/v1/admin/catalogue/qualifications` — Admin endpoint to register official NQR qualifications.
* `PATCH /api/v1/admin/catalogue/qualifications/{id}` — Admin update of qualification metadata.
* `POST /api/v1/admin/catalogue/opportunities` — Admin/Worker registration of local batches.
* `PATCH /api/v1/admin/catalogue/opportunities/{id}` — Admin/Worker batch update.
* `POST /api/v1/admin/catalogue/opportunities/{id}/archive` — Archives an opportunity rather than deleting it.

#### 5. Deterministic Recommendations & Explainability (A5)
* **Matching Pipeline:** `Confirmed Profile` ➔ `Hard Constraints Filter` ➔ `5-Factor Weighted Score` ➔ `Local Opportunity Enrichment` ➔ `Explanation Generator`.
* **Zero Hallucination Guarantee:** If no verified local batch exists, the qualification pathway is returned with `local_availability.status = "unknown"`, an admission caveat, and a counselor referral recommendation.
* `POST /api/v1/recommendations/generate` — Computes deterministic recommendations based on confirmed profile.
* `GET /api/v1/recommendations/{recommendation_id}` — Retrieves recommendation record with audit snapshot.
* `GET /api/v1/interviews/{interview_id}/recommendations` — Lists recommendations for an interview.

#### 6. Counselor Referral & Human Handoff Workflow (A7)
* **Referral Lifecycle:** `new` ➔ `assigned` ➔ `contacted` ➔ `in_progress` ➔ `resolved` ➔ `closed`.
* `POST /api/v1/referrals` — Submits referral case (requires `counselor_referral` consent).
* `GET /api/v1/referrals/me` — Beneficiary view of active referral cases.
* `GET /api/v1/counselor/referrals` — Counselor queue (restricted to counselors and administrators).
* `PATCH /api/v1/counselor/referrals/{id}/assign` — Assigns counselor to case.
* `PATCH /api/v1/counselor/referrals/{id}/status` — Counselor updates case status.
* `POST /api/v1/counselor/referrals/{id}/notes` — Adds case progression notes.

---

## 5. Automated Test Suite

Run the full automated test suite using `pytest`:
```bash
cd backend
python -m pytest tests/ -v
```

The test suite covers:
* `test_consents.py`: Versioned consent enforcement, missing consent denial, revocation cascade, and counselor referral consent.
* `test_interviews.py`: Anonymous session start, multi-turn interview, field extraction, unconfirmed vs user-confirmed state, and profile editing.
* `test_catalogue.py`: Qualification and opportunity separation, entry validation, 90-day staleness rule, and archiving.
* `test_recommendations.py`: Hard constraint filtering (education rank, wheelchair/accessibility, wage preference), no-hallucination guarantees, and no-result counselor handoff.
* `test_referrals.py`: Human handoff workflow, role-based authorization, assignment, status transitions, and notes.
* `test_profile_deletion.py`: DPDP full profile erasure, cascading purges, and immutable non-identifying audit event recording.
* `test_ai_fallback.py`: Safe AI extraction validation, bounds checking, and guided fallback mode when AI is unavailable.
* `test_api_integration.py`: End-to-end integration across all routers and state invariants.

---

## 6. Docker & Microsoft Azure Deployment

### Local Docker Run
```bash
# Build the production multi-stage image
docker build -t jeevanmitra-backend .

# Run with persistent volume for SQLite database
docker run -d -p 4000:4000 -v ./data:/app/data --name jeevanmitra-backend jeevanmitra-backend

# Or with Docker Compose
docker-compose up -d --build
```

### Deploying to Microsoft Azure
You can deploy directly to Azure Container Apps or Azure App Service without needing Docker installed locally, using Azure Container Registry (ACR) Cloud Build:

* **Windows PowerShell Automated Deployment**:
  ```powershell
  .\azure-deploy.ps1 -ResourceGroup "rg-jeevanmitra" -Location "centralindia"
  ```
* **Linux / macOS / Azure Cloud Shell (Bash)**:
  ```bash
  chmod +x azure-deploy.sh
  ./azure-deploy.sh
  ```
* **CI/CD via GitHub Actions**: Automated deployment on push to `main` via [.github/workflows/azure-deploy.yml](../.github/workflows/azure-deploy.yml).

For comprehensive Azure architecture, Azure Files persistent volume mounts, and custom domain configuration, read [AZURE_DEPLOYMENT.md](AZURE_DEPLOYMENT.md).

---

## 7. Python FastAPI Backend Quickstart

The backend has been converted to Python using **FastAPI**, **Pydantic v2**, and **Uvicorn**, providing high performance, automatic OpenAPI documentation, and native AI integration.

### Prerequisites
- Python 3.10+ (tested on Python 3.11.9)

### 1. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment
A `.env` file in `backend/` or project root is read automatically:
```env
PORT=4000
HOST=0.0.0.0
DEFAULT_DISTRICT=Moradabad
DEFAULT_STATE=Uttar Pradesh
AI_PROVIDER=mock
WORKER_API_KEY=replace-with-a-long-random-value
WORKER_ID=local-worker-01
WORKER_NAME=Local Field Worker
```

Worker routes require the `X-Worker-API-Key` header and a configured worker identity; they fail closed when these settings are missing. Use a unique secret outside local development. This shared-key setup is for the prototype and is not a replacement for production user accounts and role-based authorization.

### 3. Run the Server
```bash
python run.py
```
Or directly using Uvicorn:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 4000 --reload
```

### 4. Interactive Documentation
- **Swagger UI:** [http://localhost:4000/docs](http://localhost:4000/docs)
- **ReDoc:** [http://localhost:4000/redoc](http://localhost:4000/redoc)
- **Health Check:** [http://localhost:4000/api/health](http://localhost:4000/api/health)

# Setup

## Related Documentation
- [Frontend API Handoff Document](docs/FRONTEND_API_HANDOFF.md)
- [Backend Release Checklist](docs/BACKEND_RELEASE_CHECKLIST.md)
- [API Changelog](docs/API_CHANGELOG.md)

### Installation and Execution
```bash
cd backend
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
# source .venv/bin/activate
pip install -r requirements.txt
python run.py
```
