from fastapi import APIRouter, Depends
from app.ai_layers.layer6_monitoring.drift_detector import DriftDetector
from app.ai_layers.layer6_monitoring.advisory_queue import AdvisoryQueue
from app.dependencies.auth import Actor, require_admin_or_worker

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

from app.services.system_status_service import SystemStatusService
from app.services.alert_service import OperationalAlertService
from app.core.metrics import generate_prometheus_metrics, get_operational_metrics
from fastapi.responses import PlainTextResponse

@router.get("/admin/system/status")
def get_admin_system_status(actor: Actor = Depends(require_admin_or_worker)):
    return SystemStatusService.get_system_status()

@router.get("/admin/system/quality-summary")
def get_admin_quality_summary(actor: Actor = Depends(require_admin_or_worker)):
    return SystemStatusService.get_quality_summary()

@router.get("/alerts")
def get_operational_alerts():
    """Returns active operational health indicators and alerts across services."""
    return OperationalAlertService.evaluate_all_alerts()

@router.get("/metrics/prometheus", response_class=PlainTextResponse)
def get_prometheus_metrics():
    """Exposes real-time Prometheus / OpenMetrics scraping format."""
    return generate_prometheus_metrics()

@router.get("/metrics/operational")
def get_ops_metrics():
    """JSON format operational metrics."""
    return get_operational_metrics()
