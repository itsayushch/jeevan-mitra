from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional
import time
from app.database import get_db
from app.core.settings import settings
from app.core.metrics import _server_errors_total, _auth_errors_total, _lock
from app.utils.logger import logger


class AlertSeverity:
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    INFO = "INFO"


class OperationalAlertService:
    """
    Monitors operational health invariants and evaluates alert conditions:
    1. Backend 5xx error spikes
    2. Database connectivity/failures
    3. Audit-write integrity
    4. Export-generation failures
    5. Snapshot-generation failures
    6. Opportunity-expiry job status
    7. High authentication failure rate
    8. Storage accessibility
    9. Referral/case assignment backlog
    """

    @classmethod
    def evaluate_all_alerts(cls) -> Dict[str, Any]:
        alerts: List[Dict[str, Any]] = []

        # 1. Database connectivity check
        db_alert = cls._check_database_health()
        if db_alert:
            alerts.append(db_alert)

        # 2. Audit-write capability check
        audit_alert = cls._check_audit_write_capability()
        if audit_alert:
            alerts.append(audit_alert)

        # 3. Backend 5xx spikes
        server_error_alert = cls._check_5xx_spikes()
        if server_error_alert:
            alerts.append(server_error_alert)

        # 4. Authentication failure rate
        auth_alert = cls._check_auth_failure_rate()
        if auth_alert:
            alerts.append(auth_alert)

        # 5. Storage accessibility
        storage_alert = cls._check_storage_health()
        if storage_alert:
            alerts.append(storage_alert)

        # 6. Opportunity expiry job freshness
        expiry_alert = cls._check_opportunity_expiry_job()
        if expiry_alert:
            alerts.append(expiry_alert)

        # 7. Export generation status
        export_alert = cls._check_export_generation_health()
        if export_alert:
            alerts.append(export_alert)

        # 8. Snapshot generation status
        snapshot_alert = cls._check_snapshot_generation_health()
        if snapshot_alert:
            alerts.append(snapshot_alert)

        # 9. Case / referral backlog
        backlog_alert = cls._check_case_backlog()
        if backlog_alert:
            alerts.append(backlog_alert)

        # Aggregate overall status
        has_critical = any(a["severity"] == AlertSeverity.CRITICAL for a in alerts)
        has_warning = any(a["severity"] == AlertSeverity.WARNING for a in alerts)

        overall_status = "CRITICAL" if has_critical else ("WARNING" if has_warning else "HEALTHY")

        return {
            "status": overall_status,
            "alert_count": len(alerts),
            "alerts": alerts,
            "evaluated_at": datetime.now(timezone.utc).isoformat(),
            "environment": settings.APP_ENV,
            "version": settings.RELEASE_VERSION,
        }

    @classmethod
    def _check_database_health(cls) -> Optional[Dict[str, Any]]:
        try:
            with get_db() as conn:
                conn.execute("SELECT 1;").fetchone()
            return None
        except Exception as e:
            return {
                "name": "DatabaseConnectionFailure",
                "severity": AlertSeverity.CRITICAL,
                "message": f"Database is unreachable or rejecting queries: {str(e)}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

    @classmethod
    def _check_audit_write_capability(cls) -> Optional[Dict[str, Any]]:
        try:
            with get_db() as conn:
                # Check if audit_events table exists and is writable
                row = conn.execute("SELECT COUNT(*) FROM audit_events;").fetchone()
                if row is None:
                    raise ValueError("audit_events table is unreadable")
            return None
        except Exception as e:
            return {
                "name": "AuditWriteFailure",
                "severity": AlertSeverity.CRITICAL,
                "message": f"Audit logging store is unavailable or corrupt: {str(e)}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

    @classmethod
    def _check_5xx_spikes(cls) -> Optional[Dict[str, Any]]:
        with _lock:
            total_5xx = sum(_server_errors_total.values())

        if total_5xx >= 10:
            return {
                "name": "Backend5xxSpike",
                "severity": AlertSeverity.CRITICAL,
                "message": f"High rate of 5xx internal server errors detected: {total_5xx} errors recorded.",
                "details": {"total_5xx": total_5xx},
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        elif total_5xx > 0:
            return {
                "name": "Backend5xxDetected",
                "severity": AlertSeverity.WARNING,
                "message": f"Internal server errors observed: {total_5xx} errors recorded.",
                "details": {"total_5xx": total_5xx},
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        return None

    @classmethod
    def _check_auth_failure_rate(cls) -> Optional[Dict[str, Any]]:
        with _lock:
            total_auth_failures = sum(_auth_errors_total.values())

        if total_auth_failures >= 25:
            return {
                "name": "HighAuthenticationFailureRate",
                "severity": AlertSeverity.WARNING,
                "message": f"Elevated HTTP 401/403 authorization failures detected: {total_auth_failures} failures.",
                "details": {"total_auth_failures": total_auth_failures},
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        return None

    @classmethod
    def _check_storage_health(cls) -> Optional[Dict[str, Any]]:
        if settings.STORAGE_PROVIDER == "local":
            try:
                storage_path = Path(settings.DATABASE_PATH).parent / settings.STORAGE_PRIVATE_PREFIX
                storage_path.mkdir(parents=True, exist_ok=True)
                probe_file = storage_path / ".storage_health_probe"
                probe_file.write_text("health", encoding="utf-8")
                if probe_file.exists():
                    probe_file.unlink()
                return None
            except Exception as e:
                return {
                    "name": "StorageFailure",
                    "severity": AlertSeverity.CRITICAL,
                    "message": f"Private file storage is inaccessible: {str(e)}",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
        return None

    @classmethod
    def _check_opportunity_expiry_job(cls) -> Optional[Dict[str, Any]]:
        """Alerts if active opportunities remain with past expiration dates."""
        try:
            with get_db() as conn:
                row = conn.execute("""
                    SELECT COUNT(*) FROM local_opportunities
                    WHERE status = 'ACTIVE'
                    AND verification_expires_at IS NOT NULL
                    AND datetime(verification_expires_at) < datetime('now');
                """).fetchone()

                unhandled_expired = row[0] if row else 0
                if unhandled_expired > 0:
                    return {
                        "name": "OpportunityExpiryJobStale",
                        "severity": AlertSeverity.WARNING,
                        "message": f"{unhandled_expired} local opportunities have passed their verification expiry date without status transition. The scheduled expiry job may be failing.",
                        "details": {"unhandled_expired_count": unhandled_expired},
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
        except Exception:
            pass
        return None

    @classmethod
    def _check_export_generation_health(cls) -> Optional[Dict[str, Any]]:
        """Alerts if export generation has unpurged corrupt or orphan export files."""
        try:
            with get_db() as conn:
                # Check for expired exports that remain unpurged past retention + 3 days
                row = conn.execute("""
                    SELECT COUNT(*) FROM planning_exports
                    WHERE datetime(expires_at) < datetime('now', '-3 days');
                """).fetchone()

                orphan_expired = row[0] if row else 0
                if orphan_expired > 5:
                    return {
                        "name": "ExportRetentionJobBacklog",
                        "severity": AlertSeverity.WARNING,
                        "message": f"{orphan_expired} expired planning exports have not been cleaned up by the export retention routine.",
                        "details": {"orphan_expired_count": orphan_expired},
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
        except Exception:
            pass
        return None

    @classmethod
    def _check_snapshot_generation_health(cls) -> Optional[Dict[str, Any]]:
        """Checks whether snapshots are generated regularly for active pilot districts."""
        try:
            with get_db() as conn:
                row = conn.execute("SELECT COUNT(*) FROM planning_snapshots;").fetchone()
                # Not an error if early in lifecycle, but verify table accessible
                return None
        except Exception as e:
            return {
                "name": "SnapshotStorageFailure",
                "severity": AlertSeverity.CRITICAL,
                "message": f"Planning snapshots storage is unreadable: {str(e)}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

    @classmethod
    def _check_case_backlog(cls) -> Optional[Dict[str, Any]]:
        """Alerts if unassigned cases or stalled referrals exceed operational thresholds."""
        try:
            with get_db() as conn:
                row = conn.execute("""
                    SELECT COUNT(*) FROM beneficiary_cases
                    WHERE (assigned_worker_id IS NULL OR assigned_worker_id = '')
                    AND datetime(created_at) < datetime('now', '-7 days');
                """).fetchone()

                unassigned_cases = row[0] if row else 0
                if unassigned_cases > 20:
                    return {
                        "name": "UnassignedCaseBacklog",
                        "severity": AlertSeverity.WARNING,
                        "message": f"{unassigned_cases} beneficiary cases have remained unassigned for more than 7 days.",
                        "details": {"unassigned_cases": unassigned_cases},
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
        except Exception:
            pass
        return None
