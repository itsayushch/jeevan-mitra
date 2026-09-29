import uuid
import json
import sqlite3
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
from app.models import AnonymousSessionCreate
from app.utils.audit_events import log_audit_event
from app.utils.errors import SessionExpiredOrInvalidException

class SessionService:
    DEFAULT_EXPIRY_HOURS = 24

    @staticmethod
    def create_session(
        conn: sqlite3.Connection,
        data: Optional[AnonymousSessionCreate] = None,
        actor_id: str = "system"
    ) -> Dict[str, Any]:
        session_id = f"sess_{uuid.uuid4().hex[:12]}"
        session_token = f"tok_{uuid.uuid4().hex}"
        now = datetime.now(timezone.utc)
        expires_at = (now + timedelta(hours=SessionService.DEFAULT_EXPIRY_HOURS)).isoformat()

        owner_type = data.owner_type if data and data.owner_type else "anonymous"
        owner_id = data.owner_id if data and data.owner_id else None
        metadata = json.dumps(data.metadata if data and data.metadata else {})

        conn.execute("""
            INSERT INTO anonymous_sessions (
                id, session_token, owner_type, owner_id, expires_at, metadata, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            session_id, session_token, owner_type, owner_id, expires_at,
            metadata, now.isoformat(), now.isoformat()
        ))

        log_audit_event(
            conn=conn,
            actor_id=actor_id,
            actor_name="System / Guest",
            actor_role="anonymous",
            action="SESSION_CREATED",
            entity_type="anonymous_session",
            entity_id=session_id,
            new_values={"owner_type": owner_type, "owner_id": owner_id, "expires_at": expires_at}
        )

        row = conn.execute("SELECT * FROM anonymous_sessions WHERE id = ?;", (session_id,)).fetchone()
        res = dict(row)
        res["session_id"] = res["id"]
        return res

    @staticmethod
    def validate_session(conn: sqlite3.Connection, session_token_or_id: str) -> Dict[str, Any]:
        row = conn.execute("""
            SELECT * FROM anonymous_sessions
            WHERE session_token = ? OR id = ?;
        """, (session_token_or_id, session_token_or_id)).fetchone()

        if not row:
            raise SessionExpiredOrInvalidException("Session does not exist.")

        expires_at = datetime.fromisoformat(row["expires_at"])
        if datetime.now(timezone.utc) > expires_at:
            raise SessionExpiredOrInvalidException("Session has expired. Please start a new session.")

        res = dict(row)
        res["session_id"] = res["id"]
        return res
