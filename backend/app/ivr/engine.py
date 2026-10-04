from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from app.ivr.constants import (
    IVRState,
    IVRStatus,
    IVRCallbackReason,
    PromptKey,
    DEFAULT_LANGUAGE,
    DEFAULT_MAX_RETRIES,
)
from app.ivr.audio_catalog import AudioCatalog
from app.ivr.schemas import IVRAction


@dataclass
class EngineResult:
    next_state: IVRState
    next_status: IVRStatus
    prompt_key: PromptKey
    prompt_text: str
    accepted_digits: List[str]
    actions: List[IVRAction]
    retry_count: int = 0
    intent: Optional[str] = None
    callback_reason: Optional[IVRCallbackReason] = None
    selected_item_index: Optional[int] = None
    format_kwargs: Dict[str, Any] = field(default_factory=dict)


class IVREngine:
    """
    Pure deterministic IVR state machine.
    Decoupled entirely from database queries and external telephony provider SDKs.
    """

    @classmethod
    def get_initial_state(cls, language: str = DEFAULT_LANGUAGE) -> EngineResult:
        """Returns the entry-point state and prompt for a newly initiated IVR call."""
        text = AudioCatalog.get_prompt_text(PromptKey.WELCOME, language=language)
        action = IVRAction(
            action_type="play_prompt",
            prompt_key=PromptKey.WELCOME.value,
            text=text,
            language=language,
            allowed_digits=["1", "2"],
        )
        return EngineResult(
            next_state=IVRState.WELCOME,
            next_status=IVRStatus.ACTIVE,
            prompt_key=PromptKey.WELCOME,
            prompt_text=text,
            accepted_digits=["1", "2"],
            actions=[action],
            retry_count=0,
            intent="session_started",
        )

    @classmethod
    def transition(
        cls,
        current_state: IVRState,
        digit: Optional[str],
        invalid_attempt_count: int = 0,
        max_retries: int = DEFAULT_MAX_RETRIES,
        language: str = DEFAULT_LANGUAGE,
        context: Optional[Dict[str, Any]] = None,
        is_expired: bool = False,
    ) -> EngineResult:
        """
        Calculates the next deterministic state given current state, input digit, and context.
        """
        ctx = context or {}

        # 1. Enforce session expiry check
        if is_expired or current_state == IVRState.EXPIRED:
            text = AudioCatalog.get_prompt_text(
                PromptKey.SESSION_EXPIRED, language=language
            )
            return EngineResult(
                next_state=IVRState.EXPIRED,
                next_status=IVRStatus.EXPIRED,
                prompt_key=PromptKey.SESSION_EXPIRED,
                prompt_text=text,
                accepted_digits=[],
                actions=[
                    IVRAction(
                        action_type="hangup",
                        prompt_key=PromptKey.SESSION_EXPIRED.value,
                        text=text,
                        language=language,
                    )
                ],
                retry_count=invalid_attempt_count,
                intent="session_expired",
            )

        # 2. Terminal state check
        if current_state == IVRState.GOODBYE:
            text = AudioCatalog.get_prompt_text(PromptKey.GOODBYE, language=language)
            return EngineResult(
                next_state=IVRState.GOODBYE,
                next_status=IVRStatus.COMPLETED,
                prompt_key=PromptKey.GOODBYE,
                prompt_text=text,
                accepted_digits=[],
                actions=[
                    IVRAction(
                        action_type="hangup",
                        prompt_key=PromptKey.GOODBYE.value,
                        text=text,
                        language=language,
                    )
                ],
                retry_count=invalid_attempt_count,
                intent="end_call",
            )

        normalized_digit = str(digit).strip() if digit is not None else ""

        # Dispatch based on current state
        if current_state == IVRState.WELCOME:
            return cls._handle_welcome(
                normalized_digit, invalid_attempt_count, max_retries, language, ctx
            )

        elif current_state == IVRState.CONSENT:
            return cls._handle_consent(
                normalized_digit, invalid_attempt_count, max_retries, language, ctx
            )

        elif current_state == IVRState.IDENTITY:
            return cls._handle_identity(
                normalized_digit, invalid_attempt_count, max_retries, language, ctx
            )

        elif current_state == IVRState.MAIN_MENU:
            return cls._handle_main_menu(
                normalized_digit, invalid_attempt_count, max_retries, language, ctx
            )

        elif current_state == IVRState.TRAINING:
            return cls._handle_training(
                normalized_digit, invalid_attempt_count, max_retries, language, ctx
            )

        elif current_state == IVRState.SCHEMES:
            return cls._handle_schemes(
                normalized_digit, invalid_attempt_count, max_retries, language, ctx
            )

        elif current_state == IVRState.REFERRAL_STATUS:
            return cls._handle_referral_status(
                normalized_digit, invalid_attempt_count, max_retries, language, ctx
            )

        elif current_state == IVRState.CALLBACK_REQUEST:
            return cls._handle_callback_request(
                normalized_digit, invalid_attempt_count, max_retries, language, ctx
            )

        elif current_state == IVRState.ERROR_RETRY:
            return cls._handle_error_retry(
                normalized_digit, invalid_attempt_count, max_retries, language, ctx
            )

        # Catch-all fallback
        return cls._handle_invalid_input(
            current_state, invalid_attempt_count, max_retries, language, ["1", "2"]
        )

    # -------------------------------------------------------------------------
    # STATE HANDLERS
    # -------------------------------------------------------------------------

    @classmethod
    def _handle_welcome(
        cls, digit: str, retries: int, max_retries: int, lang: str, ctx: Dict[str, Any]
    ) -> EngineResult:
        if digit == "1":
            text = AudioCatalog.get_prompt_text(PromptKey.CONSENT, language=lang)
            return EngineResult(
                next_state=IVRState.CONSENT,
                next_status=IVRStatus.ACTIVE,
                prompt_key=PromptKey.CONSENT,
                prompt_text=text,
                accepted_digits=["1", "2"],
                actions=[
                    IVRAction(
                        action_type="play_prompt",
                        prompt_key=PromptKey.CONSENT.value,
                        text=text,
                        language=lang,
                        allowed_digits=["1", "2"],
                    )
                ],
                retry_count=0,
            )
        elif digit == "2":
            text = AudioCatalog.get_prompt_text(PromptKey.GOODBYE, language=lang)
            return EngineResult(
                next_state=IVRState.GOODBYE,
                next_status=IVRStatus.COMPLETED,
                prompt_key=PromptKey.GOODBYE,
                prompt_text=text,
                accepted_digits=[],
                actions=[
                    IVRAction(
                        action_type="hangup",
                        prompt_key=PromptKey.GOODBYE.value,
                        text=text,
                        language=lang,
                    )
                ],
                retry_count=0,
                intent="end_call",
            )
        return cls._handle_invalid_input(
            IVRState.WELCOME, retries, max_retries, lang, ["1", "2"]
        )

    @classmethod
    def _handle_consent(
        cls, digit: str, retries: int, max_retries: int, lang: str, ctx: Dict[str, Any]
    ) -> EngineResult:
        if digit == "1":
            text = AudioCatalog.get_prompt_text(PromptKey.IDENTITY, language=lang)
            return EngineResult(
                next_state=IVRState.IDENTITY,
                next_status=IVRStatus.ACTIVE,
                prompt_key=PromptKey.IDENTITY,
                prompt_text=text,
                accepted_digits=["1", "0", "9"],
                actions=[
                    IVRAction(
                        action_type="play_prompt",
                        prompt_key=PromptKey.IDENTITY.value,
                        text=text,
                        language=lang,
                        allowed_digits=["1", "0", "9"],
                    )
                ],
                retry_count=0,
                intent="grant_consent",
            )
        elif digit == "2":
            text = AudioCatalog.get_prompt_text(
                PromptKey.CONSENT_REFUSED, language=lang
            )
            return EngineResult(
                next_state=IVRState.GOODBYE,
                next_status=IVRStatus.TERMINATED,
                prompt_key=PromptKey.CONSENT_REFUSED,
                prompt_text=text,
                accepted_digits=[],
                actions=[
                    IVRAction(
                        action_type="hangup",
                        prompt_key=PromptKey.CONSENT_REFUSED.value,
                        text=text,
                        language=lang,
                    )
                ],
                retry_count=0,
                intent="refuse_consent",
            )
        return cls._handle_invalid_input(
            IVRState.CONSENT, retries, max_retries, lang, ["1", "2"]
        )

    @classmethod
    def _handle_identity(
        cls, digit: str, retries: int, max_retries: int, lang: str, ctx: Dict[str, Any]
    ) -> EngineResult:
        if digit in ("1", "9"):
            text = AudioCatalog.get_prompt_text(PromptKey.MAIN_MENU, language=lang)
            return EngineResult(
                next_state=IVRState.MAIN_MENU,
                next_status=IVRStatus.ACTIVE,
                prompt_key=PromptKey.MAIN_MENU,
                prompt_text=text,
                accepted_digits=["1", "2", "3", "0", "#", "9"],
                actions=[
                    IVRAction(
                        action_type="play_prompt",
                        prompt_key=PromptKey.MAIN_MENU.value,
                        text=text,
                        language=lang,
                        allowed_digits=["1", "2", "3", "0", "#", "9"],
                    )
                ],
                retry_count=0,
            )
        elif digit == "0":
            text = AudioCatalog.get_prompt_text(
                PromptKey.CALLBACK_CONFIRMED, language=lang
            )
            return EngineResult(
                next_state=IVRState.CALLBACK_REQUEST,
                next_status=IVRStatus.ACTIVE,
                prompt_key=PromptKey.CALLBACK_CONFIRMED,
                prompt_text=text,
                accepted_digits=["2", "9", "#"],
                actions=[
                    IVRAction(
                        action_type="play_prompt",
                        prompt_key=PromptKey.CALLBACK_CONFIRMED.value,
                        text=text,
                        language=lang,
                        allowed_digits=["2", "9", "#"],
                    )
                ],
                retry_count=0,
                intent="create_callback",
                callback_reason=IVRCallbackReason.GENERAL_HELP,
            )
        elif digit == "#":
            text = AudioCatalog.get_prompt_text(PromptKey.IDENTITY, language=lang)
            return EngineResult(
                next_state=IVRState.IDENTITY,
                next_status=IVRStatus.ACTIVE,
                prompt_key=PromptKey.IDENTITY,
                prompt_text=text,
                accepted_digits=["1", "0", "9"],
                actions=[
                    IVRAction(
                        action_type="play_prompt",
                        prompt_key=PromptKey.IDENTITY.value,
                        text=text,
                        language=lang,
                        allowed_digits=["1", "0", "9"],
                    )
                ],
                retry_count=retries,
            )
        return cls._handle_invalid_input(
            IVRState.IDENTITY, retries, max_retries, lang, ["1", "0", "9"]
        )

    @classmethod
    def _handle_main_menu(
        cls, digit: str, retries: int, max_retries: int, lang: str, ctx: Dict[str, Any]
    ) -> EngineResult:
        if digit == "1":
            text = AudioCatalog.get_prompt_text(PromptKey.TRAINING_MENU, language=lang)
            return EngineResult(
                next_state=IVRState.TRAINING,
                next_status=IVRStatus.ACTIVE,
                prompt_key=PromptKey.TRAINING_MENU,
                prompt_text=text,
                accepted_digits=["1", "2", "3", "0", "9", "#"],
                actions=[
                    IVRAction(
                        action_type="play_prompt",
                        prompt_key=PromptKey.TRAINING_MENU.value,
                        text=text,
                        language=lang,
                        allowed_digits=["1", "2", "3", "0", "9", "#"],
                    )
                ],
                retry_count=0,
            )
        elif digit == "2":
            text = AudioCatalog.get_prompt_text(PromptKey.SCHEME_MENU, language=lang)
            return EngineResult(
                next_state=IVRState.SCHEMES,
                next_status=IVRStatus.ACTIVE,
                prompt_key=PromptKey.SCHEME_MENU,
                prompt_text=text,
                accepted_digits=["1", "2", "3", "0", "9", "#"],
                actions=[
                    IVRAction(
                        action_type="play_prompt",
                        prompt_key=PromptKey.SCHEME_MENU.value,
                        text=text,
                        language=lang,
                        allowed_digits=["1", "2", "3", "0", "9", "#"],
                    )
                ],
                retry_count=0,
            )
        elif digit == "3":
            # Referral status
            has_ben = bool(ctx.get("beneficiary_id"))
            if has_ben and ctx.get("referral_summary"):
                summary = ctx.get("referral_summary")
                text = AudioCatalog.get_prompt_text(
                    PromptKey.REFERRAL_STATUS_IDENTIFIED, language=lang, summary=summary
                )
                key = PromptKey.REFERRAL_STATUS_IDENTIFIED
            else:
                text = AudioCatalog.get_prompt_text(
                    PromptKey.REFERRAL_STATUS, language=lang
                )
                key = PromptKey.REFERRAL_STATUS

            return EngineResult(
                next_state=IVRState.REFERRAL_STATUS,
                next_status=IVRStatus.ACTIVE,
                prompt_key=key,
                prompt_text=text,
                accepted_digits=["0", "9", "#"],
                actions=[
                    IVRAction(
                        action_type="play_prompt",
                        prompt_key=key.value,
                        text=text,
                        language=lang,
                        allowed_digits=["0", "9", "#"],
                    )
                ],
                retry_count=0,
            )
        elif digit == "0":
            text = AudioCatalog.get_prompt_text(
                PromptKey.CALLBACK_CONFIRMED, language=lang
            )
            return EngineResult(
                next_state=IVRState.CALLBACK_REQUEST,
                next_status=IVRStatus.ACTIVE,
                prompt_key=PromptKey.CALLBACK_CONFIRMED,
                prompt_text=text,
                accepted_digits=["2", "9", "#"],
                actions=[
                    IVRAction(
                        action_type="play_prompt",
                        prompt_key=PromptKey.CALLBACK_CONFIRMED.value,
                        text=text,
                        language=lang,
                        allowed_digits=["2", "9", "#"],
                    )
                ],
                retry_count=0,
                intent="create_callback",
                callback_reason=IVRCallbackReason.GENERAL_HELP,
            )
        elif digit in ("#", "9"):
            text = AudioCatalog.get_prompt_text(PromptKey.MAIN_MENU, language=lang)
            return EngineResult(
                next_state=IVRState.MAIN_MENU,
                next_status=IVRStatus.ACTIVE,
                prompt_key=PromptKey.MAIN_MENU,
                prompt_text=text,
                accepted_digits=["1", "2", "3", "0", "#", "9"],
                actions=[
                    IVRAction(
                        action_type="play_prompt",
                        prompt_key=PromptKey.MAIN_MENU.value,
                        text=text,
                        language=lang,
                        allowed_digits=["1", "2", "3", "0", "#", "9"],
                    )
                ],
                retry_count=retries,
            )
        return cls._handle_invalid_input(
            IVRState.MAIN_MENU,
            retries,
            max_retries,
            lang,
            ["1", "2", "3", "0", "#", "9"],
        )

    @classmethod
    def _handle_training(
        cls, digit: str, retries: int, max_retries: int, lang: str, ctx: Dict[str, Any]
    ) -> EngineResult:
        if digit in ("1", "2", "3"):
            idx = int(digit) - 1
            training_items = ctx.get("training_items") or []
            if idx < len(training_items):
                item = training_items[idx]
                summary = item.get("title", f"प्रशिक्षण कोर्स {digit}")
                text = AudioCatalog.get_prompt_text(
                    PromptKey.TRAINING_DETAIL, language=lang, summary=summary
                )
            else:
                text = AudioCatalog.get_prompt_text(PromptKey.NO_RESULTS, language=lang)

            return EngineResult(
                next_state=IVRState.TRAINING,
                next_status=IVRStatus.ACTIVE,
                prompt_key=PromptKey.TRAINING_DETAIL
                if idx < len(training_items)
                else PromptKey.NO_RESULTS,
                prompt_text=text,
                accepted_digits=["1", "2", "3", "0", "9", "#"],
                actions=[
                    IVRAction(
                        action_type="play_prompt",
                        prompt_key=PromptKey.TRAINING_DETAIL.value,
                        text=text,
                        language=lang,
                        allowed_digits=["1", "2", "3", "0", "9", "#"],
                    )
                ],
                retry_count=0,
                selected_item_index=idx,
            )
        elif digit == "0":
            text = AudioCatalog.get_prompt_text(
                PromptKey.CALLBACK_CONFIRMED, language=lang
            )
            return EngineResult(
                next_state=IVRState.CALLBACK_REQUEST,
                next_status=IVRStatus.ACTIVE,
                prompt_key=PromptKey.CALLBACK_CONFIRMED,
                prompt_text=text,
                accepted_digits=["2", "9", "#"],
                actions=[
                    IVRAction(
                        action_type="play_prompt",
                        prompt_key=PromptKey.CALLBACK_CONFIRMED.value,
                        text=text,
                        language=lang,
                        allowed_digits=["2", "9", "#"],
                    )
                ],
                retry_count=0,
                intent="create_callback",
                callback_reason=IVRCallbackReason.TRAINING_SUPPORT,
            )
        elif digit == "9":
            text = AudioCatalog.get_prompt_text(PromptKey.MAIN_MENU, language=lang)
            return EngineResult(
                next_state=IVRState.MAIN_MENU,
                next_status=IVRStatus.ACTIVE,
                prompt_key=PromptKey.MAIN_MENU,
                prompt_text=text,
                accepted_digits=["1", "2", "3", "0", "#", "9"],
                actions=[
                    IVRAction(
                        action_type="play_prompt",
                        prompt_key=PromptKey.MAIN_MENU.value,
                        text=text,
                        language=lang,
                        allowed_digits=["1", "2", "3", "0", "#", "9"],
                    )
                ],
                retry_count=0,
            )
        elif digit == "#":
            text = AudioCatalog.get_prompt_text(PromptKey.TRAINING_MENU, language=lang)
            return EngineResult(
                next_state=IVRState.TRAINING,
                next_status=IVRStatus.ACTIVE,
                prompt_key=PromptKey.TRAINING_MENU,
                prompt_text=text,
                accepted_digits=["1", "2", "3", "0", "9", "#"],
                actions=[
                    IVRAction(
                        action_type="play_prompt",
                        prompt_key=PromptKey.TRAINING_MENU.value,
                        text=text,
                        language=lang,
                        allowed_digits=["1", "2", "3", "0", "9", "#"],
                    )
                ],
                retry_count=retries,
            )
        return cls._handle_invalid_input(
            IVRState.TRAINING,
            retries,
            max_retries,
            lang,
            ["1", "2", "3", "0", "9", "#"],
        )

    @classmethod
    def _handle_schemes(
        cls, digit: str, retries: int, max_retries: int, lang: str, ctx: Dict[str, Any]
    ) -> EngineResult:
        if digit in ("1", "2", "3"):
            idx = int(digit) - 1
            scheme_items = ctx.get("scheme_items") or []
            if idx < len(scheme_items):
                item = scheme_items[idx]
                summary = item.get("title", f"योजना विकल्प {digit}")
                text = AudioCatalog.get_prompt_text(
                    PromptKey.SCHEME_DETAIL, language=lang, summary=summary
                )
            else:
                text = AudioCatalog.get_prompt_text(PromptKey.NO_RESULTS, language=lang)

            return EngineResult(
                next_state=IVRState.SCHEMES,
                next_status=IVRStatus.ACTIVE,
                prompt_key=PromptKey.SCHEME_DETAIL
                if idx < len(scheme_items)
                else PromptKey.NO_RESULTS,
                prompt_text=text,
                accepted_digits=["1", "2", "3", "0", "9", "#"],
                actions=[
                    IVRAction(
                        action_type="play_prompt",
                        prompt_key=PromptKey.SCHEME_DETAIL.value,
                        text=text,
                        language=lang,
                        allowed_digits=["1", "2", "3", "0", "9", "#"],
                    )
                ],
                retry_count=0,
                selected_item_index=idx,
            )
        elif digit == "0":
            text = AudioCatalog.get_prompt_text(
                PromptKey.CALLBACK_CONFIRMED, language=lang
            )
            return EngineResult(
                next_state=IVRState.CALLBACK_REQUEST,
                next_status=IVRStatus.ACTIVE,
                prompt_key=PromptKey.CALLBACK_CONFIRMED,
                prompt_text=text,
                accepted_digits=["2", "9", "#"],
                actions=[
                    IVRAction(
                        action_type="play_prompt",
                        prompt_key=PromptKey.CALLBACK_CONFIRMED.value,
                        text=text,
                        language=lang,
                        allowed_digits=["2", "9", "#"],
                    )
                ],
                retry_count=0,
                intent="create_callback",
                callback_reason=IVRCallbackReason.SCHEME_INFORMATION,
            )
        elif digit == "9":
            text = AudioCatalog.get_prompt_text(PromptKey.MAIN_MENU, language=lang)
            return EngineResult(
                next_state=IVRState.MAIN_MENU,
                next_status=IVRStatus.ACTIVE,
                prompt_key=PromptKey.MAIN_MENU,
                prompt_text=text,
                accepted_digits=["1", "2", "3", "0", "#", "9"],
                actions=[
                    IVRAction(
                        action_type="play_prompt",
                        prompt_key=PromptKey.MAIN_MENU.value,
                        text=text,
                        language=lang,
                        allowed_digits=["1", "2", "3", "0", "#", "9"],
                    )
                ],
                retry_count=0,
            )
        elif digit == "#":
            text = AudioCatalog.get_prompt_text(PromptKey.SCHEME_MENU, language=lang)
            return EngineResult(
                next_state=IVRState.SCHEMES,
                next_status=IVRStatus.ACTIVE,
                prompt_key=PromptKey.SCHEME_MENU,
                prompt_text=text,
                accepted_digits=["1", "2", "3", "0", "9", "#"],
                actions=[
                    IVRAction(
                        action_type="play_prompt",
                        prompt_key=PromptKey.SCHEME_MENU.value,
                        text=text,
                        language=lang,
                        allowed_digits=["1", "2", "3", "0", "9", "#"],
                    )
                ],
                retry_count=retries,
            )
        return cls._handle_invalid_input(
            IVRState.SCHEMES, retries, max_retries, lang, ["1", "2", "3", "0", "9", "#"]
        )

    @classmethod
    def _handle_referral_status(
        cls, digit: str, retries: int, max_retries: int, lang: str, ctx: Dict[str, Any]
    ) -> EngineResult:
        if digit == "0":
            text = AudioCatalog.get_prompt_text(
                PromptKey.CALLBACK_CONFIRMED, language=lang
            )
            return EngineResult(
                next_state=IVRState.CALLBACK_REQUEST,
                next_status=IVRStatus.ACTIVE,
                prompt_key=PromptKey.CALLBACK_CONFIRMED,
                prompt_text=text,
                accepted_digits=["2", "9", "#"],
                actions=[
                    IVRAction(
                        action_type="play_prompt",
                        prompt_key=PromptKey.CALLBACK_CONFIRMED.value,
                        text=text,
                        language=lang,
                        allowed_digits=["2", "9", "#"],
                    )
                ],
                retry_count=0,
                intent="create_callback",
                callback_reason=IVRCallbackReason.REFERRAL_STATUS,
            )
        elif digit == "9":
            text = AudioCatalog.get_prompt_text(PromptKey.MAIN_MENU, language=lang)
            return EngineResult(
                next_state=IVRState.MAIN_MENU,
                next_status=IVRStatus.ACTIVE,
                prompt_key=PromptKey.MAIN_MENU,
                prompt_text=text,
                accepted_digits=["1", "2", "3", "0", "#", "9"],
                actions=[
                    IVRAction(
                        action_type="play_prompt",
                        prompt_key=PromptKey.MAIN_MENU.value,
                        text=text,
                        language=lang,
                        allowed_digits=["1", "2", "3", "0", "#", "9"],
                    )
                ],
                retry_count=0,
            )
        elif digit == "#":
            text = AudioCatalog.get_prompt_text(
                PromptKey.REFERRAL_STATUS, language=lang
            )
            return EngineResult(
                next_state=IVRState.REFERRAL_STATUS,
                next_status=IVRStatus.ACTIVE,
                prompt_key=PromptKey.REFERRAL_STATUS,
                prompt_text=text,
                accepted_digits=["0", "9", "#"],
                actions=[
                    IVRAction(
                        action_type="play_prompt",
                        prompt_key=PromptKey.REFERRAL_STATUS.value,
                        text=text,
                        language=lang,
                        allowed_digits=["0", "9", "#"],
                    )
                ],
                retry_count=retries,
            )
        return cls._handle_invalid_input(
            IVRState.REFERRAL_STATUS, retries, max_retries, lang, ["0", "9", "#"]
        )

    @classmethod
    def _handle_callback_request(
        cls, digit: str, retries: int, max_retries: int, lang: str, ctx: Dict[str, Any]
    ) -> EngineResult:
        if digit == "2":
            text = AudioCatalog.get_prompt_text(PromptKey.GOODBYE, language=lang)
            return EngineResult(
                next_state=IVRState.GOODBYE,
                next_status=IVRStatus.COMPLETED,
                prompt_key=PromptKey.GOODBYE,
                prompt_text=text,
                accepted_digits=[],
                actions=[
                    IVRAction(
                        action_type="hangup",
                        prompt_key=PromptKey.GOODBYE.value,
                        text=text,
                        language=lang,
                    )
                ],
                retry_count=0,
                intent="end_call",
            )
        elif digit == "9":
            text = AudioCatalog.get_prompt_text(PromptKey.MAIN_MENU, language=lang)
            return EngineResult(
                next_state=IVRState.MAIN_MENU,
                next_status=IVRStatus.ACTIVE,
                prompt_key=PromptKey.MAIN_MENU,
                prompt_text=text,
                accepted_digits=["1", "2", "3", "0", "#", "9"],
                actions=[
                    IVRAction(
                        action_type="play_prompt",
                        prompt_key=PromptKey.MAIN_MENU.value,
                        text=text,
                        language=lang,
                        allowed_digits=["1", "2", "3", "0", "#", "9"],
                    )
                ],
                retry_count=0,
            )
        elif digit == "#":
            text = AudioCatalog.get_prompt_text(
                PromptKey.CALLBACK_CONFIRMED, language=lang
            )
            return EngineResult(
                next_state=IVRState.CALLBACK_REQUEST,
                next_status=IVRStatus.ACTIVE,
                prompt_key=PromptKey.CALLBACK_CONFIRMED,
                prompt_text=text,
                accepted_digits=["2", "9", "#"],
                actions=[
                    IVRAction(
                        action_type="play_prompt",
                        prompt_key=PromptKey.CALLBACK_CONFIRMED.value,
                        text=text,
                        language=lang,
                        allowed_digits=["2", "9", "#"],
                    )
                ],
                retry_count=retries,
            )
        return cls._handle_invalid_input(
            IVRState.CALLBACK_REQUEST, retries, max_retries, lang, ["2", "9", "#"]
        )

    @classmethod
    def _handle_error_retry(
        cls, digit: str, retries: int, max_retries: int, lang: str, ctx: Dict[str, Any]
    ) -> EngineResult:
        if digit == "0":
            text = AudioCatalog.get_prompt_text(
                PromptKey.CALLBACK_CONFIRMED, language=lang
            )
            return EngineResult(
                next_state=IVRState.CALLBACK_REQUEST,
                next_status=IVRStatus.ACTIVE,
                prompt_key=PromptKey.CALLBACK_CONFIRMED,
                prompt_text=text,
                accepted_digits=["2", "9", "#"],
                actions=[
                    IVRAction(
                        action_type="play_prompt",
                        prompt_key=PromptKey.CALLBACK_CONFIRMED.value,
                        text=text,
                        language=lang,
                        allowed_digits=["2", "9", "#"],
                    )
                ],
                retry_count=0,
                intent="create_callback",
                callback_reason=IVRCallbackReason.GENERAL_HELP,
            )
        elif digit in ("2", "#", "9") or True:
            # Safe exit after failing error retry choices to avoid loop
            text = AudioCatalog.get_prompt_text(PromptKey.GOODBYE, language=lang)
            return EngineResult(
                next_state=IVRState.GOODBYE,
                next_status=IVRStatus.COMPLETED,
                prompt_key=PromptKey.GOODBYE,
                prompt_text=text,
                accepted_digits=[],
                actions=[
                    IVRAction(
                        action_type="hangup",
                        prompt_key=PromptKey.GOODBYE.value,
                        text=text,
                        language=lang,
                    )
                ],
                retry_count=0,
                intent="end_call",
            )

    @classmethod
    def _handle_invalid_input(
        cls,
        state: IVRState,
        retries: int,
        max_retries: int,
        lang: str,
        expected_digits: List[str],
    ) -> EngineResult:
        new_retries = retries + 1
        if new_retries >= max_retries:
            # Exceeded retries -> offer callback or goodbye
            text = AudioCatalog.get_prompt_text(PromptKey.MAX_RETRIES, language=lang)
            return EngineResult(
                next_state=IVRState.ERROR_RETRY,
                next_status=IVRStatus.ACTIVE,
                prompt_key=PromptKey.MAX_RETRIES,
                prompt_text=text,
                accepted_digits=["0", "2"],
                actions=[
                    IVRAction(
                        action_type="play_prompt",
                        prompt_key=PromptKey.MAX_RETRIES.value,
                        text=text,
                        language=lang,
                        allowed_digits=["0", "2"],
                    )
                ],
                retry_count=new_retries,
                intent="max_retries_exceeded",
            )

        # First invalid attempt -> replay current menu with invalid notice
        invalid_prefix = AudioCatalog.get_prompt_text(
            PromptKey.INVALID_INPUT, language=lang
        )
        base_prompt_key = cls._state_to_default_prompt_key(state)
        base_text = AudioCatalog.get_prompt_text(base_prompt_key, language=lang)
        combined_text = f"{invalid_prefix} {base_text}"

        return EngineResult(
            next_state=state,
            next_status=IVRStatus.ACTIVE,
            prompt_key=PromptKey.INVALID_INPUT,
            prompt_text=combined_text,
            accepted_digits=expected_digits,
            actions=[
                IVRAction(
                    action_type="play_prompt",
                    prompt_key=PromptKey.INVALID_INPUT.value,
                    text=combined_text,
                    language=lang,
                    allowed_digits=expected_digits,
                )
            ],
            retry_count=new_retries,
            intent="invalid_input",
        )

    @staticmethod
    def _state_to_default_prompt_key(state: IVRState) -> PromptKey:
        mapping = {
            IVRState.WELCOME: PromptKey.WELCOME,
            IVRState.CONSENT: PromptKey.CONSENT,
            IVRState.IDENTITY: PromptKey.IDENTITY,
            IVRState.MAIN_MENU: PromptKey.MAIN_MENU,
            IVRState.TRAINING: PromptKey.TRAINING_MENU,
            IVRState.SCHEMES: PromptKey.SCHEME_MENU,
            IVRState.REFERRAL_STATUS: PromptKey.REFERRAL_STATUS,
            IVRState.CALLBACK_REQUEST: PromptKey.CALLBACK_CONFIRMED,
            IVRState.ERROR_RETRY: PromptKey.MAX_RETRIES,
            IVRState.GOODBYE: PromptKey.GOODBYE,
            IVRState.EXPIRED: PromptKey.SESSION_EXPIRED,
        }
        return mapping.get(state, PromptKey.WELCOME)
