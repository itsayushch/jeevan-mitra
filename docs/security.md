# JeevanMitra 2.0 Security Guidelines

## 1. Principles
- **Verification before Action**: Only human verified opportunities map to referrals.
- **Grounded AI Only**: LLMs operate on structured, verified data.
- **Privacy by Design**: Minimum data collection. PII must be encrypted at rest and in transit.

## 2. API Security
- **Authentication**: Mandatory for all endpoints (except public health checks).
- **Authorization**: Strict Role-Based Access Control (RBAC). A worker can only edit their assigned cases within their district block.
- **Rate Limiting**: Prevent abuse, especially on transcription and AI endpoints.
- **CORS**: Strict allowlisting per environment.

## 3. Data Integrity & Audit
- All privileged actions (e.g., verifying an opportunity, changing a referral status) generate immutable audit logs (`audit_events`).
- PII and sensitive fields (e.g., caste documents) are kept separate from the general profile and out of AI prompts.

## 4. Operational Security
- **Secrets Management**: No secrets in `.env.example` or code repositories.
- **Upload Restrictions**: Only allowed file types, max sizes, malware scanning hooks, and private storage for uploads.
