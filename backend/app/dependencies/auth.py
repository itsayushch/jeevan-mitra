from datetime import datetime, timezone
import secrets
from fastapi import Header, HTTPException, Depends
from typing import Optional, Dict, Any
from app.config import settings
from app.database import get_db
from app.utils.errors import UnauthorizedAccessException

class Actor:
    def __init__(
        self,
        actor_id: str,
        actor_role: str,
        actor_name: str,
        session_id: Optional[str] = None,
        beneficiary_id: Optional[str] = None
    ):
        self.actor_id = actor_id
        self.actor_role = actor_role
        self.actor_name = actor_name
        self.session_id = session_id
        self.beneficiary_id = beneficiary_id

    def is_staff(self) -> bool:
        return self.actor_role in ["field_worker", "district_officer", "counselor", "admin"]

def get_current_actor(
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID"),
    x_session_token: Optional[str] = Header(None, alias="X-Session-Token"),
    x_worker_api_key: Optional[str] = Header(None, alias="X-Worker-API-Key"),
    x_beneficiary_id: Optional[str] = Header(None, alias="X-Beneficiary-ID"),
    authorization: Optional[str] = Header(None)
) -> Actor:
    """
    Identifies the caller actor based on worker API keys, session tokens, or guest session IDs.
    """
    configured_staff_keys = (
        (settings.WORKER_API_KEY, "field_worker", settings.WORKER_ID, settings.WORKER_NAME),
        (settings.COUNSELOR_API_KEY, "counselor", "", "Career Counselor"),
        (settings.ADMIN_API_KEY, "admin", "admin", "District Administrator"),
        (settings.DISTRICT_OFFICER_API_KEY, "district_officer", "", "District Officer"),
        (settings.ANALYST_API_KEY, "analyst", "", "District Analyst"),
    )
    if authorization and authorization.startswith("Bearer "):
        try:
            import jwt
            token = authorization.split(" ")[1]
            payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
            return Actor(
                actor_id=payload.get("sub", "unknown"),
                actor_role=payload.get("role", "anonymous"),
                actor_name=payload.get("name", "Authenticated User"),
                session_id=x_session_token
            )
        except Exception:
            pass

    if x_worker_api_key:
        for configured_key, role, actor_id, actor_name in configured_staff_keys:
            if configured_key and secrets.compare_digest(x_worker_api_key, configured_key):
                return Actor(
                    actor_id=actor_id or role,
                    actor_role=role,
                    actor_name=actor_name or role.replace("_", " ").title(),
                    session_id=x_session_token,
                )

    # Session IDs and beneficiary IDs are public identifiers, not credentials.
    if x_session_token:
        with get_db() as conn:
            sess = conn.execute("""
                SELECT * FROM anonymous_sessions
                WHERE session_token = ?;
            """, (x_session_token,)).fetchone()

            if sess:
                expires_at = datetime.fromisoformat(sess["expires_at"])
                if expires_at.tzinfo is None:
                    expires_at = expires_at.replace(tzinfo=timezone.utc)
                if expires_at > datetime.now(timezone.utc):
                    return Actor(
                        actor_id=sess["id"],
                        actor_role=sess["owner_type"],
                        actor_name="Guest Beneficiary",
                        session_id=sess["id"],
                        beneficiary_id=sess["owner_id"]
                    )

    # Invalid or absent credentials are anonymous; protected dependencies reject this actor.
    return Actor(
        actor_id="guest_anonymous",
        actor_role="anonymous",
        actor_name="Guest Beneficiary"
    )

def require_admin_or_worker(actor: Actor = Depends(get_current_actor)) -> Actor:
    if actor.actor_role not in ["field_worker", "district_officer", "admin"]:
        raise UnauthorizedAccessException(
            message="Administrative or field worker credentials required.",
            details={"required_roles": ["field_worker", "district_officer", "admin"], "current_role": actor.actor_role}
        )
    return actor

def require_counselor_or_admin(actor: Actor = Depends(get_current_actor)) -> Actor:
    if actor.actor_role not in ["counselor", "admin", "district_officer"]:
        raise UnauthorizedAccessException(
            message="Counselor or administrator credentials required.",
            details={"required_roles": ["counselor", "admin", "district_officer"], "current_role": actor.actor_role}
        )
    return actor
