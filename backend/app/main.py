from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from app.core.settings import settings
from app.database import init_database
from app.utils.logger import logger
from app.routers import (
    health,
    beneficiaries,
    consents,
    interview,
    recommendations,
    worker,
    referrals,
    planning,
    monitoring,
    channels,
    audit,
    qualifications,
    opportunities,
    catalogue,
    chat,
    journey,
    admin_catalogue,
    training,
    auth,
    cases,
    beneficiary_cases,
    opportunity_submissions,
    metrics,
    tts
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting JeevanMitra 2.0 Python FastAPI Core Service...")
    logger.info(f"Environment: {settings.NODE_ENV} | Pilot District: {settings.DEFAULT_DISTRICT}")
    # init_database() is replaced by Alembic migrations
    from app.db.session import get_db
    from app.services.nqr_catalogue import import_catalogue
    with get_db() as conn:
        import_catalogue(conn)
    logger.info("================================================================")
    logger.info("  JEEVAN-MITRA 2.0 PYTHON BACKEND SERVICE OPERATIONAL")
    logger.info("================================================================")
    yield
    logger.info("Shutting down JeevanMitra 2.0 Python backend...")

app = FastAPI(
    title="JeevanMitra 2.0 Core API",
    description="MoSJE PM-AJAY GIA Component Backend",
    version="2.0.0",
    lifespan=lifespan
)

# Exception handlers
from app.core.exceptions import DomainException
from app.utils.errors import AppError

@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail},
    )

@app.exception_handler(DomainException)
async def domain_exception_handler(request: Request, exc: DomainException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message, "details": exc.details}},
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"error": {"code": "VALIDATION_ERROR", "message": "Invalid request parameters", "details": exc.errors()}},
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "INTERNAL_SERVER_ERROR", "message": "An unexpected error occurred", "details": {}}},
    )

import time
import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logging import request_id_ctx_var, redact_text
from app.core.metrics import record_http_request

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Ingest incoming X-Request-ID header or generate new UUID4
        incoming_id = request.headers.get("x-request-id", "").strip()
        request_id = incoming_id if (incoming_id and len(incoming_id) <= 64) else str(uuid.uuid4())
        request.state.request_id = request_id
        token = request_id_ctx_var.set(request_id)

        start_time = time.time()
        try:
            response = await call_next(request)
        finally:
            request_id_ctx_var.reset(token)

        duration_ms = (time.time() - start_time) * 1000
        # Record operational metrics
        record_http_request(request.method, request.url.path, response.status_code, duration_ms)

        # Redact any sensitive path or query text before logging
        safe_path = redact_text(str(request.url.path))
        role = getattr(request.state, "actor_role", None) or "anonymous"
        district_scope = getattr(request.state, "district_scope", None) or "none"
        logger.info(
            f"request_id={request_id} release_version={settings.RELEASE_VERSION} "
            f"environment={settings.APP_ENV} route={safe_path} method={request.method} "
            f"status={response.status_code} duration={duration_ms:.2f}ms "
            f"role={role} district_scope={district_scope}"
        )
        response.headers["X-Request-ID"] = request_id
        return response

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Security hardening headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=(self)"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "frame-ancestors 'none'; "
            "object-src 'none'; "
            "base-uri 'self';"
        )

        if settings.is_production():
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        # Prevent caching for sensitive authenticated and planning endpoints
        path = request.url.path
        if any(p in path for p in ["/auth", "/referrals", "/planning/exports", "/beneficiaries", "/cases"]):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
            response.headers["Pragma"] = "no-cache"

        return response

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.rate_limits = {}

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        path = request.url.path

        # Stricter limit for chat/interview endpoints
        limit = 2000 if "/chat" in path or "/interview" in path else 1000

        now = time.time()
        key = f"{client_ip}:{path}"

        if key not in self.rate_limits:
            self.rate_limits[key] = []

        # Clean old requests (older than 1 minute)
        self.rate_limits[key] = [t for t in self.rate_limits[key] if now - t < 60]

        if len(self.rate_limits[key]) >= limit:
            return JSONResponse(status_code=429, content={"error": {"code": "RATE_LIMIT_EXCEEDED", "message": "Too many requests"}})

        self.rate_limits[key].append(now)
        return await call_next(request)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(LoggingMiddleware)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS if settings.NODE_ENV == "production" else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers under both /api/v1 and /api prefixes for full frontend & test compatibility
api_routers = [
    health.router,
    beneficiaries.router,
    consents.router,
    interview.router,
    recommendations.router,
    worker.router,
    referrals.router,
    planning.router,
    monitoring.router,
    channels.router,
    audit.router,
    qualifications.router,
    opportunities.router,
    catalogue.router,
    chat.router,
    journey.router,
    admin_catalogue.router,
    training.router,
    training.learning_router,
    training.admin_router,
    auth.router,
    cases.router,
    beneficiary_cases.router,
    opportunity_submissions.router,
    metrics.router,
    tts.router
]

for prefix in ["/api/v1", "/api"]:
    for r in api_routers:
        app.include_router(r, prefix=prefix)

# Also expose at root for direct path access
for r in [health.router, metrics.router, cases.router, referrals.router, beneficiary_cases.router, planning.router]:
    app.include_router(r)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
