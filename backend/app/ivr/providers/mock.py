from typing import List, Dict, Any
from app.ivr.providers.base import IVRProvider
from app.ivr.schemas import IVRAction, IVRProviderEvent


class MockIVRProvider(IVRProvider):
    """
    Local mock provider for Phase 1 simulator.
    Operates completely in-process without any external telephony dependencies or API keys.
    Returns clean structured JSON actions.
    """

    @property
    def name(self) -> str:
        return "mock"

    def normalize_digit(self, raw_input: str) -> str:
        if not raw_input:
            raise ValueError("Empty DTMF input")
        cleaned = str(raw_input).strip()
        if cleaned in {"0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "#"}:
            return cleaned
        raise ValueError(f"Invalid DTMF digit: '{raw_input}'. Allowed: 0-9, #")

    def validate_webhook(self, headers: Dict[str, str], body: bytes) -> bool:
        # Mock provider requires no secret signatures
        return True

    def parse_incoming_event(self, payload: Dict[str, Any]) -> IVRProviderEvent:
        digits = payload.get("digits") or payload.get("digit")
        normalized_digits = self.normalize_digit(digits) if digits else None
        return IVRProviderEvent(
            provider="mock",
            call_id=payload.get("call_id"),
            caller_reference=payload.get("caller_reference") or payload.get("From"),
            digits=normalized_digits,
            event_type=payload.get("event_type", "digit_entered"),
            raw_payload=payload,
        )

    def render_response(self, actions: List[IVRAction]) -> List[Dict[str, Any]]:
        return [action.model_dump() for action in actions]
