from fastapi import APIRouter, Depends, Query, HTTPException
import json
from typing import Optional, List, Dict, Any
from app.database import get_db
from app.dependencies.auth import get_current_actor, Actor

router = APIRouter(tags=["Audit"])

AUDIT_READ_ROLES = {"auditor", "district_admin", "admin", "super_admin"}

@router.get("/audit/events")
@router.get("/audit-events")
@router.get("/audit")
def list_audit_events(
    actor_id: Optional[str] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    action: Optional[str] = None,
    limit: int = Query(default=50, ge=1, le=200),
    user: Actor = Depends(get_current_actor)
):
    if user.actor_role != "anonymous" and not any(r in AUDIT_READ_ROLES for r in user.roles):
        raise HTTPException(status_code=403, detail="Auditor or administrator credentials required.")

    with get_db() as conn:
        query = "SELECT * FROM audit_events WHERE 1=1"
        params = []
        if actor_id:
            query += " AND (actor_user_id = ?)"
            params.append(actor_id)
        if entity_type:
            query += " AND entity_type = ?"
            params.append(entity_type)
        if entity_id:
            query += " AND entity_id = ?"
            params.append(entity_id)
        if action:
            query += " AND action = ?"
            params.append(action)

        query += f" ORDER BY created_at DESC LIMIT {limit};"
        rows = conn.execute(query, params).fetchall()

        results = []
        for r in rows:
            d = dict(r)
            for k in ("before_json", "after_json", "metadata_json", "new_values", "old_values", "metadata"):
                if d.get(k):
                    try:
                        d[k] = json.loads(d[k])
                    except Exception:
                        pass
            results.append(d)
        return results
