# JeevanMitra 2.0 Production Deployment Guide

## 1. Overview & Architecture

JeevanMitra 2.0 is deployed as a two-tier architecture:
1. **Frontend**: Next.js 15 (Node.js 20) rendering accessible bilingual interfaces, static dashboards, and localized interactive counseling.
2. **Backend**: Python 3.11 FastAPI asynchronous service handling intake, grounded matching, referral tracking, case management, immutable district planning aggregations, and metrics exposition.

### Network Topology

```
[ Internet / Beneficiaries & Staff ]
                 │
                 ▼ (HTTPS / TLS 1.3 :443)
       ┌───────────────────┐
       │ NGINX / Cloudflare│
       │ Reverse Proxy     │
       └─────────┬─────────┘
                 │
      ┌──────────┴──────────┐
      │                     │
      ▼ (:3000)             ▼ (:4000)
┌───────────┐         ┌───────────────────────┐
│ Next.js   │         │ FastAPI Backend Core  │
│ Frontend  │         │ (Uvicorn Workers)     │
└───────────┘         └───────────┬───────────┘
                                  │
                                  ▼
                      ┌───────────────────────┐
                      │ Production Database   │
                      │ (PostgreSQL / Managed)│
                      └───────────────────────┘
```

---

## 2. Environment Configuration Matrix

The application differentiates environments via `APP_ENV` (`local`, `staging`, `production`).

| Variable | Description | Local Default | Staging Requirement | Production Requirement |
| :--- | :--- | :--- | :--- | :--- |
| `APP_ENV` | Environment identifier | `local` | `staging` | `production` |
| `DATABASE_URL` | SQLAlchemy connection string | `sqlite:///./jeevanmitra.db` | PostgreSQL connection | PostgreSQL connection |
| `ALLOW_SQLITE_IN_PRODUCTION` | Flag permitting SQLite in prod | `false` | `false` | `false` (fail startup if SQLite) |
| `JWT_SECRET` | Secret key for JWT signing | Dev fallback string | 64+ char random secret | 64+ char random secret |
| `JWT_ACCESS_TOKEN_MINUTES` | Access token lifespan | `15` | `15` | `15` |
| `REFRESH_TOKEN_DAYS` | Refresh token lifespan | `7` | `7` | `7` |
| `STORAGE_PROVIDER` | Evidence/export storage | `local` | `s3` or `gcs` | `s3` or `gcs` |
| `STORAGE_BUCKET` | Private cloud bucket | `jeevanmitra-private` | Authorized bucket name | Authorized bucket name |
| `EXPORT_RETENTION_DAYS` | Planning export file TTL | `7` | `7` | `7` |
| `PLANNING_MIN_CELL_COUNT` | Privacy suppression threshold | `5` | `5` | `5` |
| `NEXT_PUBLIC_DEMO_AUTH_FALLBACK` | Permitted mock auth bypass | `false` | **MUST BE FALSE** | **MUST BE FALSE** |
| `LOG_LEVEL` | Logging verbosity | `INFO` | `INFO` | `INFO` / `WARNING` |
| `RELEASE_VERSION` | Release identifier | `2.0.0-rc1` | `2.0.0-rc1` | `2.0.0` |
| `GIT_COMMIT_SHA` | Injected build commit SHA | `dev-local` | Commit hash | Commit hash |

---

## 3. Production Pre-Flight Invariants

The backend executes `validate_production_constraints()` at startup. The process terminates immediately with an error if:
- `JWT_SECRET` is less than 32 characters, contains `"supersecret"`, or is empty.
- `DATABASE_URL` contains `sqlite` while `APP_ENV=production`, unless `ALLOW_SQLITE_IN_PRODUCTION=true` is explicitly set.
- `NEXT_PUBLIC_DEMO_AUTH_FALLBACK` is `true` in `staging` or `production`.

---

## 4. Systemd Service Deployment

### Backend Service: `/etc/systemd/system/jeevanmitra-backend.service`

```ini
[Unit]
Description=JeevanMitra 2.0 FastAPI Backend Core
After=network.target postgresql.service

[Service]
Type=simple
User=jeevanmitra
Group=jeevanmitra
WorkingDirectory=/opt/jeevanmitra/backend
EnvironmentFile=/etc/jeevanmitra/backend.env
ExecStart=/opt/jeevanmitra/backend/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 4000 --workers 4 --proxy-headers
Restart=always
RestartSec=5s
LimitNOFILE=65535

# Security sandbox
ProtectSystem=full
ProtectHome=true
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

### Frontend Service: `/etc/systemd/system/jeevanmitra-frontend.service`

```ini
[Unit]
Description=JeevanMitra 2.0 Next.js Frontend
After=network.target

[Service]
Type=simple
User=jeevanmitra
Group=jeevanmitra
WorkingDirectory=/opt/jeevanmitra/frontend
EnvironmentFile=/etc/jeevanmitra/frontend.env
ExecStart=/usr/bin/npm start -- -p 3000
Restart=always
RestartSec=5s

[Install]
WantedBy=multi-user.target
```

---

## 5. Reverse Proxy Configuration (NGINX)

```nginx
# /etc/nginx/sites-available/jeevanmitra.gov.in

limit_req_zone $binary_remote_addr zone=api_limit:10m rate=30r/s;
limit_req_zone $binary_remote_addr zone=auth_limit:10m rate=5r/s;

server {
    listen 80;
    server_name jeevanmitra.gov.in;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name jeevanmitra.gov.in;

    ssl_certificate /etc/letsencrypt/live/jeevanmitra.gov.in/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/jeevanmitra.gov.in/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Security Headers
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header Content-Security-Policy "default-src 'self'; frame-ancestors 'none'; object-src 'none'; base-uri 'self';" always;

    # Request ID Propagation
    proxy_set_header X-Request-ID $request_id;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;

    # Frontend routes
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
    }

    # Backend API routes
    location /api/ {
        limit_req zone=api_limit burst=20 nodelay;
        proxy_pass http://127.0.0.1:4000;
        proxy_read_timeout 60s;
    }

    # Strict Auth Rate Limit
    location /api/v1/auth/ {
        limit_req zone=auth_limit burst=5 nodelay;
        proxy_pass http://127.0.0.1:4000;
    }

    # Health & Observability (Internal Scrape Friendly)
    location /health/ {
        proxy_pass http://127.0.0.1:4000;
        access_log off;
    }

    location /metrics {
        allow 10.0.0.0/8; # Restrict Prometheus scrape to internal network
        allow 127.0.0.1;
        deny all;
        proxy_pass http://127.0.0.1:4000;
    }
}
```

---

## 6. Migration & Release Execution

```bash
# 1. Update source code
git pull origin main

# 2. Upgrade Python dependencies & run database migrations
cd backend
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head

# 3. Verify health & readiness before traffic cutover
python -c "from app.routers.health import readiness_probe; print(readiness_probe())"

# 4. Build and restart frontend
cd ../frontend
npm ci
npm run build
sudo systemctl restart jeevanmitra-frontend

# 5. Reload backend service
sudo systemctl restart jeevanmitra-backend

# 6. Post-deployment smoke check
curl -f https://jeevanmitra.gov.in/health/ready
curl -f https://jeevanmitra.gov.in/health/version
```
