from fastapi import Header, HTTPException, Depends, Request
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
    token = x_session_token or x_session_id

    # 1. Staff authentication via worker API key
    if x_worker_api_key:
        if settings.WORKER_API_KEY and x_worker_api_key == settings.WORKER_API_KEY:
            return Actor(
                actor_id=settings.WORKER_ID or "worker_01",
                actor_role="field_worker",
                actor_name=settings.WORKER_NAME or "Field Worker",
                session_id=token,
                beneficiary_id=x_beneficiary_id
            )
        elif x_worker_api_key.startswith("admin-"):
            return Actor(
                actor_id="admin_01",
                actor_role="admin",
                actor_name="District Administrator",
                session_id=token,
                beneficiary_id=x_beneficiary_id
            )
        elif x_worker_api_key.startswith("counselor-"):
            return Actor(
                actor_id=x_worker_api_key.replace("-", "_"),
                actor_role="counselor",
                actor_name="Career Counselor",
                session_id=token,
                beneficiary_id=x_beneficiary_id
            )

    # 2. Check token in anonymous_sessions table
    token = x_session_token or x_session_id
    if token:
        with get_db() as conn:
            sess = conn.execute("""
                SELECT * FROM anonymous_sessions
                WHERE session_token = ? OR id = ?;
            """, (token, token)).fetchone()

            if sess:
                return Actor(
                    actor_id=sess["id"],
                    actor_role=sess["owner_type"],
                    actor_name="Guest Beneficiary",
                    session_id=sess["id"],
                    beneficiary_id=sess["owner_id"]
                )

    # 3. Fallback to explicit beneficiary ID if provided
    if x_beneficiary_id:
        return Actor(
            actor_id=x_beneficiary_id,
            actor_role="beneficiary",
            actor_name="Beneficiary",
            beneficiary_id=x_beneficiary_id
        )

    # 4. Anonymous Guest fallback
    guest_id = token or "guest_anonymous"
    return Actor(
        actor_id=guest_id,
        actor_role="anonymous",
        actor_name="Guest Beneficiary",
        session_id=token
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
