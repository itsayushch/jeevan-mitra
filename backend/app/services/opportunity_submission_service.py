import re
import uuid
import unicodedata
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from fastapi import HTTPException
from sqlite3 import Connection

from app.schemas.opportunities import OpportunitySubmissionCreate, OpportunitySubmissionReview
from app.schemas.locale import SupportedLocale, resolve_locale
from app.utils.audit_events import log_audit_event
from app.utils.logger import logger

class OpportunitySubmissionService:
    @staticmethod
    def normalize_text(text: str) -> str:
        """
        Normalizes input text with Unicode NFC and collapses whitespace.
        """
        if not text:
            return ""
        # Unicode normalization
        normalized = unicodedata.normalize("NFC", text)
        # Collapse multiple whitespace characters into a single space and strip
        return re.sub(r"\s+", " ", normalized).strip()

    @classmethod
    def validate_and_normalize(cls, text: str) -> str:
        """
        Validates text length constraints:
        - min: 3 non-whitespace chars
        - max: 1500 characters
        """
        if not text or not text.strip():
            raise HTTPException(
                status_code=400,
                detail={"code": "EMPTY_SUBMISSION", "message": "Submission text cannot be empty or only whitespace."}
            )

        cleaned = cls.normalize_text(text)
        if len(cleaned) < 3:
            raise HTTPException(
                status_code=400,
                detail={"code": "EMPTY_SUBMISSION", "message": "Submission text must be at least 3 characters long."}
            )

        if len(cleaned) > 1500:
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "SUBMISSION_TOO_LONG",
                    "message": f"Submission text exceeds the 1500 character limit (length: {len(cleaned)})."
                }
            )

        return cleaned

    @classmethod
    def create_submission(
        cls,
        conn: Connection,
        data: OpportunitySubmissionCreate,
        user_id: Optional[str] = None,
        actor_name: str = "Anonymous",
        actor_role: str = "guest",
        preferred_language: Optional[str] = None,
        accept_language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Ingests and validates a candidate opportunity submission from text or voice.
        Unified invariant: both input modes share the same validation, normalization,
        and initial status ('SUBMITTED').
        """
        normalized = cls.validate_and_normalize(data.text)
        resolved_loc = resolve_locale(
            explicit_locale=data.locale,
            accept_language=accept_language,
            preferred_language=preferred_language
        )

        sub_id = f"sub_{uuid.uuid4().hex[:10]}"
        now = datetime.now(timezone.utc).isoformat()

        conn.execute("""
            INSERT INTO opportunity_submissions (
                id, submitted_by_user_id, input_mode, raw_text, normalized_text,
                locale, audio_storage_key, transcript_confidence, status,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'SUBMITTED', ?, ?);
        """, (
            sub_id,
            user_id,
            data.input_mode,
            data.text,
            normalized,
            resolved_loc.value,
            data.audio_storage_key,
            data.transcript_confidence,
            now,
            now
        ))

        log_audit_event(
            conn=conn,
            actor_id=user_id or "anonymous",
            actor_name=actor_name,
            actor_role=actor_role,
            action="OPPORTUNITY_SUBMISSION_CREATED",
            entity_type="opportunity_submission",
            entity_id=sub_id,
            metadata={
                "input_mode": data.input_mode,
                "locale": resolved_loc.value,
                "length": len(normalized)
            }
        )

        return cls.get_submission_by_id(conn, sub_id)

    @staticmethod
    def get_submission_by_id(conn: Connection, sub_id: str) -> Dict[str, Any]:
        row = conn.execute("SELECT * FROM opportunity_submissions WHERE id = ?;", (sub_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail=f"Opportunity submission '{sub_id}' not found.")
        return dict(row)

    @staticmethod
    def list_my_submissions(conn: Connection, user_id: str) -> List[Dict[str, Any]]:
        rows = conn.execute("""
            SELECT * FROM opportunity_submissions
            WHERE submitted_by_user_id = ?
            ORDER BY created_at DESC;
        """, (user_id,)).fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def list_all_submissions(
        conn: Connection,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        if status:
            rows = conn.execute("""
                SELECT * FROM opportunity_submissions
                WHERE status = ?
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?;
            """, (status, limit, offset)).fetchall()
        else:
            rows = conn.execute("""
                SELECT * FROM opportunity_submissions
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?;
            """, (limit, offset)).fetchall()
        return [dict(r) for r in rows]

    @classmethod
    def review_submission(
        cls,
        conn: Connection,
        sub_id: str,
        review_data: OpportunitySubmissionReview,
        reviewer_id: str,
        reviewer_name: str,
        reviewer_role: str
    ) -> Dict[str, Any]:
        """
        Staff review workflow: transitions submission status and optionally links to verified opportunity.
        """
        existing = cls.get_submission_by_id(conn, sub_id)
        target_status = review_data.status

        # If linking, ensure linked opportunity exists
        linked_opp_id = review_data.linked_opportunity_id
        if target_status == "LINKED_TO_OPPORTUNITY":
            if not linked_opp_id:
                raise HTTPException(
                    status_code=400,
                    detail="linked_opportunity_id is required when setting status to LINKED_TO_OPPORTUNITY."
                )
            opp_row = conn.execute("SELECT id FROM local_opportunities WHERE id = ?;", (linked_opp_id,)).fetchone()
            if not opp_row:
                raise HTTPException(
                    status_code=400,
                    detail=f"Target opportunity '{linked_opp_id}' does not exist."
                )

        now = datetime.now(timezone.utc).isoformat()
        conn.execute("""
            UPDATE opportunity_submissions
            SET status = ?, linked_opportunity_id = ?, reviewed_by_user_id = ?, review_notes = ?, updated_at = ?
            WHERE id = ?;
        """, (
            target_status,
            linked_opp_id,
            reviewer_id,
            review_data.review_notes or existing.get("review_notes"),
            now,
            sub_id
        ))

        log_audit_event(
            conn=conn,
            actor_id=reviewer_id,
            actor_name=reviewer_name,
            actor_role=reviewer_role,
            action="OPPORTUNITY_SUBMISSION_REVIEWED",
            entity_type="opportunity_submission",
            entity_id=sub_id,
            metadata={
                "previous_status": existing["status"],
                "new_status": target_status,
                "linked_opportunity_id": linked_opp_id
            }
        )

        return cls.get_submission_by_id(conn, sub_id)
