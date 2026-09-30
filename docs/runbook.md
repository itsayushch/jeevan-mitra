# JeevanMitra 2.0 Operations Runbook

## 1. System Setup & Migrations

### Database Migrations
Migrations are managed via Alembic in `backend/alembic`:
```bash
# Check current database revision
cd backend
python -m alembic current

# Upgrade database to latest revision (Head: d1e2f3a4b5c6)
python -m alembic upgrade head
```

### Full Backend Verification
```bash
cd backend
python -m pytest -q
# Target: 86 passed, 0 failed
```

### Frontend Build & Compilation
```bash
cd frontend
npm run build
# Target: All static & dynamic routes compiled cleanly
```

---

## 2. Monitoring & Health
- **Live Health Check**: `GET /api/v1/health` or `GET /health`
- **Catalogue Freshness**: Monitored via `CatalogueFreshnessService`. Alerts trigger when opportunities near expiry (<7 days) or exceed 90 days without re-verification.
- **Expiry Daemon**: Run periodically or via scheduled cron to sweep expired opportunities:
  `OpportunityExpiryService.expire_stale_opportunities(conn)`

---

## 3. Operational Escalations & Case Triage

### Case Stuck in Pipeline
1. Check `cases` table for `follow_up_due_at` date.
2. In the Field Worker Portal, filter by `HIGH` or `URGENT` priority.
3. If assigned worker is unavailable, reassign case via `POST /api/v1/staff/cases/{case_id}/assign`.

### Referral Dispute or Drop-Out
1. Check `referral_status_history` table for full provenance of state transitions.
2. If beneficiary opted out, record `BENEFICIARY_DECLINED` or `DROPPED_OUT`.
3. If provider rejected, transition status to `REJECTED` and add a case note explaining cause.

### Outcome Verification Flow
1. Field worker logs outcome via `POST /api/v1/staff/referrals/{id}/outcomes`. Status begins as `REPORTED`.
2. District Admin or Supervisor reviews certificate or offer letter evidence.
3. Supervisor calls `POST /api/v1/staff/referrals/outcomes/{outcome_id}/verify` with `{"verified": true}` to transition to `VERIFIED`.

---

## 4. Disaster Recovery & Rollback
1. SQLite database backups stored in daily timestamped snapshots.
2. If a migration needs rollback:
   `python -m alembic downgrade -1`
3. Audit logs in `audit_events` are append-only and immutable.
