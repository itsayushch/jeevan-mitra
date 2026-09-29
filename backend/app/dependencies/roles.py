import hmac
from fastapi import Header, HTTPException, Depends
from typing import Optional
from app.config import settings
from app.dependencies.auth import Actor, get_current_actor


class PlanningActor:
    """
    Authenticated actor for district-planning routes.

    Roles are derived only from credentials verified against server-side
    secrets (settings.ADMIN_API_KEY / settings.OFFICER_API_KEY /
    settings.WORKER_API_KEY). Unlike the legacy X-Worker-API-Key prefix
    conventions, no role is ever inferred from the shape of the key itself.
    """

    def __init__(
        self,
        actor_id: str,
        actor_role: str,
        actor_name: str,
        district: Optional[str] = None,
    ):
        self.actor_id = actor_id
        self.actor_role = actor_role
        self.actor_name = actor_name
        self.district = district

    def is_planning_officer(self) -> bool:
        return self.actor_role in ("district_officer", "admin")


def get_planning_actor(
    x_worker_api_key: Optional[str] = Header(None, alias="X-Worker-API-Key"),
    x_officer_api_key: Optional[str] = Header(None, alias="X-Officer-API-Key"),
    x_admin_api_key: Optional[str] = Header(None, alias="X-Admin-API-Key"),
    current_actor: Actor = Depends(get_current_actor),
) -> PlanningActor:
    """
    Resolves the caller for planning endpoints by checking presented
    credentials against configured secrets, in priority order:
    admin -> district_officer -> field_worker -> anonymous.
    """
    if x_admin_api_key and settings.ADMIN_API_KEY and hmac.compare_digest(x_admin_api_key, settings.ADMIN_API_KEY):
        return PlanningActor(
            actor_id="admin",
            actor_role="admin",
            actor_name="District Administrator",
        )

    if x_officer_api_key and any(
        key and hmac.compare_digest(x_officer_api_key, key)
        for key in (settings.DISTRICT_OFFICER_API_KEY, settings.OFFICER_API_KEY)
    ):
        return PlanningActor(
            actor_id=settings.OFFICER_ID or "officer_01",
            actor_role="district_officer",
            actor_name=settings.OFFICER_NAME or "District Planning Officer",
            district=settings.OFFICER_DISTRICT or None,
        )

    # Preserve main's configured staff credentials and its X-Worker-API-Key contract.
    if current_actor.is_staff():
        return PlanningActor(
            actor_id=current_actor.actor_id,
            actor_role=current_actor.actor_role,
            actor_name=current_actor.actor_name,
            district=settings.OFFICER_DISTRICT or None,
        )

    return PlanningActor(
        actor_id="anonymous",
        actor_role="anonymous",
        actor_name="Guest",
    )


def require_district_officer_or_admin(
    actor: PlanningActor = Depends(get_planning_actor),
) -> PlanningActor:
    """Real role check: only district_officer or admin may access planning data."""
    if not actor.is_planning_officer():
        raise HTTPException(
            status_code=403,
            detail={
                "error": "FORBIDDEN_ROLE",
                "message": "District planning data requires district_officer or admin role.",
                "current_role": actor.actor_role,
            },
        )
    return actor


def enforce_district_scope(actor: PlanningActor, district: str) -> None:
    """
    District scoping: a district_officer may only read data for their own
    district (settings.OFFICER_DISTRICT). Admins are unrestricted.
    Fails closed: an officer without a configured district is denied.
    """
    if actor.actor_role == "admin":
        return
    if not actor.district:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "DISTRICT_SCOPE_UNCONFIGURED",
                "message": "Officer district scope is not configured; access denied.",
            },
        )
    if actor.district.strip().lower() != district.strip().lower():
        raise HTTPException(
            status_code=403,
            detail={
                "error": "DISTRICT_SCOPE_VIOLATION",
                "message": f"Officer scoped to '{actor.district}' cannot access district '{district}'.",
                "officer_district": actor.district,
                "requested_district": district,
            },
        )
