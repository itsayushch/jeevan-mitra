import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from app.core.settings import settings
from app.ivr.constants import (
    IVRState,
    IVRStatus,
    IVRCallbackReason,
    IVREventType,
    PromptKey,
)
from app.ivr.engine import IVREngine
from app.ivr.repository import IVRRepository
from app.ivr.audio_catalog import AudioCatalog
from app.ivr.schemas import (
    IVRSessionStartRequest,
    IVRDigitInputRequest,
    IVRSessionResponse,
    IVREventResponse,
    IVRAction,
)
from app.ivr.providers.mock import MockIVRProvider
from app.ivr.security import sanitize_payload_for_logging
from app.services.consent_service import ConsentService
from app.models import ConsentRecordCreate
from app.utils.audit_events import log_audit_event
from app.utils.errors import EntityNotFoundException, AppError


class IVRService:
    """
    Coordinates IVR state machine, database persistence, consent records,
    beneficiary privacy, and audit logging for the feature-phone simulator.
    """

    @staticmethod
    def _check_simulator_enabled():
        if not getattr(settings, "IVR_SIMULATOR_ENABLED", True):
            raise AppError(
                status_code=403,
                code="SIMULATOR_DISABLED",
                message="IVR Simulator is disabled in this environment.",
            )

    @staticmethod
    def _load_initial_context(
        conn: Any, beneficiary_id: Optional[str]
    ) -> Dict[str, Any]:
        """Loads safe summaries of training, schemes, and optional referral status."""
        context: Dict[str, Any] = {
            "training_items": [],
            "scheme_items": [],
            "referral_summary": None,
            "has_consent": False,
        }

        # 1. Load up to 3 published training courses
        try:
            courses = conn.execute("""
                SELECT id, title, sector, duration_hours
                FROM training_courses
                WHERE is_published = 1
                LIMIT 3;
            """).fetchall()
            context["training_items"] = [
                {"id": c["id"], "title": c["title"], "sector": c.get("sector")}
                for c in courses
            ]
        except Exception:
            context["training_items"] = []

        # 2. Load up to 3 verified NQR qualifications / schemes
        try:
            quals = conn.execute("""
                SELECT id, title, sector, nsqf_level
                FROM qualifications
                WHERE UPPER(verification_status) = 'VERIFIED'
                LIMIT 3;
            """).fetchall()
            context["scheme_items"] = [
                {"id": q["id"], "title": q["title"], "sector": q.get("sector")}
                for q in quals
            ]
        except Exception:
            context["scheme_items"] = []

        # 3. If beneficiary is identified, load active referral/case status safely
        if beneficiary_id:
            try:
                # Check beneficiary_cases table
                case = conn.execute(
                    """
                    SELECT case_status, updated_at
                    FROM beneficiary_cases
                    WHERE beneficiary_id = ?
                    ORDER BY updated_at DESC LIMIT 1;
                """,
                    (beneficiary_id,),
                ).fetchone()

                if case:
                    st = case.get("case_status", "NEW").replace("_", " ").title()
                    context["referral_summary"] = f"स्थिति {st} है"
                else:
                    # Check referrals table
                    ref = conn.execute(
                        """
                        SELECT referral_status, updated_at
                        FROM referrals
                        WHERE beneficiary_id = ?
                        ORDER BY updated_at DESC LIMIT 1;
                    """,
                        (beneficiary_id,),
                    ).fetchone()
                    if ref:
                        st = (
                            ref.get("referral_status", "pending")
                            .replace("_", " ")
                            .title()
                        )
                        context["referral_summary"] = f"रेफरल स्थिति {st} है"
            except Exception:
                context["referral_summary"] = None

        return context

    @staticmethod
    def start_session(conn: Any, req: IVRSessionStartRequest) -> IVRSessionResponse:
        IVRService._check_simulator_enabled()

        # 1. Resolve beneficiary
        ben_id = req.beneficiary_id
        if not ben_id and req.simulated_caller_reference:
            # Safe registered phone lookup
            clean_ref = req.simulated_caller_reference.strip()
            row = conn.execute(
                "SELECT id FROM beneficiaries WHERE phone = ?;", (clean_ref,)
            ).fetchone()
            if row:
                ben_id = row["id"]

        session_id = f"ivrs_{uuid.uuid4().hex[:12]}"
        language = req.language or settings.IVR_DEFAULT_LANGUAGE
        timeout_seconds = settings.IVR_SESSION_TIMEOUT_SECONDS

        # 2. Preload safe contextual catalog items
        context = IVRService._load_initial_context(conn, ben_id)
        if ben_id:
            context["beneficiary_id"] = ben_id

        # 3. Create session record
        session_row = IVRRepository.create_session(
            conn=conn,
            session_id=session_id,
            provider="mock",
            provider_call_id=None,
            caller_reference=req.simulated_caller_reference,
            beneficiary_id=ben_id,
            language=language,
            timeout_seconds=timeout_seconds,
            initial_context=context,
        )

        # 4. Engine initial state
        engine_res = IVREngine.get_initial_state(language=language)

        # 5. Append initial event
        safe_payload = {
            "prompt_key": engine_res.prompt_key.value,
            "accepted_digits": engine_res.accepted_digits,
        }
        IVRRepository.append_event(
            conn=conn,
            session_id=session_id,
            event_type=IVREventType.SESSION_STARTED.value,
            state_before="none",
            state_after=IVRState.WELCOME.value,
            digit=None,
            prompt_key=engine_res.prompt_key.value,
            idempotency_key=req.idempotency_key,
            safe_payload=safe_payload,
        )

        # 6. Audit event
        log_audit_event(
            conn=conn,
            actor_id=ben_id or "anonymous_caller",
            actor_name="IVR Caller",
            actor_role="beneficiary",
            action="IVR_CALL_STARTED",
            entity_type="ivr_session",
            entity_id=session_id,
            new_values={
                "language": language,
                "caller_hash": session_row.get("caller_reference_hash"),
                "beneficiary_id": ben_id,
            },
        )

        return IVRSessionResponse(
            session_id=session_id,
            state=engine_res.next_state,
            status=engine_res.next_status,
            prompt_key=engine_res.prompt_key.value,
            prompt_text=engine_res.prompt_text,
            accepted_digits=engine_res.accepted_digits,
            actions=engine_res.actions,
            retry_count=0,
            expires_at=session_row["expires_at"],
            callback_request=None,
            data_summary=None,
        )

    @staticmethod
    def process_digit_input(
        conn: Any, session_id: str, req: IVRDigitInputRequest
    ) -> IVRSessionResponse:
        IVRService._check_simulator_enabled()

        # 1. Fetch existing session
        session = IVRRepository.get_session(conn, session_id)
        if not session:
            raise EntityNotFoundException("IVRSession", session_id)

        language = session.get("language") or settings.IVR_DEFAULT_LANGUAGE
        current_state = IVRState(session["current_state"])
        current_status = IVRStatus(session["status"])
        context = session.get("context") or {}
        ben_id = session.get("beneficiary_id")
        retry_count = session.get("invalid_attempt_count", 0)

        # 2. Check session expiry
        now_utc = datetime.now(timezone.utc)
        expires_at_dt = datetime.fromisoformat(
            session["expires_at"].replace("Z", "+00:00")
        )
        is_expired = now_utc > expires_at_dt or current_status == IVRStatus.EXPIRED

        if is_expired:
            if current_status != IVRStatus.EXPIRED:
                IVRRepository.expire_session(conn, session_id)
            res = IVREngine.transition(
                current_state=IVRState.EXPIRED,
                digit=None,
                is_expired=True,
                language=language,
            )
            return IVRSessionResponse(
                session_id=session_id,
                state=res.next_state,
                previous_state=current_state,
                status=res.next_status,
                prompt_key=res.prompt_key.value,
                prompt_text=res.prompt_text,
                accepted_digits=res.accepted_digits,
                actions=res.actions,
                retry_count=retry_count,
                expires_at=session["expires_at"],
            )

        # 3. Check idempotency: if idempotency key already seen, return previous event response
        if req.idempotency_key:
            prev_event = IVRRepository.get_event_by_idempotency_key(
                conn, session_id, req.idempotency_key
            )
            if prev_event and prev_event.get("safe_payload"):
                payload = prev_event["safe_payload"]
                cb = IVRRepository.get_callback_request(conn, session_id)
                return IVRSessionResponse(
                    session_id=session_id,
                    state=IVRState(payload.get("next_state", session["current_state"])),
                    previous_state=IVRState(prev_event["state_before"])
                    if prev_event.get("state_before")
                    else None,
                    status=IVRStatus(payload.get("next_status", session["status"])),
                    prompt_key=prev_event["prompt_key"],
                    prompt_text=payload.get("prompt_text", ""),
                    accepted_digits=payload.get("accepted_digits", []),
                    actions=[IVRAction(**a) for a in payload.get("actions", [])],
                    retry_count=payload.get("retry_count", retry_count),
                    expires_at=session["expires_at"],
                    callback_request=cb,
                    data_summary=payload.get("data_summary"),
                )

        # 4. Check terminal states (goodbye / completed)
        if current_status in (IVRStatus.COMPLETED, IVRStatus.TERMINATED):
            res = IVREngine.transition(
                current_state=IVRState.GOODBYE, digit=None, language=language
            )
            cb = IVRRepository.get_callback_request(conn, session_id)
            return IVRSessionResponse(
                session_id=session_id,
                state=res.next_state,
                previous_state=current_state,
                status=current_status,
                prompt_key=res.prompt_key.value,
                prompt_text=res.prompt_text,
                accepted_digits=res.accepted_digits,
                actions=res.actions,
                retry_count=retry_count,
                expires_at=session["expires_at"],
                callback_request=cb,
            )

        # 5. Normalize digit via MockProvider
        provider = MockIVRProvider()
        normalized_digit = provider.normalize_digit(req.digit)

        # 6. Execute deterministic state machine
        engine_res = IVREngine.transition(
            current_state=current_state,
            digit=normalized_digit,
            invalid_attempt_count=retry_count,
            max_retries=settings.IVR_MAX_INVALID_ATTEMPTS,
            language=language,
            context=context,
            is_expired=False,
        )

        # 7. Apply side-effects according to intent
        cb_record = None
        data_summary = None

        if engine_res.intent == "grant_consent":
            context["has_consent"] = True
            # Record affirmative consent in DPDP consent ledger
            try:
                consent_req = ConsentRecordCreate(
                    session_id=session_id,
                    beneficiary_id=ben_id,
                    consent_type="dpdp_general",
                    policy_version="1.0",
                    user_language="hi",
                    capture_channel="ivr",
                    granted=True,
                )
                ConsentService.record_consent(
                    conn, consent_req, actor_id=ben_id or "ivr_caller"
                )
            except Exception:
                pass

        elif engine_res.intent == "refuse_consent":
            context["has_consent"] = False
            # If consent was refused, log refusal
            log_audit_event(
                conn=conn,
                actor_id=ben_id or "ivr_caller",
                actor_name="IVR Caller",
                actor_role="beneficiary",
                action="IVR_CONSENT_REFUSED",
                entity_type="ivr_session",
                entity_id=session_id,
                metadata={"reason": "Caller pressed 2 during consent"},
            )

        elif engine_res.intent == "create_callback":
            reason = (
                engine_res.callback_reason.value
                if engine_res.callback_reason
                else IVRCallbackReason.GENERAL_HELP.value
            )
            cb_record = IVRRepository.get_or_create_callback_request(
                conn=conn,
                session_id=session_id,
                beneficiary_id=ben_id,
                callback_reason=reason,
            )
            # Log callback audit event
            log_audit_event(
                conn=conn,
                actor_id=ben_id or "ivr_caller",
                actor_name="IVR Caller",
                actor_role="beneficiary",
                action="IVR_CALLBACK_REQUESTED",
                entity_type="ivr_callback_request",
                entity_id=cb_record["id"],
                metadata={"reason": reason, "session_id": session_id},
            )

        # Data summaries for training or scheme exploration
        if engine_res.selected_item_index is not None:
            if current_state == IVRState.TRAINING:
                items = context.get("training_items") or []
                if 0 <= engine_res.selected_item_index < len(items):
                    data_summary = [items[engine_res.selected_item_index]]
            elif current_state == IVRState.SCHEMES:
                items = context.get("scheme_items") or []
                if 0 <= engine_res.selected_item_index < len(items):
                    data_summary = [items[engine_res.selected_item_index]]

        # 8. Check if call completed/terminated
        ended_at = None
        if engine_res.next_status in (IVRStatus.COMPLETED, IVRStatus.TERMINATED):
            ended_at = now_utc.isoformat()

        # 9. Update session in repository
        IVRRepository.update_session_state(
            conn=conn,
            session_id=session_id,
            current_state=engine_res.next_state.value,
            status=engine_res.next_status.value,
            invalid_attempt_count=engine_res.retry_count,
            context=context,
            ended_at=ended_at,
        )

        # 10. Persist event
        existing_cb = cb_record or IVRRepository.get_callback_request(conn, session_id)
        event_payload = {
            "next_state": engine_res.next_state.value,
            "next_status": engine_res.next_status.value,
            "prompt_text": engine_res.prompt_text,
            "accepted_digits": engine_res.accepted_digits,
            "actions": [a.model_dump() for a in engine_res.actions],
            "retry_count": engine_res.retry_count,
            "data_summary": data_summary,
        }
        IVRRepository.append_event(
            conn=conn,
            session_id=session_id,
            event_type=IVREventType.STATE_TRANSITIONED.value,
            state_before=current_state.value,
            state_after=engine_res.next_state.value,
            digit=normalized_digit,
            prompt_key=engine_res.prompt_key.value,
            idempotency_key=req.idempotency_key,
            safe_payload=event_payload,
        )

        return IVRSessionResponse(
            session_id=session_id,
            state=engine_res.next_state,
            previous_state=current_state,
            status=engine_res.next_status,
            prompt_key=engine_res.prompt_key.value,
            prompt_text=engine_res.prompt_text,
            accepted_digits=engine_res.accepted_digits,
            actions=engine_res.actions,
            retry_count=engine_res.retry_count,
            expires_at=session["expires_at"],
            callback_request=existing_cb,
            data_summary=data_summary,
        )

    @staticmethod
    def get_session_detail(conn: Any, session_id: str) -> IVRSessionResponse:
        IVRService._check_simulator_enabled()
        session = IVRRepository.get_session(conn, session_id)
        if not session:
            raise EntityNotFoundException("IVRSession", session_id)

        cb = IVRRepository.get_callback_request(conn, session_id)
        curr_state = IVRState(session["current_state"])
        prompt_key = IVREngine._state_to_default_prompt_key(curr_state)
        language = session.get("language") or settings.IVR_DEFAULT_LANGUAGE
        prompt_text = AudioCatalog.get_prompt_text(prompt_key, language=language)

        accepted_digits = []
        if curr_state == IVRState.WELCOME:
            accepted_digits = ["1", "2"]
        elif curr_state == IVRState.CONSENT:
            accepted_digits = ["1", "2"]
        elif curr_state == IVRState.IDENTITY:
            accepted_digits = ["1", "0", "9"]
        elif curr_state in (IVRState.MAIN_MENU, IVRState.TRAINING, IVRState.SCHEMES):
            accepted_digits = ["1", "2", "3", "0", "#", "9"]
        elif curr_state in (IVRState.REFERRAL_STATUS, IVRState.CALLBACK_REQUEST):
            accepted_digits = ["2", "9", "#"]

        actions = [
            IVRAction(
                action_type="play_prompt"
                if session["status"] == "active"
                else "hangup",
                prompt_key=prompt_key.value,
                text=prompt_text,
                language=language,
                allowed_digits=accepted_digits,
            )
        ]

        return IVRSessionResponse(
            session_id=session_id,
            state=curr_state,
            status=IVRStatus(session["status"]),
            prompt_key=prompt_key.value,
            prompt_text=prompt_text,
            accepted_digits=accepted_digits,
            actions=actions,
            retry_count=session.get("invalid_attempt_count", 0),
            expires_at=session["expires_at"],
            callback_request=cb,
        )

    @staticmethod
    def get_session_events(conn: Any, session_id: str) -> List[IVREventResponse]:
        IVRService._check_simulator_enabled()
        session = IVRRepository.get_session(conn, session_id)
        if not session:
            raise EntityNotFoundException("IVRSession", session_id)

        raw_events = IVRRepository.get_events_by_session(conn, session_id)
        sanitized_responses = []
        for e in raw_events:
            sanitized_payload = sanitize_payload_for_logging(
                e.get("safe_payload") or {}
            )
            sanitized_responses.append(
                IVREventResponse(
                    id=e["id"],
                    session_id=e["session_id"],
                    event_type=e["event_type"],
                    state_before=e["state_before"],
                    state_after=e["state_after"],
                    digit=e.get("digit"),
                    prompt_key=e["prompt_key"],
                    created_at=e["created_at"],
                    safe_payload=sanitized_payload,
                )
            )
        return sanitized_responses

    @staticmethod
    def force_expire_session(conn: Any, session_id: str) -> IVRSessionResponse:
        """Development and testing endpoint to trigger explicit session expiry."""
        IVRService._check_simulator_enabled()
        session = IVRRepository.get_session(conn, session_id)
        if not session:
            raise EntityNotFoundException("IVRSession", session_id)

        IVRRepository.expire_session(conn, session_id)
        language = session.get("language") or settings.IVR_DEFAULT_LANGUAGE
        expired_text = AudioCatalog.get_prompt_text(
            PromptKey.SESSION_EXPIRED, language=language
        )

        IVRRepository.append_event(
            conn=conn,
            session_id=session_id,
            event_type=IVREventType.SESSION_EXPIRED.value,
            state_before=session["current_state"],
            state_after=IVRState.EXPIRED.value,
            digit=None,
            prompt_key=PromptKey.SESSION_EXPIRED.value,
            safe_payload={"prompt_text": expired_text},
        )

        return IVRSessionResponse(
            session_id=session_id,
            state=IVRState.EXPIRED,
            previous_state=IVRState(session["current_state"]),
            status=IVRStatus.EXPIRED,
            prompt_key=PromptKey.SESSION_EXPIRED.value,
            prompt_text=expired_text,
            accepted_digits=[],
            actions=[
                IVRAction(
                    action_type="hangup",
                    prompt_key=PromptKey.SESSION_EXPIRED.value,
                    text=expired_text,
                    language=language,
                )
            ],
            retry_count=session.get("invalid_attempt_count", 0),
            expires_at=session["expires_at"],
            callback_request=IVRRepository.get_callback_request(conn, session_id),
        )
