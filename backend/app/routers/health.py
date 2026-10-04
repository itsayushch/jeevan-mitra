from fastapi import APIRouter
from datetime import datetime, timezone
import os
from pathlib import Path
from typing import Dict, Any
from app.database import get_db
from app.core.settings import settings
from fastapi.responses import JSONResponse

router = APIRouter(tags=["Health"])


def get_alembic_head_revision(conn) -> str:
    """Safely retrieves current alembic migration revision."""
    try:
        row = conn.execute("SELECT version_num FROM alembic_version LIMIT 1;").fetchone()
        if row and row[0]:
            return str(row[0])
        return "unmigrated"
    except Exception:
        return "unmigrated"


def check_storage_status() -> Dict[str, Any]:
    """Checks accessibility of storage backend."""
    if settings.STORAGE_PROVIDER == "local":
        try:
            storage_path = Path(settings.DATABASE_PATH).parent / settings.STORAGE_PRIVATE_PREFIX
            storage_path.mkdir(parents=True, exist_ok=True)
            test_file = storage_path / ".health_check_tmp"
            test_file.write_text("healthcheck", encoding="utf-8")
            if test_file.exists():
                test_file.unlink()
            return {"status": "healthy", "provider": "local"}
        except Exception as e:
            return {"status": f"unhealthy: {str(e)}", "provider": "local"}
    else:
        return {"status": "configured", "provider": settings.STORAGE_PROVIDER, "bucket": settings.STORAGE_BUCKET}


@router.get("/health")
def health_check():
    """General health check (backward compatible)."""
    return {
        "service": "JeevanMitra 2.0 Backend Core (Python / FastAPI)",
        "status": "operational",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "environment": settings.APP_ENV,
        "version": settings.RELEASE_VERSION,
    }


@router.get("/health/live")
def liveness_check():
    """Fast process liveness probe. Does not query database or external dependencies."""
    return {
        "status": "live",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "JeevanMitra 2.0 Backend Core",
        "environment": settings.APP_ENV,
        "version": settings.RELEASE_VERSION,
    }


@router.get("/health/ready")
def readiness_probe():
    """
    Deep readiness probe for orchestrators (Kubernetes/ECS/Systemd).
    Verifies database connectivity, Alembic schema version, and storage accessibility.
    Returns HTTP 503 if any dependency check fails.
    """
    db_status = "healthy"
    alembic_head = "unknown"
    storage_info = check_storage_status()

    # 1. Check database connectivity
    try:
        with get_db() as conn:
            conn.execute("SELECT 1;").fetchone()
            alembic_head = get_alembic_head_revision(conn)
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
        return JSONResponse(
            status_code=503,
            content={
                "status": "unavailable",
                "database": db_status,
                "alembic_head": alembic_head,
                "storage": storage_info.get("status", "unknown"),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

    # 2. Check storage status
    if "unhealthy" in storage_info.get("status", ""):
        return JSONResponse(
            status_code=503,
            content={
                "status": "unavailable",
                "database": db_status,
                "alembic_head": alembic_head,
                "storage": storage_info.get("status"),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

    return {
        "status": "ready",
        "database": db_status,
        "alembic_head": alembic_head,
        "storage": storage_info.get("status"),
        "storage_provider": storage_info.get("provider"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "environment": settings.APP_ENV,
    }


@router.get("/ready")
def legacy_readiness_check():
    """Backward compatible readiness check endpoint."""
    db_status = "healthy"
    try:
        with get_db() as conn:
            conn.execute("SELECT 1;").fetchone()
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
        return JSONResponse(status_code=503, content={"status": "unavailable", "database": db_status})

    return {
        "status": "ready",
        "database": db_status,
        "aiProvider": settings.AI_PROVIDER,
        "defaultDistrict": settings.DEFAULT_DISTRICT,
        "sixLayersStatus": {
            "layer1_intake": "active",
            "layer2_extraction": "active",
            "layer3_grounded_matching": "active",
            "layer4_copilot": "active",
            "layer5_planning_narrative": "active",
            "layer6_drift_monitoring": "active",
        },
        "verifiedMatchProtocol": "enforced"
    }


@router.get("/health/version")
def version_check():
    """Safe release version and commit metadata."""
    alembic_head = "unknown"
    try:
        with get_db() as conn:
            alembic_head = get_alembic_head_revision(conn)
    except Exception:
        pass

    return {
        "service": "JeevanMitra 2.0 Core API",
        "release_version": settings.RELEASE_VERSION,
        "git_commit_sha": settings.GIT_COMMIT_SHA,
        "environment": settings.APP_ENV,
        "alembic_head": alembic_head,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/health/config")
def config_report():
    """Safe, non-sensitive configuration report."""
    return {
        "status": "ok",
        "config": settings.get_safe_config_report(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
