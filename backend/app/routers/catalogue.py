from fastapi import APIRouter, HTTPException
import json
from typing import Optional
from app.database import get_db

router = APIRouter(prefix="/catalogue", tags=["Catalogue"])

@router.get("/qualifications")
def list_qualifications(sector: Optional[str] = None):
    with get_db() as conn:
        query = "SELECT * FROM qualifications WHERE verification_status = 'verified'"
        params = []
        if sector:
            query += " AND sector = ?"
            params.append(sector)
        query += " ORDER BY nsqf_level ASC;"

        rows = conn.execute(query, params).fetchall()
        results = []
        for r in rows:
            d = dict(r)
            d["skills_acquired"] = json.loads(d.get("skills_acquired") or "[]")
            results.append(d)

        return {
            "count": len(results),
            "qualifications": results
        }

@router.get("/qualifications/{qual_id}")
def get_qualification_detail(qual_id: str):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM qualifications WHERE id = ?;", (qual_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Qualification not found")

        qual = dict(row)
        qual["skills_acquired"] = json.loads(qual.get("skills_acquired") or "[]")

        opp_rows = conn.execute("""
            SELECT * FROM local_opportunities
            WHERE qualification_id = ? AND batch_status IN ('active', 'upcoming');
        """, (qual_id,)).fetchall()

        return {
            "qualification": qual,
            "activeBatches": [dict(o) for o in opp_rows]
        }

@router.get("/opportunities")
def list_opportunities(district: Optional[str] = None, block: Optional[str] = None, status: Optional[str] = None):
    with get_db() as conn:
        query = "SELECT * FROM local_opportunities WHERE 1=1"
        params = []
        if district:
            query += " AND district = ?"
            params.append(district)
        if block:
            query += " AND block = ?"
            params.append(block)
        if status:
            query += " AND batch_status = ?"
            params.append(status)
        query += " ORDER BY batch_start_date ASC;"

        rows = conn.execute(query, params).fetchall()
        return {
            "count": len(rows),
            "opportunities": [dict(r) for r in rows]
        }
