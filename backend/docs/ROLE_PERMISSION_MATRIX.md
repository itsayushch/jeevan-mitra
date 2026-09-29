# Role Permission Matrix

This document outlines the access controls for JeevanMitra 2.0 based on Plan C requirements.

## Roles
- **Anonymous**: Basic access, landing page.
- **Beneficiary**: Can access their own profile, interview, recommendations.
- **Counselor**: Can access beneficiary profiles assigned to them, provide overrides.
- **Catalogue Admin**: Can manage opportunities, qualifications, schemes.
- **Analyst**: View system metrics, quality summaries.
- **Super Admin**: Full access to all endpoints, including system management.

## Matrix

| Endpoint | Anonymous | Beneficiary | Counselor | Catalogue Admin | Analyst | Super Admin |
|----------|-----------|-------------|-----------|-----------------|---------|-------------|
| /api/v1/interview | ❌ | ✅ | ✅ | ❌ | ❌ | ✅ |
| /api/v1/recommendations | ❌ | ✅ | ✅ | ❌ | ❌ | ✅ |
| /api/v1/monitoring/admin/system/status | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| /api/v1/monitoring/admin/system/quality-summary| ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| /api/v1/catalogue/* | ❌ | ❌ | ❌ | ✅ | ❌ | ✅ |
