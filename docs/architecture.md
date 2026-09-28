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
