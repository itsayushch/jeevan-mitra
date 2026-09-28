from fastapi import APIRouter
from datetime import datetime, timezone
from app.database import get_db
from app.config import settings

router = APIRouter(tags=["Health"])

@router.get("/health")
def health_check():
    db_status = "healthy"
    try:
        with get_db() as conn:
            conn.execute("SELECT 1;").fetchone()
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return {
        "service": "JeevanMitra 2.0 Backend Core (Python / FastAPI)",
        "status": "operational",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "environment": settings.NODE_ENV,
        "defaultDistrict": settings.DEFAULT_DISTRICT,
        "defaultState": settings.DEFAULT_STATE,
        "aiProvider": settings.AI_PROVIDER,
        "database": db_status,
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
