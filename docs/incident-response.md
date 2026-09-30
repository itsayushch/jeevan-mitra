# JeevanMitra 2.0 Incident Response & Diagnostic Playbooks

## 1. Severity Classification

| Level | Definition | Impact | Response SLA | Target Resolution |
| :--- | :--- | :--- | :--- | :--- |
| **Sev 1 (Critical)** | Core service down; total loss of intake, matching, or referral service. | All users blocked | 15 minutes | $< 2$ hours |
| **Sev 2 (Major)** | Core service degraded; AI fallback active; exports failing; database slow. | Significant portion of users impacted | 30 minutes | $< 6$ hours |
| **Sev 3 (Moderate)** | Non-blocking bug; specific block/language glitch; metrics collection error. | Minor operational impact | 2 hours | $< 24$ hours |
| **Sev 4 (Minor)** | UI cosmetic error, typo in translation key, minor documentation defect. | Minimal impact | 1 business day | Next release cycle |

---

## 2. Diagnostic Playbooks

### Playbook 1: Backend Service 503 / Unavailable

**Symptom**: `GET /health/ready` returns HTTP 503 with `"status": "unavailable"`.

1. **Inspect Readiness Probe Response**:
   ```bash
   curl -i http://127.0.0.1:4000/health/ready
   ```
   Determine which dependency failed:
   - If `"database": "unhealthy"`: Proceed to Step 2.
   - If `"storage": "unhealthy"`: Check disk space (`df -h`) and write permissions on `/var/lib/jeevanmitra/evidence/`.

2. **Verify Database Service**:
   ```bash
   # Check if database file is locked or corrupt
   sqlite3 /opt/jeevanmitra/backend/jeevanmitra.db "PRAGMA integrity_check;"
   ```
3. **Inspect Application Systemd Logs**:
   ```bash
   sudo journalctl -u jeevanmitra-backend -n 100 --no-pager
   ```
4. **Restart Backend Service**:
   ```bash
   sudo systemctl restart jeevanmitra-backend
   curl -f http://127.0.0.1:4000/health/live
   ```

---

### Playbook 2: Database Schema / Migration Head Failure

**Symptom**: Startup crashes with `Alembic revision mismatch` or logs show `no such table`.

1. **Check Current Database Revision**:
   ```bash
   cd /opt/jeevanmitra/backend
   python -c "from app.database import get_db;
   with get_db() as conn:
       print('Current DB version:', conn.execute('SELECT version_num FROM alembic_version;').fetchone())"
   ```
2. **Inspect Migration Status**:
   ```bash
   alembic current
   alembic history
   ```
3. **Apply Pending Migrations**:
   ```bash
   alembic upgrade head
   ```

---

### Playbook 3: Spike in 401 / 403 Authentication Failures

**Symptom**: `jeevanmitra_http_auth_errors_total` increases sharply on Prometheus dashboard.

1. **Check Metrics Summary**:
   ```bash
   curl -s http://127.0.0.1:4000/metrics/summary | jq .auth_errors
   ```
2. **Review Filtered Logs for Malicious Patterns**:
   ```bash
   sudo journalctl -u jeevanmitra-backend | grep "status=401" | tail -n 50
   ```
   Check if a single client IP is brute-forcing logins or presenting an expired JWT secret.
3. **Verify JWT Configuration**:
   ```bash
   curl -s http://127.0.0.1:4000/health/config | jq .config.jwt_secret_configured
   ```

---

### Playbook 4: Elevated Latency (p95 > 500ms)

**Symptom**: Load testing or monitoring alerts on high response times.

1. **Execute In-Process Benchmark**:
   ```bash
   python /opt/jeevanmitra/backend/scripts/load_test.py --concurrency 5 --requests 20
   ```
2. **Examine Endpoint Breakdown**: Identify which route has elevated latencies:
   - If `/api/v1/planning/overview`: Check index on `recommendations(qualification_id, match_state)`.
   - If `/api/v1/opportunities`: Check index on `local_opportunities(district_id, status)`.
3. **Run SQLite Query Optimization**:
   ```bash
   sqlite3 /opt/jeevanmitra/backend/jeevanmitra.db "PRAGMA optimize;"
   ```

---

## 3. Post-Mortem Incident Template

```markdown
# Incident Post-Mortem: [INCIDENT TITLE]

- **Date**: YYYY-MM-DD
- **Severity**: Sev 1 / Sev 2 / Sev 3
- **Duration**: [Start Time UTC] to [Resolution Time UTC] (Total: X minutes)
- **Incident Commander**: [Name / Role]

## 1. Summary
[Brief high-level description of what occurred and user impact]

## 2. Root Cause
[Technical detail explaining why the failure happened]

## 3. Timeline
- HH:MM UTC - Initial symptom / alert triggered
- HH:MM UTC - Incident triage started
- HH:MM UTC - Root cause identified
- HH:MM UTC - Mitigation deployed
- HH:MM UTC - System verified operational via /health/ready

## 4. Preventive & Action Items
- [ ] Action item 1 (Owner, Target Date)
- [ ] Action item 2 (Owner, Target Date)
```
