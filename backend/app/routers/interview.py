from fastapi import APIRouter, HTTPException
import uuid
import json
from datetime import datetime, timezone
from app.database import get_db
from app.models import InterviewStartRequest, InterviewTurnRequest, ConfirmProfileRequest
from app.ai_layers.layer1_intake.dialogue_manager import DialogueManager
from app.ai_layers.layer1_intake.speech_adapter import SpeechAdapter
from app.ai_layers.layer2_extraction.extraction_engine import ExtractionEngine

router = APIRouter(prefix="/interview", tags=["Interview"])
extraction_engine = ExtractionEngine()

@router.post("/start", status_code=201)
def start_interview(data: InterviewStartRequest):
    session_id = f"sess_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc).isoformat()
    first_turn = DialogueManager.get_initial_turn(data.language or "hi")

    with get_db() as conn:
        conn.execute("""
            INSERT INTO interview_sessions (
                id, beneficiary_id, channel, status, current_question_index,
                last_question, language, transcript_history, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            session_id, data.beneficiary_id, data.channel or "web_app", "in_progress",
            first_turn["question_index"], first_turn["question"], data.language or "hi",
            json.dumps([{"speaker": "ai", "text": first_turn["question"]}]), now, now
        ))
        return {
            "session_id": session_id,
            "status": "in_progress",
            "first_question": first_turn["question"],
            "language": data.language or "hi"
        }

@router.post("/turn")
def process_turn(data: InterviewTurnRequest):
    now = datetime.now(timezone.utc).isoformat()
    with get_db() as conn:
        session = conn.execute("SELECT * FROM interview_sessions WHERE id = ?;", (data.session_id,)).fetchone()
        if not session:
            raise HTTPException(status_code=404, detail="Interview session not found")

        current_idx = session["current_question_index"]
        history = json.loads(session["transcript_history"] or "[]")
        lang = data.language or session["language"] or "hi"

        user_text = SpeechAdapter.transcribe(data.audio_input_base64, data.text_input, lang)
        next_turn = DialogueManager.process_turn(current_idx, user_text, history, lang)

        new_status = "profile_extracted" if next_turn["is_final"] else "in_progress"

        conn.execute("""
            UPDATE interview_sessions
            SET current_question_index = ?, last_question = ?, transcript_history = ?, status = ?, updated_at = ?
            WHERE id = ?;
        """, (
            next_turn["question_index"], next_turn["question"], json.dumps(history),
            new_status, now, data.session_id
        ))

        return {
            "session_id": data.session_id,
            "transcript_heard": user_text,
            "next_question": next_turn["question"],
            "is_final": next_turn["is_final"],
            "status": new_status
        }

@router.get("/extract/{session_id}")
def extract_profile(session_id: str):
    with get_db() as conn:
        session = conn.execute("SELECT * FROM interview_sessions WHERE id = ?;", (session_id,)).fetchone()
        if not session:
            raise HTTPException(status_code=404, detail="Interview session not found")

        history = json.loads(session["transcript_history"] or "[]")
        ben = conn.execute("SELECT * FROM beneficiaries WHERE id = ?;", (session["beneficiary_id"],)).fetchone()
        district = ben["district"] if ben else "Moradabad"
        block = ben["block"] if ben else "Chhajlet"

        extracted = extraction_engine.extract_profile(history, district, block)
        return {
            "session_id": session_id,
            "beneficiary_id": session["beneficiary_id"],
            "extracted_profile": extracted
        }

@router.post("/confirm")
def confirm_profile(data: ConfirmProfileRequest):
    now = datetime.now(timezone.utc).isoformat()
    with get_db() as conn:
        for field, val in data.confirmed_fields.items():
            ans_id = f"ans_{uuid.uuid4().hex[:10]}"
            conn.execute("""
                INSERT INTO profile_answers (
                    id, beneficiary_id, session_id, field_name, field_value,
                    confidence_score, confirmation_status, source, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                ans_id, data.beneficiary_id, data.session_id, field,
                json.dumps(val) if isinstance(val, (list, dict)) else str(val),
                1.0, "confirmed", "beneficiary_edit", now, now
            ))

        conn.execute("UPDATE interview_sessions SET status = 'confirmed', updated_at = ? WHERE id = ?;", (now, data.session_id))
        return {
            "status": "confirmed",
            "message": "Profile answers verified and locked by beneficiary."
        }

@router.get("/session/{session_id}")
def get_session(session_id: str):
    with get_db() as conn:
        session = conn.execute("SELECT * FROM interview_sessions WHERE id = ?;", (session_id,)).fetchone()
        if not session:
            raise HTTPException(status_code=404, detail="Interview session not found")
        result = dict(session)
        result["transcript_history"] = json.loads(result.get("transcript_history") or "[]")
        return result
