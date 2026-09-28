from fastapi import APIRouter, HTTPException
import uuid
from datetime import datetime, timezone
from typing import Optional
from app.database import get_db
from app.models import BeneficiaryCreate, BeneficiaryUpdate

router = APIRouter(prefix="/beneficiaries", tags=["Beneficiaries"])

@router.post("", status_code=201)
def create_beneficiary(data: BeneficiaryCreate):
    ben_id = f"ben_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc).isoformat()
    with get_db() as conn:
        conn.execute("""
            INSERT INTO beneficiaries (
                id, name, phone, gender, age, category, preferred_language,
                district, block, village, contact_preference, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            ben_id, data.name, data.phone, data.gender, data.age, data.category,
            data.preferred_language, data.district, data.block, data.village,
            data.contact_preference, now, now
        ))
        row = conn.execute("SELECT * FROM beneficiaries WHERE id = ?;", (ben_id,)).fetchone()
        return dict(row)

@router.get("")
def list_beneficiaries(district: Optional[str] = None, block: Optional[str] = None):
    with get_db() as conn:
        query = "SELECT * FROM beneficiaries WHERE 1=1"
        params = []
        if district:
            query += " AND district = ?"
            params.append(district)
        if block:
            query += " AND block = ?"
            params.append(block)
        query += " ORDER BY created_at DESC;"
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]

@router.get("/{beneficiary_id}")
def get_beneficiary(beneficiary_id: str):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM beneficiaries WHERE id = ?;", (beneficiary_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Beneficiary not found")
        return dict(row)

@router.patch("/{beneficiary_id}")
def update_beneficiary(beneficiary_id: str, updates: BeneficiaryUpdate):
    now = datetime.now(timezone.utc).isoformat()
    with get_db() as conn:
        existing = conn.execute("SELECT * FROM beneficiaries WHERE id = ?;", (beneficiary_id,)).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Beneficiary not found")

        update_dict = updates.model_dump(exclude_unset=True)
        if not update_dict:
            return dict(existing)

        set_clauses = [f"{k} = ?" for k in update_dict.keys()]
        set_clauses.append("updated_at = ?")
        params = list(update_dict.values()) + [now, beneficiary_id]

        conn.execute(f"UPDATE beneficiaries SET {', '.join(set_clauses)} WHERE id = ?;", params)
        row = conn.execute("SELECT * FROM beneficiaries WHERE id = ?;", (beneficiary_id,)).fetchone()
        return dict(row)
