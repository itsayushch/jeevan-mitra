from fastapi import APIRouter
from app.ai_layers.layer6_monitoring.drift_detector import DriftDetector
from app.ai_layers.layer6_monitoring.advisory_queue import AdvisoryQueue

router = APIRouter(prefix="/monitoring", tags=["Monitoring"])

@router.get("/drift")
def get_drift_anomalies(district: str = "Moradabad"):
    return {
        "district": district,
        "anomalies": DriftDetector.detect_anomalies(district)
    }

@router.get("/advisories")
def get_advisories(district: str = "Moradabad"):
    return {
        "district": district,
        "advisories": AdvisoryQueue.list_open_advisories(district)
    }
