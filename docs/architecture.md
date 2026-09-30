# JeevanMitra 2.0 Target Architecture

## 1. Overview
JeevanMitra is transitioning to a **Modular Monolith**. We will avoid microservices until traffic or complexity necessitates them.

## 2. Technology Stack
- **Frontend**: PWA using React, Vite, Tailwind CSS, TanStack Query, and React Router.
- **Backend**: Node.js + TypeScript, Express.
- **Database**: PostgreSQL (migrating from SQLite).
- **ORM**: Prisma or Drizzle ORM.
- **Authentication**: Supabase Auth, Auth0, Clerk, or custom JWT/OIDC provider.
- **Storage**: Supabase Storage, Azure Blob Storage, or S3-compatible private storage for audio.
- **Background Jobs**: BullMQ + Redis for processing queues (e.g., audio, reports).
- **AI Gateway**: Backend-only adapter service for centralizing prompts, security, and rate limiting.

## 3. Architecture Boundary
- **Client layer**: Beneficiary PWA, Kiosk, WhatsApp, IVR can ONLY talk to the backend API Gateway.
- **Backend Gateway**: Consolidates authentication, authorization, rate limiting.
- **Application Modules**: Interview Engine, Matching Engine, Worker Workflow.
- **Data Layer**: PostgreSQL containing entities (beneficiaries, catalogue, referrals, audit).
- **External Dependencies**: AI providers, Job queue, Storage.

## 4. API Separation & AI Security
- No frontend directly calls the LLM, transcription, database, or storage.
- All AI extraction, text-to-speech, speech-to-text, matching is server-side.
- AI must NOT directly update system state (e.g., no auto-enrollment).

## 5. District Planning, Aggregations & Controlled Exports Architecture (Sprint 6)
- **Authoritative Aggregation Engine (`PlanningAggregationService`)**:
  - Consumes authoritative operational records directly from Sprint 4 (`local_opportunities`, `qualifications`, `opportunity_providers`) and Sprint 5 (`beneficiary_cases`, `referrals`, `referral_outcomes`).
  - Strict domain boundaries: Unverified or expired opportunities are excluded from verified capacity; full opportunities count as full rather than available capacity; reported outcomes are never conflated with verified livelihoods.
  - $k$-Anonymity Suppression ($k=5$): Groups with fewer than 5 unique beneficiaries are masked (`is_suppressed=True`), designed to support DPDP-aligned practices.
- **Immutable Snapshot Pipeline (`PlanningSnapshotService`)**:
  - Captures complete frozen district planning aggregations into `planning_snapshots` with JSON payloads and normalized dimensional metric records in `planning_snapshot_metrics`.
  - Immutable lifecycle: `GENERATED` -> `REVIEWED` -> `APPROVED`.
- **Controlled Export Subsystem (`PlanningExportService`)**:
  - Exports (CSV and PDF) are generated exclusively from immutable snapshots, ensuring deterministic reproducibility.
  - Generates SHA-256 cryptographic checksums for tamper detection.
  - **Re-authorization at Download**: Geographic authorization is re-verified at download time. Expired exports return HTTP 410 Gone.
  - Complete omission of beneficiary PII, casework notes, or provider private contacts.
