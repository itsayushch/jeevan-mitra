# Backend Release Checklist

Before deploying a new version of the JeevanMitra 2.0 backend, ensure all items in this checklist are verified.

## Environment and Configuration
- [ ] Environment variables (e.g., `DB_PATH`, `JWT_SECRET`, `API_KEYS`) are correctly set in the deployment environment.
- [ ] Database migrations have been reviewed and applied.
- [ ] Feature flags for new endpoints/services are correctly configured.
- [ ] External service endpoints (e.g., LLM services, SMS gateways) point to production URLs.

## Privacy and Data Safety
- [ ] DPDP consent mechanisms are functioning as expected.
- [ ] Consent revocation logic successfully cascades and stops data processing.
- [ ] PII deletion mechanisms (hard delete) are tested and verified.
- [ ] Logs do not contain plain-text PII or sensitive audio transcripts.

## Recommendation Safety
- [ ] Deterministic matching engine prioritizes verified catalog entries.
- [ ] Fallback handling for missing attributes behaves safely and predictably.
- [ ] Output filtering prevents inappropriate or off-topic recommendations.

## Security and Access Control
- [ ] All API endpoints enforce proper authentication (Actor dependencies).
- [ ] Role-Based Access Control (RBAC) allows only authorized actions.
- [ ] Rate limiting is applied to prevent abuse (especially on `POST /start` and `/respond`).
- [ ] CORS policies restrict access to trusted frontend domains.

## Quality and Deployment
- [ ] Unit and end-to-end test suites pass successfully.
- [ ] `API_CHANGELOG.md` is updated with all contract modifications.
- [ ] Documentation (`FRONTEND_API_HANDOFF.md`, Swagger/OpenAPI spec) accurately reflects the current state.
- [ ] Deployment runbooks and rollback strategies are up-to-date.
