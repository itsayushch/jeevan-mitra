# API Changelog

This document tracks changes to the JeevanMitra 2.0 API contracts.

## Version Policy
- **Major versions (v1, v2):** Introduce breaking changes to the API contract. A new major version will run concurrently with the old version for a deprecation period.
- **Minor additions:** Non-breaking changes (e.g., adding new endpoints, adding optional fields to requests, adding new fields to responses) do not require a version bump.
- **Deprecation:** Endpoints marked for deprecation will return a `DeprecationWarning` header and will be supported for at least 3 months.

## [Unreleased]
### Added
- Journey API endpoints (`/api/v1/journey/*`) to encapsulate the entire user lifecycle.
- Versioned Consent management endpoints (`/consents` with `ConsentRecordCreate`).
- Deterministic recommendation engine endpoint (`/recommendations/generate`).

### Changed
- Legacy `/recommendations/match` is maintained for backward compatibility.
- Legacy `/consents` payload schema gracefully maps to the new `ConsentRecordCreate` model.

### Deprecated
- N/A

### Removed
- N/A
