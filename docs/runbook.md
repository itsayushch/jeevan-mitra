# JeevanMitra 2.0 Operations Runbook

## 1. System Setup & Migrations

### Database Migrations
Migrations are managed via Alembic in `backend/alembic`:
```bash
# Check current database revision
cd backend
python -m alembic current

# Upgrade database to latest revision (Head: f3a4b5c6d7e8)
python -m alembic upgrade head
```

### Full Backend Verification
```bash
cd backend
pytest -v
# Target: 138 passed, 0 failed
```

### Frontend Build & Compilation
```bash
cd frontend
npm run build
# Target: 14/14 static & dynamic routes compiled cleanly (0 TypeScript/Lint errors)
```

---

## 2. Health & Observability Endpoints

| Endpoint | Method | Expected Output | Purpose |
| :--- | :--- | :--- | :--- |
| `/health/live` | GET | `{"status": "live", ...}` | Process liveness probe (Zero DB queries) |
| `/health/ready` | GET | `{"status": "ready", ...}` | Deep dependency readiness (DB, Alembic, Storage) |
| `/health/version`| GET | `{"service": ..., "release_version": ...}` | Release version & git commit metadata |
| `/health/config` | GET | `{"status": "ok", "config": ...}` | Safe non-sensitive config report |
| `/metrics` | GET | Prometheus exposition format | Scraped by Prometheus / Datadog |
| `/metrics/summary`| GET | JSON operational indicators | Operational dashboard summary |

---

## 3. Disaster Recovery & Backup Operations

### Creating Atomic Point-in-Time Backup
Creates SQLite atomic snapshot with SHA-256 manifest:
```bash
cd backend
python scripts/backup_db.py --dest /var/backups/jeevanmitra
```

### Running Automated Disaster Recovery Restore Drill
Validates backup checksum, PRAGMA integrity, Alembic revision, and table counts:
```bash
cd backend
# Automated Recovery & Integrity Restore Drill
python scripts/db_backup_restore_drill.py
```

---

## 4. Performance & Load Benchmark Harness
Run concurrent load tests to measure throughput and latency percentiles (p50, p90, p95, p99):
```bash
cd backend
# In-process benchmark
python scripts/load_test.py --concurrency 10 --requests 60

# HTTP socket benchmark against live daemon
python scripts/load_test.py --url http://127.0.0.1:4000 --concurrency 20 --requests 100
```

---

## 5. District Planning, Snapshots & Export Operations

### Data Quality Telemetry Check
```bash
cd backend
python scripts/check_planning_data_quality.py --district-id Moradabad
```

### Scheduled Snapshot Freezing
```bash
cd backend
python scripts/generate_planning_snapshot.py --district-id Moradabad --period-start 2026-01-01 --period-end 2026-12-31
```

### Export Cleanup & Expiry Maintenance
```bash
cd backend
python scripts/expire_planning_exports.py
```

---

## 6. Operational Escalations & Case Triage

### Case Stuck in Pipeline
1. Check `beneficiary_cases` table for `next_follow_up_at` date.
2. In the Field Worker Portal, filter by `HIGH` or `URGENT` priority.
3. If assigned worker is unavailable, reassign case via `POST /api/v1/staff/cases/{case_id}/assign`.

### Referral Dispute or Drop-Out
1. Check `referral_status_history` table for full provenance of state transitions.
2. If beneficiary opted out, record `BENEFICIARY_DECLINED` or `DROPPED_OUT`.
3. If provider rejected, transition status to `REJECTED_BY_PROVIDER` and add a case note explaining cause.

### Outcome Verification Flow
1. Field worker logs outcome via `POST /api/v1/staff/referrals/{id}/outcomes`. Status begins as `REPORTED`.
2. District Admin or Supervisor reviews certificate or offer letter evidence.
3. Supervisor calls `POST /api/v1/staff/referrals/outcomes/{outcome_id}/verify` with `{"verified": true}` to transition to `VERIFIED`.

---

## 7. Operational Documentation Reference
- **Deployment**: [deployment.md](file:///c:/Users/DELL/JEEVAN-MITRA%202.0/docs/deployment.md)
- **Production Readiness**: [production-readiness.md](file:///c:/Users/DELL/JEEVAN-MITRA%202.0/docs/production-readiness.md)
- **Backup & Recovery**: [backup-recovery.md](file:///c:/Users/DELL/JEEVAN-MITRA%202.0/docs/backup-recovery.md)
- **Security Test Plan**: [security-test-plan.md](file:///c:/Users/DELL/JEEVAN-MITRA%202.0/docs/security-test-plan.md)
- **Pilot Operating Model**: [pilot-operations.md](file:///c:/Users/DELL/JEEVAN-MITRA%202.0/docs/pilot-operations.md)
- **Incident Response**: [incident-response.md](file:///c:/Users/DELL/JEEVAN-MITRA%202.0/docs/incident-response.md)
- **Accessibility & Localization QA**: [accessibility-qa.md](file:///c:/Users/DELL/JEEVAN-MITRA%202.0/docs/accessibility-qa.md)
- **Observability**: [observability.md](file:///c:/Users/DELL/JEEVAN-MITRA%202.0/docs/observability.md)
