from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from app.ivr.constants import IVRState, IVRStatus, DEFAULT_LANGUAGE


class IVRPrompt(BaseModel):
    key: str
    text: str
    language: str = DEFAULT_LANGUAGE
    audio_asset_id: Optional[str] = None


class IVRAction(BaseModel):
    action_type: str = Field(
        default="play_prompt", description="play_prompt, collect_input, hangup"
    )
    prompt_key: str
    text: str
    language: str = DEFAULT_LANGUAGE
    allowed_digits: List[str] = Field(default_factory=list)
    timeout_seconds: Optional[int] = 10


class IVRSessionStartRequest(BaseModel):
    simulated_caller_reference: Optional[str] = Field(
        None, max_length=64, description="Optional simulated caller phone or caller ID"
    )
    beneficiary_id: Optional[str] = Field(
        None, max_length=64, description="Optional registered beneficiary ID"
    )
    language: str = Field(default=DEFAULT_LANGUAGE, max_length=16)
    idempotency_key: Optional[str] = Field(None, max_length=128)


class IVRDigitInputRequest(BaseModel):
    digit: str = Field(..., description="DTMF digit: 0-9 or #")
    idempotency_key: Optional[str] = Field(None, max_length=128)
    expected_state: Optional[str] = Field(None, max_length=32)

    @field_validator("digit")
    @classmethod
    def validate_dtmf_digit(cls, v: str) -> str:
        cleaned = v.strip()
        if cleaned not in {"0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "#"}:
            raise ValueError("Invalid DTMF digit. Must be a single digit 0-9 or #.")
        return cleaned


class IVRCallbackRequestResponse(BaseModel):
    id: str
    session_id: str
    beneficiary_id: Optional[str] = None
    callback_reason: str
    status: str
    created_at: str

    def __getitem__(self, item: str) -> Any:
        return getattr(self, item)


class IVRSessionResponse(BaseModel):
    session_id: str
    state: IVRState
    previous_state: Optional[IVRState] = None
    status: IVRStatus
    prompt_key: str
    prompt_text: str
    accepted_digits: List[str]
    actions: List[IVRAction]
    retry_count: int = 0
    expires_at: str
    callback_request: Optional[IVRCallbackRequestResponse] = None
    data_summary: Optional[List[Dict[str, Any]]] = None


class IVREventResponse(BaseModel):
    id: str
    session_id: str
    event_type: str
    state_before: str
    state_after: str
    digit: Optional[str] = None
    prompt_key: str
    created_at: str
    safe_payload: Optional[Dict[str, Any]] = None


class IVRProviderEvent(BaseModel):
    provider: str = "mock"
    call_id: Optional[str] = None
    caller_reference: Optional[str] = None
    digits: Optional[str] = None
    event_type: str = "digit_entered"
    raw_payload: Optional[Dict[str, Any]] = None
