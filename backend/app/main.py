from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
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
    logger.info("  MoSJE PM-AJAY GIA Component (Problem Statement ID 26097)")
    logger.info("================================================================")
    logger.info(f"  Server URL:             http://{settings.HOST}:{settings.PORT}")
    logger.info(f"  Health Check:           http://{settings.HOST}:{settings.PORT}/api/health")
    logger.info("  Claim 1 Invariant:      Verified Match Protocol [ACTIVE]")
    logger.info("  Claim 2 Planning Loop:  Aggregated Supply-Gap Engine [ACTIVE]")
    logger.info("  Six AI Layers:          L1 Intake, L2 Extraction, L3 RAG Matcher,")
    logger.info("                          L4 Co-Pilot, L5 Narrative Brief, L6 Bias Drift")
    logger.info("================================================================")
    yield
    logger.info("Shutting down JeevanMitra 2.0 Python backend...")

app = FastAPI(
    title="JeevanMitra 2.0 Core API",
    description="MoSJE PM-AJAY GIA Component Livelihood Matching and District Planning Backend in Python",
    version="2.0.0",
    lifespan=lifespan
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers under /api prefix to match frontend Vite proxy
api_prefix = "/api"
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
