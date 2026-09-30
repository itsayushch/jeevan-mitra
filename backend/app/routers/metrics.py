from fastapi import APIRouter, Request, Response
from fastapi.responses import PlainTextResponse, JSONResponse
from app.core.metrics import generate_prometheus_metrics, get_operational_metrics

router = APIRouter(tags=["Metrics"])


@router.get("/metrics")
async def metrics_endpoint(request: Request):
    """
    Exposes operational metrics.
    Returns Prometheus / OpenMetrics format by default.
    Returns JSON if query parameter `format=json` or header `Accept: application/json`.
    """
    accept = request.headers.get("accept", "")
    format_param = request.query_params.get("format", "")

    if "application/json" in accept or format_param.lower() == "json":
        return JSONResponse(content=get_operational_metrics())

    prometheus_data = generate_prometheus_metrics()
    return Response(
        content=prometheus_data,
        media_type="text/plain; version=0.0.4; charset=utf-8"
    )


@router.get("/metrics/summary")
async def metrics_summary_endpoint():
    """Returns JSON summary of system operational health and indicators."""
    return get_operational_metrics()
