from fastapi import APIRouter, HTTPException
from typing import Optional
from app.database import get_db

router = APIRouter(prefix="/referrals", tags=["Referrals"])

@router.get("")
def list_referrals(status: Optional[str] = None):
    with get_db() as conn:
        query = "SELECT * FROM referrals WHERE 1=1"
        params = []
        if status:
            query += " AND status = ?"
            params.append(status)
        query += " ORDER BY created_at DESC;"
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]

@router.get("/{referral_id}")
def get_referral(referral_id: str):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM referrals WHERE id = ?;", (referral_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Referral not found")
        return dict(row)
