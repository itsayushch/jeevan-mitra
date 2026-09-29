import uuid
import sqlite3
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from app.utils.logger import logger


def current_period_label(now: Optional[datetime] = None) -> str:
    """
    Returns the current Indian financial-year label (FY April-March),
    e.g. 'FY 2026-27'. Used as the default demand-record period.
    """
    now = now or datetime.now(timezone.utc)
    year = now.year if now.month >= 4 else now.year - 1
    return f"FY {year}-{(year + 1) % 100:02d}"


class DemandRecordService:
    """
    Writes anonymised district-planning demand records.

    A demand record captures ONLY: qualification interest, district, block,
    mobility radius, work preference, timestamp, period, and whether a
    Verified Match existed. It contains no name, contact details, or free
    text, and lives in its own table separate from PII tables.

    Records are written only when the beneficiary has granted analytics
    consent (consent_records.consent_type = 'analytics', status =
    'granted'). When no beneficiary/session identifier is available, consent
    cannot be verified and nothing is written (privacy by default).
    """

    @staticmethod
    def has_analytics_consent(
        conn: sqlite3.Connection,
        beneficiary_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> bool:
        if not beneficiary_id and not session_id:
            return False
        row = conn.execute("""
            SELECT status FROM consent_records
            WHERE consent_type = 'analytics'
              AND (beneficiary_id = ? OR session_id = ?)
            ORDER BY timestamp DESC, rowid DESC
            LIMIT 1;
        """, (beneficiary_id or "", session_id or "")).fetchone()
        return row is not None and row['status'] == 'granted'

    @staticmethod
    def record_demand(
        conn: sqlite3.Connection,
        qualification_id: str,
        district: str,
        block: str,
        mobility_radius_km: Optional[float] = None,
        work_preference: Optional[str] = None,
        had_verified_match: bool = False,
        period: Optional[str] = None,
        beneficiary_id: Optional[str] = None,
        session_id: Optional[str] = None,
        created_at: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Writes one anonymised demand record after verifying analytics consent.
        Returns the stored record, or None when consent is missing / not
        verifiable. The record carries only an opaque random id - no join key
        back to any PII table.
        """
        if not DemandRecordService.has_analytics_consent(conn, beneficiary_id, session_id):
            logger.debug(
                "Skipping demand record: no analytics consent for beneficiary=%s session=%s",
                beneficiary_id, session_id,
            )
            return None

        now = created_at or datetime.now(timezone.utc).isoformat()
        record_id = f"dem_{uuid.uuid4().hex[:12]}"
        period = period or current_period_label()

        conn.execute("""
            INSERT INTO demand_records (
                id, qualification_id, district, block,
                mobility_radius_km, work_preference, had_verified_match, period, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            record_id, qualification_id, district, block,
            mobility_radius_km, work_preference, 1 if had_verified_match else 0,
            period, now,
        ))

        return dict(conn.execute(
            "SELECT * FROM demand_records WHERE id = ?;", (record_id,)
        ).fetchone())
