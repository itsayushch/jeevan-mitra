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
    catalogue,
    chat
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting JeevanMitra 2.0 Python FastAPI Core Service...")
    logger.info(f"Environment: {settings.NODE_ENV} | Pilot District: {settings.DEFAULT_DISTRICT}")
    init_database()
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

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        start_time = time.time()
        
        response = await call_next(request)
        
        process_time = time.time() - start_time
        logger.info(
            f"method={request.method} path={request.url.path} "
            f"status={response.status_code} latency={process_time:.4f}s "
            f"request_id={request_id}"
        )
        response.headers["X-Request-ID"] = request_id
        return response

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.rate_limits = {}
        
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        path = request.url.path
        
        # Stricter limit for chat/interview endpoints
        limit = 20 if "/chat" in path or "/interview" in path else 100
        
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

# Include API routers under /api/v1 prefix
api_prefix = settings.API_PREFIX
app.include_router(health.router, prefix=api_prefix)
app.include_router(beneficiaries.router, prefix=api_prefix)
app.include_router(consents.router, prefix=api_prefix)
app.include_router(interview.router, prefix=api_prefix)
app.include_router(recommendations.router, prefix=api_prefix)
app.include_router(worker.router, prefix=api_prefix)
app.include_router(referrals.router, prefix=api_prefix)
app.include_router(planning.router, prefix=api_prefix)
app.include_router(monitoring.router, prefix=api_prefix)
app.include_router(channels.router, prefix=api_prefix)
app.include_router(audit.router, prefix=api_prefix)
app.include_router(catalogue.router, prefix=api_prefix)
app.include_router(chat.router, prefix=api_prefix)

# Also expose health check at root /health for convenience
app.include_router(health.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)

