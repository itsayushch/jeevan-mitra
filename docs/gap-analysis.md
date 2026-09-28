# Gap Analysis: JeevanMitra 2.0

## 1. Existing Implementation
- **Frontend**: Scaffolding with React, Vite, and Tailwind CSS. Basic file structure exists, but broken/incomplete frontend connections to the backend.
- **Backend**: Node.js + TypeScript application with Express.
- **Database**: Currently using in-memory/file-based SQLite (`better-sqlite3`).
- **Endpoints**: Controllers and routes exist for beneficiaries, consent, interview, recommendations, referrals, worker, planning, monitoring, channels, audit, catalogue.
- **AI Layers**: Six layers structure exists but lacks robust provider adapters.
- **Testing**: Vitest suite with passing basic integration tests.
- **Deployment**: Dockerfile and Docker Compose exist. Basic Azure deployment scripts provided.

## 2. Required Production Behavior
- **Database**: PostgreSQL with connection pooling, migrations, and row-level security.
- **Security**: Strict authentication (OTP/Password), Role-Based Access Control (RBAC), API rate limiting, and request validation on all routes.
- **Verification Guarantee**: "Verified Match" state must be strictly enforced via backend logic and database constraints. No frontend or AI can bypass this.
- **Privacy/Consent**: Explicit consent required before data collection. Audit trails for all privileged actions.
- **AI Guardrails**: AI must be deterministic for ranking, grounded, schema-constrained, and not allowed to independently take action.

## 3. Missing Work
- **Database**: Migration from SQLite to PostgreSQL. Definition of Prisma or Drizzle ORM schema.
- **Security**: Implementation of Auth middleware, Zod/Joi request validation on routes, rate limiting, and CORS configuration.
- **Feature Completeness**: 
  - Complete integration of frontend and backend.
  - Development of robust Speech-to-Text (STT) and Text-to-Speech (TTS) adapters.
  - CSV/Excel import for NQR/NSQF sample data.
- **Observability**: Structured logging, error boundaries, and OpenTelemetry-compatible tracing.
- **Environment Management**: Separation of local, staging, and production environments.

## 4. Priority
1. **P0**: PostgreSQL setup, Auth, RBAC, Validation, Beneficiary intake flow, Local opportunity verification, Match-state enforcement.
2. **P1**: Hindi STT/TTS, Notification workflows, Worker co-pilot, Planning narratives.
3. **P2**: WhatsApp/IVR integration, GIS maps, State APIs.

## 5. Estimated Engineering Effort
- **Phase 1 (Foundation & Security)**: 2 weeks (Database setup, Auth, Middleware).
- **Phase 2 (Catalogue & Verification)**: 2-3 weeks (NQR import, CRUD for opportunities, match state logic).
- **Phase 3 (Beneficiary Experience)**: 3 weeks (UI flows, Accessibility).
- **Phase 4 (AI Engine)**: 3-4 weeks (Provider adapters, deterministic matching).
- **Phase 5 (Worker Case Management)**: 2-3 weeks.
- **Phase 6 (District Planning)**: 2 weeks.
- **Total**: ~14 weeks for core production readiness.
