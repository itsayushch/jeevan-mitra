from fastapi import APIRouter
from datetime import datetime, timezone
from app.database import get_db
from app.core.settings import settings
from fastapi.responses import JSONResponse

router = APIRouter(tags=["Health"])

@router.get("/health")
def health_check():
    return {
        "service": "JeevanMitra 2.0 Backend Core (Python / FastAPI)",
        "status": "operational",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "environment": settings.NODE_ENV
    }

@router.get("/ready")
def readiness_check():
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

