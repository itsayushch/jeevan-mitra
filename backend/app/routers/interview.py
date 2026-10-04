from fastapi import APIRouter, HTTPException, Depends
import uuid
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from app.database import get_db
from app.models import (
    InterviewStartRequest, InterviewTurnRequest, ConfirmProfileRequest,
    InterviewFieldUpdateRequest, ExportSummaryRequest
)
from app.ai_layers.layer1_intake.dialogue_manager import DialogueManager
from app.ai_layers.layer1_intake.speech_adapter import SpeechAdapter
from app.ai_layers.layer2_extraction.extraction_engine import ExtractionEngine
from app.ai_layers.layer2_extraction.conversation import extract_conversation
from app.dependencies.auth import get_current_actor, Actor
from app.dependencies.consent import verify_consent
from app.services.export_service import ExportService
from app.utils.audit_events import log_audit_event
from app.utils.errors import EntityNotFoundException, ConsentRequiredException

router = APIRouter(tags=["Interview"])
extraction_engine = ExtractionEngine()

REQUIRED_PROFILE_FIELDS = [
    "district", "language", "education", "current_work", "traditional_or_existing_skills",
    "interests", "mobility", "access_needs", "employment_preference", "self_employment_or_wage_preference"
]

def _check_ai_consent(conn, beneficiary_id: Optional[str], session_id: Optional[str]):
    latest_c = None
    if beneficiary_id and beneficiary_id.startswith("ben_"):
        ben = conn.execute("SELECT id FROM beneficiaries WHERE id = ?;", (beneficiary_id,)).fetchone()
        if not ben:
            raise HTTPException(status_code=404, detail="Beneficiary not found")

        latest_c = conn.execute("""
            SELECT dpdp_affirmative_consent FROM consents
            WHERE beneficiary_id = ?
            ORDER BY timestamp DESC, rowid DESC LIMIT 1;
        """, (beneficiary_id,)).fetchone()
        if not latest_c or not latest_c["dpdp_affirmative_consent"]:
            raise HTTPException(status_code=403, detail="Affirmative consent is required for interview data")

    try:
        verify_consent(conn, "ai_processing", beneficiary_id, session_id)
    except ConsentRequiredException:
        if beneficiary_id and latest_c and latest_c["dpdp_affirmative_consent"]:
            return
        raise

# ============================================================================
# A3 State Machine & Field-Provenance Routes (/api/v1/interviews/...)
# ============================================================================
@router.post("/interviews/start", status_code=201)
@router.post("/interview/start", status_code=201)
def start_interview(data: InterviewStartRequest, actor: Actor = Depends(get_current_actor)):
    interview_id = f"int_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc).isoformat()
    lang = data.language or "hi"
    target_session_id = data.session_id or actor.session_id or interview_id
    target_ben_id = data.beneficiary_id or actor.beneficiary_id

    with get_db() as conn:
        _check_ai_consent(conn, target_ben_id, target_session_id)
        first_turn = DialogueManager.get_initial_turn(lang)

        conn.execute("""
            INSERT INTO interview_sessions (
                id, beneficiary_id, session_id, channel, status, current_question_index,
                last_question, language, transcript_history, created_at, updated_at
            ) VALUES (?, ?, ?, ?, 'in_progress', ?, ?, ?, ?, ?, ?);
        """, (
            interview_id, target_ben_id, target_session_id, data.channel or "web_app",
            first_turn["question_index"], first_turn["question"], lang,
            json.dumps([{"speaker": "ai", "text": first_turn["question"]}]), now, now
        ))

        # Log initial turn
        conn.execute("""
            INSERT INTO interview_turns (id, interview_id, turn_index, speaker, text, mode, created_at)
            VALUES (?, ?, ?, 'ai', ?, 'standard', ?);
        """, (f"turn_{uuid.uuid4().hex[:10]}", interview_id, 0, first_turn["question"], now))

        log_audit_event(
            conn=conn,
            actor_id=actor.actor_id,
            actor_name=actor.actor_name,
            actor_role=actor.actor_role,
            action="INTERVIEW_STARTED",
            entity_type="interview_session",
            entity_id=interview_id
        )

        return {
            "interview_id": interview_id,
            "session_id": target_session_id,
            "status": "collecting",
            "first_question": first_turn["question"],
            "question_index": 0,
            "language": lang
        }

@router.post("/interviews/{interview_id}/turns")
def process_interview_turn(
    interview_id: str,
    data: InterviewTurnRequest,
    actor: Actor = Depends(get_current_actor)
):
    now = datetime.now(timezone.utc).isoformat()
    with get_db() as conn:
        sess = conn.execute("SELECT * FROM interview_sessions WHERE id = ?;", (interview_id,)).fetchone()
        if not sess:
            raise EntityNotFoundException("InterviewSession", interview_id)

        if not actor.is_staff() and not (
            (actor.session_id and actor.session_id == sess["session_id"])
            or (actor.beneficiary_id and actor.beneficiary_id == sess["beneficiary_id"])
        ):
            raise HTTPException(403, "This interview belongs to another session")

        target_ben_id = sess["beneficiary_id"] or actor.beneficiary_id
        target_session_id = sess["session_id"] or actor.session_id

        current_idx = sess["current_question_index"]
        history = json.loads(sess["transcript_history"] or "[]")
        lang = data.language or sess["language"] or "hi"

        user_text = data.message or data.text_input or getattr(data, "text", None)
        if not user_text and data.audio_input_base64:
            user_text = SpeechAdapter.transcribe(data.audio_input_base64, None, lang)
        if not user_text or not user_text.strip():
            raise HTTPException(422, "Please provide a message")
        if len(user_text) > 4000:
            raise HTTPException(422, "Message must be at most 4000 characters")

        # If guided fallback mode is explicitly requested, bypass AI consent check and AI extraction
        if getattr(data, "mode", None) == "guided_fallback":
            fallback_turn = DialogueManager.get_fallback_turn(current_idx + 1, language=lang)
            user_turn_id = f"turn_{uuid.uuid4().hex[:10]}"
            conn.execute("""
                INSERT INTO interview_turns (id, interview_id, turn_index, speaker, text, mode, created_at)
                VALUES (?, ?, ?, 'user', ?, 'guided_fallback', ?);
            """, (user_turn_id, interview_id, current_idx + 1, user_text, now))

            ai_turn_id = f"turn_{uuid.uuid4().hex[:10]}"
            conn.execute("""
                INSERT INTO interview_turns (id, interview_id, turn_index, speaker, text, mode, extracted_fields, created_at)
                VALUES (?, ?, ?, 'ai', ?, 'guided_fallback', '{}', ?);
            """, (ai_turn_id, interview_id, fallback_turn["question_index"], fallback_turn["question"], now))

            history.append({"speaker": "user", "text": user_text})
            history.append({"speaker": "ai", "text": fallback_turn["question"]})

            conn.execute("""
                UPDATE interview_sessions
                SET current_question_index = ?, last_question = ?, transcript_history = ?, updated_at = ?
                WHERE id = ?;
            """, (fallback_turn["question_index"], fallback_turn["question"], json.dumps(history), now, interview_id))

            return {
                "interview_id": interview_id,
                "question": fallback_turn["question"],
                "question_index": fallback_turn["question_index"],
                "mode": "guided_fallback",
                "extracted_fields": {},
                "is_final": fallback_turn.get("is_final", False),
                "status": "collecting"
            }

        _check_ai_consent(conn, target_ben_id, target_session_id)

        # Record user turn in DB
        user_turn_id = f"turn_{uuid.uuid4().hex[:10]}"
        conn.execute("""
            INSERT INTO interview_turns (id, interview_id, turn_index, speaker, text, mode, created_at)
            VALUES (?, ?, ?, 'user', ?, 'standard', ?);
        """, (user_turn_id, interview_id, current_idx + 1, user_text, now))

        # Incremental extraction & confidence evaluation
        ben_row = conn.execute("SELECT * FROM beneficiaries WHERE id = ?;", (target_ben_id,)).fetchone() if target_ben_id else None
        district = ben_row["district"] if ben_row else "Moradabad"
        block = ben_row["block"] if ben_row else "Chhajlet"

        history_with_user = list(history)
        history_with_user.append({"speaker": "user", "text": user_text})
        provider = None
        missing = []
        if data.mode == "conversational":
            verify_consent(conn, "profile_storage", target_ben_id, target_session_id)
            extracted, missing, question, provider = extract_conversation(history_with_user, lang)
            history = history_with_user + [{"speaker": "ai", "text": question}]
            next_turn = {"question_index": current_idx + 1, "question": question,
                         "mode": "standard" if provider == "gemini" else "guided_fallback",
                         "is_final": not missing}
        else:
            extracted = extraction_engine.extract_profile(history_with_user, district, block)
            next_turn = DialogueManager.process_turn(
                current_index=current_idx, user_utterance=user_text,
                transcript_history=history, language=lang,
                clarification_prompt=extracted.get("clarification_needed"))

        if getattr(data, "mode", None) == "guided_fallback":
            next_turn["mode"] = "guided_fallback"

        # Record AI turn in DB
        ai_turn_id = f"turn_{uuid.uuid4().hex[:10]}"
        conn.execute("""
            INSERT INTO interview_turns (id, interview_id, turn_index, speaker, text, mode, extracted_fields, created_at)
            VALUES (?, ?, ?, 'ai', ?, ?, ?, ?);
        """, (
            ai_turn_id, interview_id, next_turn["question_index"], next_turn["question"],
            next_turn["mode"], json.dumps(extracted), now
        ))

        # Save AI-inferred fields into profile_field_values as unconfirmed
        for field, val in extracted.items():
            if field in ["confidence_scores", "clarification_needed"]:
                continue
            conf = extracted.get("confidence_scores", {}).get(field, 0.85)

            existing_f = conn.execute("""
                SELECT id, field_value, version FROM profile_field_values
                WHERE interview_id = ? AND field_name = ?;
            """, (interview_id, field)).fetchone()

            val_str = json.dumps(val) if isinstance(val, (list, dict)) else str(val)

            if existing_f:
                conn.execute("""
                    UPDATE profile_field_values
                    SET field_value = ?, confidence = ?, previous_value = ?, user_confirmed = 0, source = 'ai_inferred', version = version + 1, updated_at = ?
                    WHERE id = ?;
                """, (val_str, conf, existing_f["field_value"], now, existing_f["id"]))
            else:
                conn.execute("""
                    INSERT INTO profile_field_values (
                        id, interview_id, beneficiary_id, field_name, field_value,
                        source, confidence, user_confirmed, version, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, 'ai_inferred', ?, 0, 1, ?, ?);
                """, (f"pfv_{uuid.uuid4().hex[:10]}", interview_id, target_ben_id, field, val_str, conf, now, now))

        # State transition
        new_status = "awaiting_confirmation" if next_turn["is_final"] else "collecting"
        conn.execute("""
            UPDATE interview_sessions
            SET current_question_index = ?, last_question = ?, transcript_history = ?, status = ?, updated_at = ?
            WHERE id = ?;
        """, (next_turn["question_index"], next_turn["question"], json.dumps(history), new_status, now, interview_id))

        return {
            "interview_id": interview_id,
            "session_id": sess["session_id"],
            "user_text": user_text,
            "next_question": next_turn["question"],
            "mode": next_turn["mode"],
            "is_final": next_turn["is_final"],
            "status": new_status,
            "extraction_provider": provider,
            "missing_fields": missing,
            "inferred_profile": extracted
        }

@router.get("/interviews/{interview_id}")
def get_interview_detail(interview_id: str):
    with get_db() as conn:
        sess = conn.execute("SELECT * FROM interview_sessions WHERE id = ?;", (interview_id,)).fetchone()
        if not sess:
            raise EntityNotFoundException("InterviewSession", interview_id)
        _check_ai_consent(conn, sess["beneficiary_id"], sess["session_id"] or interview_id)

        turns = conn.execute("SELECT * FROM interview_turns WHERE interview_id = ? ORDER BY turn_index ASC;", (interview_id,)).fetchall()
        field_values = conn.execute("SELECT * FROM profile_field_values WHERE interview_id = ?;", (interview_id,)).fetchall()

        fields_dict = {}
        for f in field_values:
            val = f["field_value"]
            try:
                parsed_val = json.loads(val)
            except Exception:
                parsed_val = val
            fields_dict[f["field_name"]] = {
                "value": parsed_val,
                "source": f["source"],
                "confidence": f["confidence"],
                "user_confirmed": bool(f["user_confirmed"]),
                "version": f["version"]
            }

        res = dict(sess)
        res["transcript_history"] = json.loads(res.get("transcript_history") or "[]")
        res["turns"] = [dict(t) for t in turns]
        res["fields"] = fields_dict
        return res

@router.post("/interviews/{interview_id}/confirm-profile")
def confirm_interview_profile(
    interview_id: str,
    data: ConfirmProfileRequest,
    actor: Actor = Depends(get_current_actor)
):
    """
    User reviews and confirms profile values before matching can occur.
    Transitions interview state from awaiting_confirmation -> ready_for_matching.
    """
    with get_db() as conn:
        sess = conn.execute("SELECT * FROM interview_sessions WHERE id = ?;", (interview_id,)).fetchone()
        if not sess:
            raise EntityNotFoundException("InterviewSession", interview_id)
        if not actor.is_staff() and not (actor.session_id and actor.session_id == sess["session_id"]):
            raise HTTPException(403, "This interview belongs to another session")
        target_ben_id = data.beneficiary_id or sess["beneficiary_id"] or actor.beneficiary_id
        target_session_id = sess["session_id"] or actor.session_id or interview_id
        _check_ai_consent(conn, target_ben_id, target_session_id)
        now = datetime.now(timezone.utc).isoformat()

        # Update or insert each confirmed field
        for field, val in data.confirmed_fields.items():
            val_str = json.dumps(val) if isinstance(val, (list, dict)) else str(val)
            existing = conn.execute("""
                SELECT id, field_value, version FROM profile_field_values
                WHERE interview_id = ? AND field_name = ?;
            """, (interview_id, field)).fetchone()

            if existing:
                conn.execute("""
                    UPDATE profile_field_values
                    SET field_value = ?, source = 'user', confidence = 1.0, user_confirmed = 1,
                        previous_value = ?, version = version + 1, updated_at = ?
                    WHERE id = ?;
                """, (val_str, existing["field_value"], now, existing["id"]))
            else:
                conn.execute("""
                    INSERT INTO profile_field_values (
                        id, interview_id, beneficiary_id, field_name, field_value,
                        source, confidence, user_confirmed, version, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, 'user', 1.0, 1, 1, ?, ?);
                """, (f"pfv_{uuid.uuid4().hex[:10]}", interview_id, target_ben_id, field, val_str, now, now))

            # Also mirror to profile_answers for backward compatibility
            if target_ben_id:
                conn.execute("""
                    INSERT INTO profile_answers (
                        id, beneficiary_id, session_id, field_name, field_value,
                        confidence_score, confirmation_status, source, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, 1.0, 'confirmed', 'beneficiary_edit', ?, ?);
                """, (f"ans_{uuid.uuid4().hex[:10]}", target_ben_id, interview_id, field, val_str, now, now))

        # Save immutable ProfileRevision snapshot
        rev_count = conn.execute("SELECT COUNT(*) as count FROM profile_revisions WHERE interview_id = ?;", (interview_id,)).fetchone()["count"]
        conn.execute("""
            INSERT INTO profile_revisions (id, interview_id, revision_number, profile_snapshot, created_by, created_at)
            VALUES (?, ?, ?, ?, ?, ?);
        """, (f"rev_{uuid.uuid4().hex[:10]}", interview_id, rev_count + 1, json.dumps(data.confirmed_fields), actor.actor_id, now))

        # State transition to ready_for_matching
        conn.execute("""
            UPDATE interview_sessions
            SET status = 'ready_for_matching', updated_at = ?
            WHERE id = ?;
        """, (now, interview_id))

        log_audit_event(
            conn=conn,
            actor_id=actor.actor_id,
            actor_name=actor.actor_name,
            actor_role=actor.actor_role,
            action="PROFILE_CONFIRMED_FOR_MATCHING",
            entity_type="interview_session",
            entity_id=interview_id,
            new_values=data.confirmed_fields
        )

        return {
            "status": "ready_for_matching",
            "interview_id": interview_id,
            "message": "Profile fields confirmed by user. Interview is now ready for deterministic recommendation matching."
        }

@router.patch("/interviews/{interview_id}/fields/{field_name}")
def update_interview_field(
    interview_id: str,
    field_name: str,
    body: InterviewFieldUpdateRequest,
    actor: Actor = Depends(get_current_actor)
):
    """
    Enables user or counselor to edit any single field with full revision provenance.
    """
    now = datetime.now(timezone.utc).isoformat()
    val_str = json.dumps(body.value) if isinstance(body.value, (list, dict)) else str(body.value)

    with get_db() as conn:
        sess = conn.execute("SELECT * FROM interview_sessions WHERE id = ?;", (interview_id,)).fetchone()
        if not sess:
            raise EntityNotFoundException("InterviewSession", interview_id)

        if not actor.is_staff() and not (
            (actor.session_id and actor.session_id == sess["session_id"])
            or (actor.beneficiary_id and actor.beneficiary_id == sess["beneficiary_id"])
        ):
            raise HTTPException(403, "This interview belongs to another session")

        target_ben_id = sess["beneficiary_id"] or actor.beneficiary_id

        existing = conn.execute("""
            SELECT id, field_value, version FROM profile_field_values
            WHERE interview_id = ? AND field_name = ?;
        """, (interview_id, field_name)).fetchone()

        if existing:
            conn.execute("""
                UPDATE profile_field_values
                SET field_value = ?, source = ?, confidence = 1.0, user_confirmed = 1,
                    previous_value = ?, version = version + 1, updated_at = ?
                WHERE id = ?;
            """, (val_str, body.source or "user", existing["field_value"], now, existing["id"]))
        else:
            conn.execute("""
                INSERT INTO profile_field_values (
                    id, interview_id, beneficiary_id, field_name, field_value,
                    source, confidence, user_confirmed, version, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, 1.0, 1, 1, ?, ?);
            """, (f"pfv_{uuid.uuid4().hex[:10]}", interview_id, target_ben_id, field_name, val_str, body.source or "user", now, now))

        log_audit_event(
            conn=conn,
            actor_id=actor.actor_id,
            actor_name=actor.actor_name,
            actor_role=actor.actor_role,
            action="PROFILE_FIELD_CORRECTED",
            entity_type="profile_field_value",
            entity_id=f"{interview_id}:{field_name}",
            old_values={"field_value": existing["field_value"] if existing else None},
            new_values={"field_value": val_str, "source": body.source}
        )

        return {
            "status": "updated",
            "field_name": field_name,
            "new_value": body.value,
            "source": body.source
        }

@router.post("/interviews/{interview_id}/complete")
def complete_interview(interview_id: str, actor: Actor = Depends(get_current_actor)):
    now = datetime.now(timezone.utc).isoformat()
    with get_db() as conn:
        sess = conn.execute("SELECT * FROM interview_sessions WHERE id = ?;", (interview_id,)).fetchone()
        if not sess:
            raise EntityNotFoundException("InterviewSession", interview_id)

        conn.execute("UPDATE interview_sessions SET status = 'completed', updated_at = ? WHERE id = ?;", (now, interview_id))
        return {"status": "completed", "interview_id": interview_id}

@router.post("/interviews/{interview_id}/summary")
def get_interview_summary_export(
    interview_id: str,
    body: Optional[ExportSummaryRequest] = None,
    actor: Actor = Depends(get_current_actor)
):
    with get_db() as conn:
        sess = conn.execute("SELECT * FROM interview_sessions WHERE id = ?;", (interview_id,)).fetchone()
        if not sess:
            raise EntityNotFoundException("InterviewSession", interview_id)

        return ExportService.generate_summary_export(
            conn=conn,
            interview_id=interview_id,
            beneficiary_id=sess["beneficiary_id"],
            actor_id=actor.actor_id
        )

# ============================================================================
# Legacy Interview Endpoints (Backwards Compatibility)
# ============================================================================
@router.post("/interview/turn")
def legacy_turn(data: InterviewTurnRequest, actor: Actor = Depends(get_current_actor)):
    session_id = data.session_id or data.interview_id
    if not session_id:
        raise HTTPException(status_code=422, detail="session_id is required")
    return process_interview_turn(session_id, data, actor)

@router.get("/interview/extract/{session_id}")
def legacy_extract(session_id: str, actor: Actor = Depends(get_current_actor)):
    with get_db() as conn:
        sess = conn.execute("SELECT * FROM interview_sessions WHERE id = ?;", (session_id,)).fetchone()
        if not sess:
            raise EntityNotFoundException("InterviewSession", session_id)
        _check_ai_consent(conn, sess["beneficiary_id"], session_id)

        history = json.loads(sess["transcript_history"] or "[]")
        ben = conn.execute("SELECT * FROM beneficiaries WHERE id = ?;", (sess["beneficiary_id"],)).fetchone() if sess["beneficiary_id"] else None
        district = ben["district"] if ben else "Moradabad"
        block = ben["block"] if ben else "Chhajlet"

        extracted = extraction_engine.extract_profile(history, district, block)
        return {
            "session_id": session_id,
            "beneficiary_id": sess["beneficiary_id"],
            "extracted_profile": extracted
        }

@router.post("/interview/confirm")
def legacy_confirm(data: ConfirmProfileRequest, actor: Actor = Depends(get_current_actor)):
    sess_id = data.session_id or data.interview_id
    if not sess_id:
        raise HTTPException(status_code=422, detail="session_id is required")
    return confirm_interview_profile(sess_id, data, actor)

@router.get("/interview/session/{session_id}")
def legacy_get_session(session_id: str):
    return get_interview_detail(session_id)
