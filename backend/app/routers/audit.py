from fastapi import APIRouter
import json
from typing import Optional
from app.database import get_db

router = APIRouter(prefix="/audit-events", tags=["Audit"])

@router.get("")
def list_audit_events(actor_role: Optional[str] = None):
    with get_db() as conn:
        query = "SELECT * FROM audit_events WHERE 1=1"
        params = []
        if actor_role:
            query += " AND actor_role = ?"
            params.append(actor_role)
        query += " ORDER BY timestamp DESC LIMIT 50;"
        rows = conn.execute(query, params).fetchall()

        results = []
        for r in rows:
            d = dict(r)
            if d.get("new_values"):
                try:
                    d["new_values"] = json.loads(d["new_values"])
                except:
                    pass
            results.append(d)
        return results
