import uuid
import json
import sqlite3
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from app.dependencies.consent import verify_consent
from app.services.recommendation_service import RecommendationService
from app.utils.audit_events import log_audit_event
from app.utils.errors import EntityNotFoundException

class ExportService:
    DISCLAIMER_TEXT = (
        "This summary is an informational guidance advisory generated under the PM-AJAY Livelihood "
        "Matching framework. It does not constitute a legal entitlement, admission guarantee, or scheme approval."
    )

    @staticmethod
    def generate_summary_export(
        conn: sqlite3.Connection,
        interview_id: Optional[str] = None,
        beneficiary_id: Optional[str] = None,
        actor_id: str = "system"
    ) -> Dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        export_id = f"exp_{uuid.uuid4().hex[:10]}"

        # 1. Mandatory consent check for export
        verify_consent(conn, "export_summary", beneficiary_id, interview_id)

        # 2. Extract only user-confirmed profile fields
        confirmed_fields: Dict[str, Any] = {}
        if interview_id:
            rows = conn.execute("""
                SELECT field_name, field_value FROM profile_field_values
                WHERE interview_id = ? AND user_confirmed = 1;
            """, (interview_id,)).fetchall()
            for r in rows:
                val = r["field_value"]
                try:
                    confirmed_fields[r["field_name"]] = json.loads(val)
                except Exception:
                    confirmed_fields[r["field_name"]] = val

        if not confirmed_fields and beneficiary_id:
            rows = conn.execute("""
                SELECT field_name, field_value FROM profile_answers
                WHERE beneficiary_id = ? AND confirmation_status = 'confirmed';
            """, (beneficiary_id,)).fetchall()
            for r in rows:
                val = r["field_value"]
                try:
                    confirmed_fields[r["field_name"]] = json.loads(val)
                except Exception:
                    confirmed_fields[r["field_name"]] = val

        # 3. Extract recommendations
        if interview_id:
            recs = RecommendationService.get_recommendations_for_interview(conn, interview_id)
        elif beneficiary_id:
            rec_rows = conn.execute("""
                SELECT id FROM recommendations
                WHERE beneficiary_id = ?
                ORDER BY rank ASC;
            """, (beneficiary_id,)).fetchall()
            recs = [RecommendationService.get_recommendation_by_id(conn, r["id"]) for r in rec_rows]
        else:
            recs = []

        # 4. Filter out any sensitive information (no raw transcripts, no Aadhaar, no certificates)
        safe_profile = {
            k: v for k, v in confirmed_fields.items()
            if k not in ["raw_audio", "aadhaar", "bank_account", "caste_certificate", "full_transcript"]
        }

        # 5. Record export audit
        conn.execute("""
            INSERT INTO export_audits (
                id, interview_id, beneficiary_id, exported_by, export_type, consent_verified, metadata, created_at
            ) VALUES (?, ?, ?, ?, 'summary', 1, ?, ?);
        """, (
            export_id, interview_id, beneficiary_id, actor_id,
            json.dumps({"recommendations_count": len(recs), "confirmed_fields_count": len(safe_profile)}),
            now
        ))

        log_audit_event(
            conn=conn,
            actor_id=actor_id,
            actor_name="Beneficiary Export",
            actor_role="beneficiary",
            action="PROFILE_SUMMARY_EXPORTED",
            entity_type="export_audit",
            entity_id=export_id,
            metadata={"interview_id": interview_id, "beneficiary_id": beneficiary_id}
        )

        return {
            "export_id": export_id,
            "interview_id": interview_id,
            "beneficiary_id": beneficiary_id,
            "confirmed_profile": safe_profile,
            "recommendations": recs,
            "disclaimer": ExportService.DISCLAIMER_TEXT,
            "generated_at": now
        }
