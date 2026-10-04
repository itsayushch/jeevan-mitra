# JeevanMitra 2.0 Observability & Monitoring Guide

## 1. Observability Architecture

```
[ Incoming Requests ]
         │
         ▼
[ LoggingMiddleware ] ── Attach/Ingest X-Request-ID, Time Latency
         │
         ├──► [ Structured Logger ] ── Redact PII/Tokens ──► JSON Stdout / Log Aggregator
         │
         ▼
[ Metrics Collector ] ── In-Memory Prometheus Counters & Domain Gauges
         │
         ├──► GET /metrics (Prometheus / OpenMetrics text format)
         └──► GET /metrics/summary (JSON operational overview)
```

---

## 2. Health & Probe Endpoints

| Endpoint | Purpose | External Dependencies Checked | Expected Response |
| :--- | :--- | :--- | :--- |
| `GET /health/live` | Process liveness probe | None (Zero DB calls) | `200 OK` `{"status": "live", ...}` |
| `GET /health/ready` | Deployment readiness probe | Database (`SELECT 1`), Alembic head revision, Storage write access | `200 OK` (or `503 Service Unavailable`) |
| `GET /health/version` | Safe version & commit info | Alembic version table | `200 OK` `{"service": ..., "release_version": ..., "git_commit_sha": ...}` |
| `GET /health/config` | Safe configuration report | None (Redacts all credentials) | `200 OK` Non-sensitive configuration summary |

---

## 3. Metrics Catalog

### Prometheus Metrics Exposition (`GET /metrics`)

```prometheus
# HELP jeevanmitra_uptime_seconds Total service uptime in seconds
# TYPE jeevanmitra_uptime_seconds counter
jeevanmitra_uptime_seconds 3600

# HELP jeevanmitra_db_connected Database connectivity status (1=connected, 0=disconnected)
# TYPE jeevanmitra_db_connected gauge
jeevanmitra_db_connected 1

# HELP jeevanmitra_planning_suppressed_cells_total Total privacy cell suppression events (k < 5)
# TYPE jeevanmitra_planning_suppressed_cells_total counter
jeevanmitra_planning_suppressed_cells_total 14

# HELP jeevanmitra_active_opportunities_expiring_soon Active verified opportunities expiring in <= 14 days
# TYPE jeevanmitra_active_opportunities_expiring_soon gauge
jeevanmitra_active_opportunities_expiring_soon 3

# HELP jeevanmitra_overdue_referrals Referrals without updates for > 7 days in active stages
# TYPE jeevanmitra_overdue_referrals gauge
jeevanmitra_overdue_referrals 5

# HELP jeevanmitra_pending_outcome_verifications Referrals with reported outcomes awaiting verification
# TYPE jeevanmitra_pending_outcome_verifications gauge
jeevanmitra_pending_outcome_verifications 2

# HELP jeevanmitra_http_requests_total Total HTTP requests handled
# TYPE jeevanmitra_http_requests_total counter
jeevanmitra_http_requests_total{method="GET",path="/api/v1/opportunities",status="200"} 412
jeevanmitra_http_requests_total{method="GET",path="/health/live",status="200"} 1205

# HELP jeevanmitra_http_auth_errors_total Total HTTP 401/403 authorization failures
# TYPE jeevanmitra_http_auth_errors_total counter
jeevanmitra_http_auth_errors_total{status="401"} 2
jeevanmitra_http_auth_errors_total{status="403"} 1
```

---

## 4. Structured Logging & PII Redaction Filter

All log messages pass through `RedactingJsonFormatter` in production/staging environments.

### Redaction Rules
The logger automatically replaces:
- **JWT / Bearer Tokens**: Replaced with `Bearer [REDACTED_JWT]`
- **Passwords / Secrets**: Replaced with `[REDACTED]`
- **Aadhaar Numbers** (12 digits): Replaced with `[REDACTED_AADHAAR]`
- **Mobile Numbers** (10 digits starting 6-9): Replaced with `[REDACTED_PHONE]`
- **Email Addresses**: Replaced with `[REDACTED_EMAIL]`
- **Casework Notes / Raw Transcripts**: Masked to prevent leaking citizen narratives

---

## 5. Prometheus Scraping & Alerting Configuration

### `prometheus.yml` Scrape Job
```yaml
scrape_configs:
  - job_name: "jeevanmitra"
    scrape_interval: 15s
    static_configs:
      - targets: ["127.0.0.1:4000"]
    metrics_path: "/metrics"
```

### Critical Alert Rules
```yaml
groups:
  - name: jeevanmitra_alerts
    rules:
      - alert: ServiceDown
        expr: jeevanmitra_db_connected == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "JeevanMitra database connection lost"

      - alert: AuthFailureSpike
        expr: rate(jeevanmitra_http_auth_errors_total[5m]) > 10
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "Abnormal spike in 401/403 authorization failures"

      - alert: HighOverdueReferrals
        expr: jeevanmitra_overdue_referrals > 25
        for: 1h
        labels:
          severity: warning
        annotations:
          summary: "Over 25 referrals are stalled without caseworker contact for > 7 days"
```
