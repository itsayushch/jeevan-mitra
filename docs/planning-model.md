# Layer 5 — District Planning Model (Claim 2: The Planning Loop)

Turns beneficiary conversations into district/block-level supply-gap evidence and
generates a plain-language planning brief for district officers. **Every number in
the brief comes from a database query. The LLM never produces a figure.**

## 1. End-to-end flow

```
interview (consented) -> recommendations/generate
        |                                   |
        v                                   v
demand_records (anonymised)         local_opportunities (worker-verified supply)
        |                                   |
        +---------------+------------------------+
                        v
        AggregationService.get_demand_supply_matrix(district, period)
                        |
                        v
        NarrativeEngine.generate_brief(matrix)   <- template-first, LLM only rephrases
                        |
                        v
        planning_briefs (snapshot + narrative + status=draft)
                        |
                        v
        sign-off (draft -> under_review -> signed_off) -> export (CSV / PDF-ready JSON)
```

## 2. Demand records (privacy)

Written by `DemandRecordService.record_demand` when recommendations are generated
for a confirmed profile (`RecommendationService.generate_recommendations`,
backend/app/services/recommendation_service.py:319).

* **Consent gate:** a record is written only if the beneficiary has a granted
  `analytics` consent row (`consent_records.consent_type='analytics'`). With no
  beneficiary/session identifier, consent is unverifiable and nothing is written
  (privacy by default).
* **Anonymised columns only:** `qualification_id, district, block,
  mobility_radius_km, work_preference, had_verified_match, period, created_at`.
  No name, contact, audio, or free text.
* **No join keys:** the record id is an opaque random token (`dem_<hex>`). There is
  no foreign key to `beneficiaries`, `interview_sessions`, or any other PII table,
  so the table cannot be joined back to an individual. It lives in its own table,
  separate from PII tables.
* `had_verified_match` records whether a Verified Match existed for that
  recommendation set (match_state logic is untouched).

## 3. Supply (verified batches only)

From `local_opportunities`, a batch counts toward supply only if **all** hold:

```sql
verified_by_worker_id IS NOT NULL               -- worker-verified
AND substr(verified_at,1,10) >= today - OPPORTUNITY_REVIEW_DAYS   -- non-stale (30d)
AND batch_end_date >= date('now')                -- still running / upcoming
AND available_seats > 0                          -- seats actually available
AND is_archived = 0                              -- non-archived
```

Seats are summed per qualification per block (`available_seats` = verified seats,
`total_seats` = sanctioned capacity).

## 4. Aggregation matrix

`AggregationService.get_demand_supply_matrix(district, period)` returns one row per
block x qualification:

| column | meaning |
|---|---|
| `demand_count` | anonymised demand records in the cell |
| `verified_seats` | sum of `available_seats` from eligible batches in the cell |
| `total_seats` | sum of `total_seats` from eligible batches in the cell |
| `gap` | `demand_count - verified_seats` (positive = unmet demand) |
| `nearest_verified_centre_km` | haversine distance from the block centroid to the nearest eligible centre for that qualification **in the district** (null if none exists) |
| `share_of_demand_with_no_verified_batch` | fraction of the cell's demand records with no eligible batch in the same block within the record's mobility radius (null mobility = any batch in the block covers) |
| `coverage` | `min(verified_seats / demand_count, 1)` |
| `severity_score` | see formula below |
| `suppressed` | k-anonymity flag (see below) |

### Gap severity formula (auditable, returned in every API response)

```
coverage        = min(verified_seats / demand_count, 1)
distance_factor = 1 + min(nearest_verified_centre_km, 50) / 50
                  (2.0 when no verified centre exists in the district)
severity        = demand_count * (1 - coverage) * distance_factor
```

Rationale: unmet demand (`demand_count * (1 - coverage)`) is the base; the distance
penalty (1.0x-2.0x) prioritises gaps that are also geographically inaccessible.
The formula, the 50 km cap, and the k-anonymity threshold are exposed in the
`gap_scoring` block of the API response so officers can audit the ranking.

### K-anonymity (small-cell suppression)

Cells with `demand_count < 5` are **suppressed**: numeric figures are nulled, the
cell is flagged `suppressed: true` with a `suppression_reason`, demand row ids are
withheld, and the cell is excluded from gap ranking. Suppressed cells are still
listed (after all reportable cells) so officers can see where data is thin.

### Insufficient data

A district (or district+period) with zero demand records returns
`status: "insufficient_data"` with an explicit message — never estimated figures.
Brief generation for such a district fails with HTTP 422 `insufficient_data`.

## 5. Narrative engine (template-first)

`NarrativeEngine.generate_brief(matrix)`:

1. **Template first.** The brief is built from a fixed template containing
   placeholders (`{demand_count}`, `{top_block}`, `{top_gap}`, ...). All
   placeholder values come from the aggregation query result.
2. **LLM may only rephrase.** If `AI_PROVIDER` is not `mock` (and an API key is
   configured), the LLM receives the raw template and may rewrite sentences, but
   the placeholders must survive. Numbers are inserted by code **after**
   generation — the LLM never sees or emits a figure.
3. **Validator.** LLM output is rejected if it (a) drops/mangles any template
   placeholder, or (b) contains a digit sequence not present in the query result
   (the allowed set is derived from every numeric value in the result plus digits
   inside the template's own static text). Rejected output falls back to the raw
   template; the outcome is recorded in `narrative_meta.validation`.
4. **Source references.** Every figure carries `source_query_id` and
   `source_row_ids` (see section 6).

## 6. Figure-to-source traceability

* Each matrix cell carries `source.query_id` (a deterministic SHA-256 over the
  district, period, cell key, and the sorted row ids that produced it),
  `source.demand_row_ids`, and `source.supply_batch_ids`.
* The whole matrix carries a top-level `query_id`.
* A generated brief stores the **full aggregation snapshot** (every cell with its
  source references) in `planning_briefs.aggregation_snapshot`, plus the narrative
  and `generated_at`.
* The narrative's `figures` list maps each cited figure to its cell's
  `query_id` and row ids.
* Officers can re-run the same query (`GET /planning/matrix?district=&period=`)
  and reproduce every number exactly — the query is deterministic.

## 7. Brief lifecycle and access control

* `POST /planning/briefs/generate` → `draft` (stores snapshot + narrative).
* `POST /planning/briefs/{id}/sign-off` with `action`:
  * `submit_for_review`: `draft -> under_review`
  * `sign_off`: `draft|under_review -> signed_off` (sets `signed_off_by/at`)
  * Invalid transitions → 409. Every transition writes an `audit_events` row
    (`BRIEF_GENERATED`, `BRIEF_UNDER_REVIEW`, `BRIEF_SIGNED_OFF`).
* `GET /planning/briefs/{id}/export` → **409 unless `signed_off`**. CSV by
  default; `?format=json` returns PDF-ready JSON (brief + snapshot + narrative).
* All endpoints require a real role check (`district_officer` or `admin`) via
  `app/dependencies/roles.py`: credentials are compared against server-side
  secrets with `hmac.compare_digest` — no prefix tricks. A `district_officer` is
  scoped to `OFFICER_DISTRICT` and cannot read another district's data (403
  `DISTRICT_SCOPE_VIOLATION`); the scope fails closed when unconfigured. Admins
  are unrestricted. Field workers and beneficiaries are rejected (403).

## 8. API summary

| endpoint | role | purpose |
|---|---|---|
| `GET /planning/matrix?district=&period=` | officer/admin | demand vs verified-supply matrix |
| `POST /planning/briefs/generate` | officer/admin | generate brief (snapshot + narrative) |
| `GET /planning/briefs/{id}` | officer/admin | fetch brief |
| `POST /planning/briefs/{id}/sign-off` | officer/admin | review lifecycle + audit |
| `GET /planning/briefs/{id}/export?format=csv\|json` | officer/admin | export signed-off brief |
| `GET /planning/briefs` | officer/admin | list briefs (officer auto-scoped) |

Legacy aliases (`/planning/supply-gap-matrix`, `/planning/generate-brief`,
`/planning/export`) are kept for backwards compatibility and enforce the same
auth. Routes are mounted under both `/api/v1` and `/api`.

## 9. Demo data

`backend/scripts/seed_demo_data.py` creates ~200 synthetic anonymised demand
records across 5 blocks (Bahjoi, Chhajlet, Moradabad Rural, Bilari, Kundarki).
Bahjoi has 80 expressions of interest (38 for Mushroom Cultivation) and **zero**
worker-verified batches; the nearest verified mushroom centre (KVK Chhajlet) is
~65 km away, producing the demo's top severity-ranked gap. Changing a seat count
via the worker `/verify` endpoint and regenerating the brief changes the brief's
numbers accordingly.
