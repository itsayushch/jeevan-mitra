import uuid
import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from sqlite3 import Connection
from app.utils.logger import logger

ALLOWED_ANALYTICS_EVENTS = {
    "locale.selected",
    "locale.voice_unavailable",
    "recommendation.explanation_viewed",
    "recommendation.explanation_played",
    "opportunity_submission.mode_selected",
    "opportunity_submission.submitted",
    "opportunity_submission.validation_failed",
    "opportunity_submission.staff_reviewed"
}

FORBIDDEN_METADATA_KEYS = {
    "text", "raw_text", "normalized_text", "transcript", "notes", "review_notes",
    "comment", "name", "phone", "email", "address", "content", "reason"
}

class AnalyticsService:
    @staticmethod
    def sanitize_metadata(metadata: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Strips any sensitive profile, note, text, or transcript fields.
        Permits only operational metrics (counts, lengths, flags, status codes).
        """
        if not metadata or not isinstance(metadata, dict):
            return {}

        sanitized = {}
        for k, v in metadata.items():
            k_lower = str(k).lower()
            if any(forbidden in k_lower for forbidden in FORBIDDEN_METADATA_KEYS):
                continue
            if isinstance(v, (int, float, bool, str)) and len(str(v)) <= 100:
                sanitized[k] = v
        return sanitized

    @classmethod
    def record_event(
        cls,
        conn: Connection,
        event_name: str,
        actor_type: str = "beneficiary",
        district_id: Optional[str] = None,
        locale: Optional[str] = "en",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Records a privacy-safe, non-sensitive operational analytics telemetry event.
        Guarantees that raw user text, full transcripts, or private notes are never recorded.
        """
        if event_name not in ALLOWED_ANALYTICS_EVENTS:
            logger.debug(f"Ignoring unrecognized analytics event: {event_name}")
            return None

        event_id = f"evt_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).isoformat()
        clean_meta = cls.sanitize_metadata(metadata)

        conn.execute("""
            INSERT INTO analytics_events (
                id, event_name, actor_type, district_id, locale, metadata_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?);
        """, (
            event_id,
            event_name,
            actor_type,
            district_id,
            locale or "en",
            json.dumps(clean_meta, ensure_ascii=False),
            now
        ))
        return event_id

    @classmethod
    def get_aggregated_metrics(
        cls,
        conn: Connection,
        district_id: Optional[str] = None,
        k_threshold: int = 5
    ) -> Dict[str, Any]:
        """
        Aggregates operational metrics with k-anonymity privacy protection:
        any count below k_threshold is suppressed to protect small groups.
        """
        params = []
        where_clause = ""
        if district_id:
            where_clause = "WHERE district_id = ?"
            params.append(district_id)

        rows = conn.execute(f"""
            SELECT event_name, locale, COUNT(*) as cnt
            FROM analytics_events
            {where_clause}
            GROUP BY event_name, locale;
        """, params).fetchall()

        events_summary: Dict[str, Any] = {}
        for r in rows:
            ev = r["event_name"]
            loc = r["locale"]
            count = r["cnt"]
            if ev not in events_summary:
                events_summary[ev] = {}
            # Apply k-anonymity privacy suppression
            events_summary[ev][loc] = count if count >= k_threshold else "<SUPPRESSED_BELOW_K>"

        return {
            "district_id": district_id or "ALL",
            "k_threshold": k_threshold,
            "metrics": events_summary
        }
