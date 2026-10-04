import re
import threading
import time
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from app.database import get_db

_lock = threading.Lock()

# Metrics storage
_http_requests_total: Dict[tuple, int] = defaultdict(int)
_http_request_durations: Dict[tuple, List[float]] = defaultdict(list)
_auth_errors_total: Dict[int, int] = defaultdict(int)
_server_errors_total: Dict[int, int] = defaultdict(int)
_cell_suppression_events: int = 0
_start_time: float = time.time()


def normalize_path(path: str) -> str:
    """Replaces variable IDs (UUIDs, ints) with placeholders to avoid metric explosion."""
    path = re.sub(r'/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', '/:id', path, flags=re.I)
    path = re.sub(r'/\d+', '/:id', path)
    return path


def record_http_request(method: str, path: str, status_code: int, duration_ms: float) -> None:
    norm_path = normalize_path(path)
    with _lock:
        _http_requests_total[(method, norm_path, status_code)] += 1
        # Keep recent 100 durations per key to prevent unbounded memory growth
        durations = _http_request_durations[(method, norm_path)]
        durations.append(duration_ms)
        if len(durations) > 100:
            durations.pop(0)

        if status_code in (401, 403):
            _auth_errors_total[status_code] += 1
        if status_code >= 500:
            _server_errors_total[status_code] += 1


def record_cell_suppression() -> None:
    global _cell_suppression_events
    with _lock:
        _cell_suppression_events += 1


def get_operational_metrics() -> Dict[str, Any]:
    """Computes real-time operational indicators from metrics registry and database."""
    uptime_seconds = int(time.time() - _start_time)
    db_connected = 0
    expiring_opportunities = 0
    overdue_referrals = 0
    pending_outcome_verifications = 0

    try:
        with get_db() as conn:
            conn.execute("SELECT 1;").fetchone()
            db_connected = 1

            # Expiring opportunities within 14 days
            try:
                row = conn.execute(
                    "SELECT COUNT(*) FROM local_opportunities WHERE status = 'ACTIVE' "
                    "AND date(verification_expires_at) <= date('now', '+14 days') AND date(verification_expires_at) >= date('now');"
                ).fetchone()
                if row:
                    expiring_opportunities = row[0]
            except Exception:
                pass

            # Overdue referrals (> 7 days without update in non-terminal state)
            try:
                row = conn.execute(
                    "SELECT COUNT(*) FROM referrals WHERE status NOT IN "
                    "('REJECTED_BY_BENEFICIARY', 'REJECTED_BY_PROVIDER', 'DROPPED_OUT', 'OUTCOME_VERIFIED') "
                    "AND datetime(updated_at) <= datetime('now', '-7 days');"
                ).fetchone()
                if row:
                    overdue_referrals = row[0]
            except Exception:
                pass

            # Pending outcome verifications
            try:
                row = conn.execute(
                    "SELECT COUNT(*) FROM referrals WHERE outcome_reported_at IS NOT NULL "
                    "AND outcome_verified_at IS NULL;"
                ).fetchone()
                if row:
                    pending_outcome_verifications = row[0]
            except Exception:
                pass
    except Exception:
        db_connected = 0

    with _lock:
        total_requests = sum(_http_requests_total.values())
        auth_errors = sum(_auth_errors_total.values())
        server_errors = sum(_server_errors_total.values())
        suppression_events = _cell_suppression_events

    return {
        "uptime_seconds": uptime_seconds,
        "database_connected": db_connected,
        "total_requests": total_requests,
        "auth_errors": auth_errors,
        "server_errors": server_errors,
        "cell_suppression_events": suppression_events,
        "active_opportunities_expiring_14d": expiring_opportunities,
        "overdue_referrals_count": overdue_referrals,
        "pending_outcome_verifications_count": pending_outcome_verifications,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def generate_prometheus_metrics() -> str:
    """Generates Prometheus / OpenMetrics format text."""
    ops = get_operational_metrics()
    lines = [
        "# HELP jeevanmitra_uptime_seconds Total service uptime in seconds",
        "# TYPE jeevanmitra_uptime_seconds counter",
        f"jeevanmitra_uptime_seconds {ops['uptime_seconds']}",
        "",
        "# HELP jeevanmitra_db_connected Database connectivity status (1=connected, 0=disconnected)",
        "# TYPE jeevanmitra_db_connected gauge",
        f"jeevanmitra_db_connected {ops['database_connected']}",
        "",
        "# HELP jeevanmitra_planning_suppressed_cells_total Total privacy cell suppression events (k < 5)",
        "# TYPE jeevanmitra_planning_suppressed_cells_total counter",
        f"jeevanmitra_planning_suppressed_cells_total {ops['cell_suppression_events']}",
        "",
        "# HELP jeevanmitra_active_opportunities_expiring_soon Active verified opportunities expiring in <= 14 days",
        "# TYPE jeevanmitra_active_opportunities_expiring_soon gauge",
        f"jeevanmitra_active_opportunities_expiring_soon {ops['active_opportunities_expiring_14d']}",
        "",
        "# HELP jeevanmitra_overdue_referrals Referrals without updates for > 7 days in active stages",
        "# TYPE jeevanmitra_overdue_referrals gauge",
        f"jeevanmitra_overdue_referrals {ops['overdue_referrals_count']}",
        "",
        "# HELP jeevanmitra_pending_outcome_verifications Referrals with reported outcomes awaiting verification",
        "# TYPE jeevanmitra_pending_outcome_verifications gauge",
        f"jeevanmitra_pending_outcome_verifications {ops['pending_outcome_verifications_count']}",
        "",
        "# HELP jeevanmitra_http_requests_total Total HTTP requests handled",
        "# TYPE jeevanmitra_http_requests_total counter",
    ]

    with _lock:
        for (method, path, status), count in sorted(_http_requests_total.items()):
            lines.append(f'jeevanmitra_http_requests_total{{method="{method}",path="{path}",status="{status}"}} {count}')

        lines.append("")
        lines.append("# HELP jeevanmitra_http_auth_errors_total Total HTTP 401/403 authorization failures")
        lines.append("# TYPE jeevanmitra_http_auth_errors_total counter")
        for status, count in sorted(_auth_errors_total.items()):
            lines.append(f'jeevanmitra_http_auth_errors_total{{status="{status}"}} {count}')

        lines.append("")
        lines.append("# HELP jeevanmitra_http_server_errors_total Total HTTP 5xx internal server errors")
        lines.append("# TYPE jeevanmitra_http_server_errors_total counter")
        for status, count in sorted(_server_errors_total.items()):
            lines.append(f'jeevanmitra_http_server_errors_total{{status="{status}"}} {count}')

    return "\n".join(lines) + "\n"
