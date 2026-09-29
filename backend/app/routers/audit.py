from fastapi import APIRouter, Depends, Query
import json
from typing import Optional, List, Dict, Any
from app.database import get_db
from app.dependencies.auth import require_admin_or_worker, Actor

router = APIRouter(tags=["Audit"])

@router.get("/audit-events")
@router.get("/audit")
def list_audit_events(
    actor_role: Optional[str] = None,
    entity_type: Optional[str] = None,
    action: Optional[str] = None,
    limit: int = Query(default=50, ge=1, le=200)
):
    with get_db() as conn:
        query = "SELECT * FROM audit_events WHERE 1=1"
        params = []
        if actor_role:
            query += " AND actor_role = ?"
            params.append(actor_role)
        if entity_type:
            query += " AND entity_type = ?"
            params.append(entity_type)
        if action:
            query += " AND action = ?"
            params.append(action)

        query += f" ORDER BY timestamp DESC LIMIT {limit};"
        rows = conn.execute(query, params).fetchall()

        results = []
        for r in rows:
            d = dict(r)
            if d.get("new_values"):
                try:
                    d["new_values"] = json.loads(d["new_values"])
                except Exception:
                    pass
            if d.get("old_values"):
                try:
                    d["old_values"] = json.loads(d["old_values"])
                except Exception:
                    pass
            if d.get("metadata"):
                try:
                    d["metadata"] = json.loads(d["metadata"])
                except Exception:
                    pass
            results.append(d)
        return results
