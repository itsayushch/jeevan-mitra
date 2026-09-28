# JeevanMitra 2.0 Decision Log

| Date | Topic | Decision | Rationale |
|---|---|---|---|
| 2026-09-28 | **Architecture Pattern** | Adopt Modular Monolith over Microservices | Keeps deployment and local development simple. Can split later when team or traffic scales. |
| 2026-09-28 | **Database** | Move from SQLite to PostgreSQL | Required for production-grade concurrency, row-level security, jsonb, and pgvector. |
| 2026-09-28 | **AI Action Boundary** | LLM cannot initiate referral | "Human in the loop" is critical. AI only ranks and explains; worker verifies and executes. |
| 2026-09-28 | **Match State Integrity** | Enforce match state strictly in Backend & DB | Prevent frontend tampering or prompt injection from creating false availability. |
