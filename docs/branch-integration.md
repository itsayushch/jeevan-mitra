# Branch integration audit

Integration baseline: `origin/main` at `bbb9937`. Audit completed 2026-09-30.

## Branch inventory

| Branch | Audited tip | Status relative to baseline | Integration |
| --- | --- | --- | --- |
| Backend | 247a962 | Already merged | Retained through main |
| codex/frontend-workspace-redesign-20260929 | 5cfc745 | Already merged | Retained through main |
| feat/backend-e2e-release-readiness | 447907a | Already merged | Retained through main |
| feat/nextjs-migration | 5cfc745 | Already merged | Retained through main |
| fix/backend-integration-hardening | a6e6467 | Already merged | Retained through main |
| frontend2.0 | bbb9937 | Same as main | Retained through main |
| work | 02cf27d | Already merged | Retained through main |
| chore/backend-release-validation | 1e32734 | One unmerged commit | Merge commit, followed by compatibility correction |
| ML-model | af96bbc | Two unmerged commits | Merge commit and planning integration fixes |
| ml-recommendation | 58e25c4 | Three unmerged commits | Merge commit and optional inference adapter |

All branch histories are retained. No branches were deleted or histories rewritten.
The existing root layout remains: `backend/`, `frontend/`, and `docs/`.
The ML pipeline, synthetic datasets, reports and contributed model remain in
`backend/ml_model/`; no second application root or standalone ML API was added.

## Compatibility decisions

- Preserved main's configured staff credentials, session-token ownership checks,
  and all role settings. Planning accepts both the existing
  `DISTRICT_OFFICER_API_KEY` and the contributed `OFFICER_API_KEY`. District
  officers require `OFFICER_DISTRICT`; cross-district access fails closed.
- Updated the contributed planning tests to authenticate with session tokens.
  Public session IDs do not grant access.
- Planning checks the latest analytics-consent decision, including revocation.
  Sign-off audit records use the authenticated officer identity.
- The release-validation branch changed `journeys.session_id` to reference
  `anonymous_sessions`. Main's `JourneyService.start_journey` creates and stores
  an interview-session ID there. The merged implementation retains main's
  `interview_sessions` foreign key; the journey ownership regression test covers
  creation and access. Existing main databases retain their schema relationship.
- Removed the unused, broken AI orchestrator as the planning branch intended;
  live routes use the existing extraction/recommendation/planning services.
- ML imports use `ml_model.src` rather than a global `src` package. The model
  loader maps the contributed pickle's old transformer path to the shared
  inference transformer without importing training/plotting dependencies.
- The inference dependency file pins scikit-learn to the model artifact's
  training version, 1.9.0. Education labels such as `Class 10` are normalized
  before eligibility and feature calculation.
- The Next.js build explicitly uses the frontend directory as its tracing root.

## Optional ML ranking

The contributed model is trained on synthetic data. Its availability is not
evidence of predictive quality on real beneficiaries. It is disabled by default.

From `backend/`, using Python 3.12:

```sh
python -m pip install -r requirements.txt -r ml_model/requirements-inference.txt
python -m pytest tests/test_ml_adapter.py
```

Set `ML_RANKING_ENABLED=true` in the backend environment to opt in. The adapter
receives only verified catalogue candidates that already passed the existing
hard filters. It blends 80% of the deterministic score with 20% of the ML score,
records the components in `ranking_factors`, and cannot add synthetic courses,
alter eligibility, create seats, or upgrade a match's verification state.
Incomplete, invalid or unavailable model output retains deterministic ranking.
The application does not load synthetic CSVs for live matching.

For a container with inference dependencies, build from `backend/`:

```sh
docker build --build-arg INSTALL_ML=true -t jeevan-mitra-backend .
```

The default image retains the deterministic path. The model/package is included
in both variants; datasets, reports and local environments are excluded.

Standalone research commands work from `backend/`:

```sh
python -m ml_model.main --step predict
python -m ml_model.main --step predict_fallback
```

Training and EDA additionally require `ml_model/requirements.txt`.

## Validation

- Backend suite without ML dependencies: 89 passed, two optional ML tests skipped.
- Optional inference adapter suite with the actual model: 10 passed.
- Full backend suite with ML dependencies installed: 91 passed, zero skipped.
- Frontend production build and TypeScript checks passed.
- Git whitespace/conflict checks passed; branch ancestry is checked before delivery.
- CI includes separate backend, optional ML, frontend build and Docker build jobs.
- Local Docker build could not run because the Docker Desktop engine was stopped.
- External speech/LLM providers, cloud deployment and model accuracy on real data
  are not validated by these checks. Existing mock/stub integrations are not
  presented as completed provider implementations.
