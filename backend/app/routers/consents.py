from fastapi import APIRouter, HTTPException
import uuid
from datetime import datetime, timezone
from app.database import get_db
from app.models import ConsentCreate

router = APIRouter(prefix="/consents", tags=["Consents"])

@router.post("", status_code=201)
def record_consent(data: ConsentCreate):
    consent_id = f"consent_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc).isoformat()
    with get_db() as conn:
        # Check beneficiary exists
        ben = conn.execute("SELECT id FROM beneficiaries WHERE id = ?;", (data.beneficiary_id,)).fetchone()
        if not ben:
            raise HTTPException(status_code=404, detail="Beneficiary not found")

        conn.execute("""
            INSERT INTO consents (
                id, beneficiary_id, purpose, notice_version, audio_consent_recorded,
                voice_retention_choice, dpdp_affirmative_consent, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            consent_id, data.beneficiary_id, data.purpose, data.notice_version,
            1 if data.audio_consent_recorded else 0, data.voice_retention_choice,
            1 if data.dpdp_affirmative_consent else 0, now
        ))
        row = conn.execute("SELECT * FROM consents WHERE id = ?;", (consent_id,)).fetchone()
        return dict(row)

@router.get("/beneficiary/{beneficiary_id}")
def get_beneficiary_consents(beneficiary_id: str):
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM consents WHERE beneficiary_id = ? ORDER BY timestamp DESC;", (beneficiary_id,)).fetchall()
        return [dict(r) for r in rows]
