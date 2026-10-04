import uuid
import sqlite3
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from app.models import JourneyState, JourneyResponse, JourneyConsentRequest, JourneyStartRequest
from app.utils.audit_events import log_audit_event
from app.utils.errors import NotFoundException, ValidationException
from app.services.session_service import SessionService
from app.services.consent_service import ConsentService
from app.services.recommendation_service import RecommendationService
from app.services.referral_service import ReferralService
from app.services.export_service import ExportService

class JourneyService:

    @staticmethod
    def _to_response(row: sqlite3.Row) -> JourneyResponse:
        return JourneyResponse(
            id=row["id"],
            session_id=row["session_id"],
            actor_id=row["actor_id"],
            actor_role=row["actor_role"],
            state=JourneyState(row["state"]),
            ai_processing_consent=bool(row["ai_processing_consent"]),
            storage_consent=bool(row["storage_consent"]),
            referral_consent=bool(row["referral_consent"]),
            profile_confirmed=bool(row["profile_confirmed"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )

    @staticmethod
    def _validate_ownership(conn: sqlite3.Connection, journey_id: str, actor_id: Optional[str]) -> Dict[str, Any]:
        row = conn.execute("SELECT * FROM journeys WHERE id = ?;", (journey_id,)).fetchone()
        if not row:
            raise NotFoundException("Journey not found")
        if row["state"] == JourneyState.DELETED.value:
            raise ValidationException("Journey has been deleted")
        if not actor_id or not row["actor_id"] or row["actor_id"] != actor_id:
            raise ValidationException("Unauthorized to access this journey")
        return dict(row)

    @staticmethod
    def start_journey(conn: sqlite3.Connection, req: JourneyStartRequest) -> JourneyResponse:
        session_id = f"sess_{uuid.uuid4().hex[:12]}"
        journey_id = f"journey_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).isoformat()

        conn.execute("""
            INSERT INTO interview_sessions (
                id, session_id, channel, status, current_question_index,
                last_question, language, transcript_history, created_at, updated_at
            ) VALUES (?, ?, 'web_app', 'not_started', 0, NULL, 'hi', '[]', ?, ?);
        """, (session_id, req.actor_id, now, now))
        
        conn.execute("""
            INSERT INTO journeys (id, session_id, actor_id, actor_role, state, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?);
        """, (journey_id, session_id, req.actor_id, req.actor_role, JourneyState.CREATED.value, now, now))
        
        row = conn.execute("SELECT * FROM journeys WHERE id = ?;", (journey_id,)).fetchone()
        return JourneyService._to_response(row)
        
    @staticmethod
    def get_journey(conn: sqlite3.Connection, journey_id: str, actor_id: Optional[str] = None) -> JourneyResponse:
        row_dict = JourneyService._validate_ownership(conn, journey_id, actor_id)
        return JourneyService._to_response(row_dict) # type: ignore

    @staticmethod
    def update_consent(conn: sqlite3.Connection, journey_id: str, req: JourneyConsentRequest, actor_id: Optional[str] = None) -> JourneyResponse:
        row_dict = JourneyService._validate_ownership(conn, journey_id, actor_id)
        now = datetime.now(timezone.utc).isoformat()
        new_state = row_dict["state"]
        
        # simple state machine progression logic if needed
        if row_dict["state"] in [JourneyState.CREATED.value, JourneyState.AWAITING_CONSENT.value]:
             if req.ai_processing_consent:
                 new_state = JourneyState.COLLECTING_PROFILE.value
        
        conn.execute("""
            UPDATE journeys 
            SET ai_processing_consent = ?, storage_consent = ?, referral_consent = ?, state = ?, updated_at = ?
            WHERE id = ?;
        """, (int(req.ai_processing_consent), int(req.storage_consent), int(req.referral_consent), new_state, now, journey_id))
        
        row = conn.execute("SELECT * FROM journeys WHERE id = ?;", (journey_id,)).fetchone()
        return JourneyService._to_response(row)

    @staticmethod
    def respond(conn: sqlite3.Connection, journey_id: str, message: str, language: str, actor_id: Optional[str] = None) -> Dict[str, Any]:
        row_dict = JourneyService._validate_ownership(conn, journey_id, actor_id)
        if not row_dict["ai_processing_consent"]:
            raise ValidationException("AI processing consent is required to process responses")
        
        # Simulate AI response using orchestrator/bot logic. Here we just return a stub for simplicity or integrate actual AI.
        return {"response": "AI Response stub", "journey_id": journey_id}

    @staticmethod
    def confirm_profile(conn: sqlite3.Connection, journey_id: str, confirm: bool, actor_id: Optional[str] = None) -> JourneyResponse:
        row_dict = JourneyService._validate_ownership(conn, journey_id, actor_id)
        if not row_dict["storage_consent"]:
            raise ValidationException("Storage consent is required to confirm profile")
            
        now = datetime.now(timezone.utc).isoformat()
        new_state = JourneyState.READY_FOR_RECOMMENDATIONS.value if confirm else JourneyState.CLARIFICATION_REQUIRED.value
        
        conn.execute("""
            UPDATE journeys 
            SET profile_confirmed = ?, state = ?, updated_at = ?
            WHERE id = ?;
        """, (int(confirm), new_state, now, journey_id))
        
        row = conn.execute("SELECT * FROM journeys WHERE id = ?;", (journey_id,)).fetchone()
        return JourneyService._to_response(row)

    @staticmethod
    def generate_recommendations(conn: sqlite3.Connection, journey_id: str, actor_id: Optional[str] = None) -> Dict[str, Any]:
        row_dict = JourneyService._validate_ownership(conn, journey_id, actor_id)
        if not row_dict["profile_confirmed"]:
            raise ValidationException("Profile must be confirmed before generating recommendations")
        
        now = datetime.now(timezone.utc).isoformat()
        conn.execute("UPDATE journeys SET state = ?, updated_at = ? WHERE id = ?;", (JourneyState.RECOMMENDATIONS_READY.value, now, journey_id))
        return {"status": "Recommendations generated"}

    @staticmethod
    def request_referral(conn: sqlite3.Connection, journey_id: str, actor_id: Optional[str] = None) -> Dict[str, Any]:
        row_dict = JourneyService._validate_ownership(conn, journey_id, actor_id)
        if not row_dict["referral_consent"]:
            raise ValidationException("Referral consent is required")
        if row_dict["state"] != JourneyState.RECOMMENDATIONS_READY.value:
            raise ValidationException("Recommendations must be ready before requesting referral")
            
        now = datetime.now(timezone.utc).isoformat()
        conn.execute("UPDATE journeys SET state = ?, updated_at = ? WHERE id = ?;", (JourneyState.REFERRAL_REQUESTED.value, now, journey_id))
        return {"status": "Referral requested"}
        
    @staticmethod
    def get_summary(conn: sqlite3.Connection, journey_id: str, actor_id: Optional[str] = None) -> Dict[str, Any]:
        row_dict = JourneyService._validate_ownership(conn, journey_id, actor_id)
        return {"summary": "Journey summary stub"}

    @staticmethod
    def delete_journey(conn: sqlite3.Connection, journey_id: str, actor_id: Optional[str] = None) -> Dict[str, Any]:
        row_dict = JourneyService._validate_ownership(conn, journey_id, actor_id)
        now = datetime.now(timezone.utc).isoformat()
        conn.execute("UPDATE journeys SET state = ?, updated_at = ? WHERE id = ?;", (JourneyState.DELETED.value, now, journey_id))
        return {"status": "deleted"}

