from enum import Enum


class IVRState(str, Enum):
    WELCOME = "welcome"
    CONSENT = "consent"
    IDENTITY = "identity"
    MAIN_MENU = "main_menu"
    TRAINING = "training"
    SCHEMES = "schemes"
    REFERRAL_STATUS = "referral_status"
    CALLBACK_REQUEST = "callback_request"
    ERROR_RETRY = "error_retry"
    GOODBYE = "goodbye"
    EXPIRED = "expired"


class IVRStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    EXPIRED = "expired"
    TERMINATED = "terminated"
    FAILED = "failed"


class IVRCallbackReason(str, Enum):
    TRAINING_SUPPORT = "training_support"
    SCHEME_INFORMATION = "scheme_information"
    REFERRAL_STATUS = "referral_status"
    GENERAL_HELP = "general_help"
    UNKNOWN = "unknown"


class IVREventType(str, Enum):
    SESSION_STARTED = "session_started"
    INPUT_RECEIVED = "input_received"
    STATE_TRANSITIONED = "state_transitioned"
    CONSENT_RECORDED = "consent_recorded"
    CALLBACK_REQUESTED = "callback_requested"
    SESSION_EXPIRED = "session_expired"
    SESSION_COMPLETED = "session_completed"
    MAX_RETRIES_EXCEEDED = "max_retries_exceeded"
    ERROR_OCCURRED = "error_occurred"


class PromptKey(str, Enum):
    WELCOME = "WELCOME"
    CONSENT = "CONSENT"
    CONSENT_REFUSED = "CONSENT_REFUSED"
    IDENTITY = "IDENTITY"
    MAIN_MENU = "MAIN_MENU"
    TRAINING_MENU = "TRAINING_MENU"
    TRAINING_DETAIL = "TRAINING_DETAIL"
    SCHEME_MENU = "SCHEME_MENU"
    SCHEME_DETAIL = "SCHEME_DETAIL"
    REFERRAL_STATUS = "REFERRAL_STATUS"
    REFERRAL_STATUS_IDENTIFIED = "REFERRAL_STATUS_IDENTIFIED"
    CALLBACK_CONFIRMED = "CALLBACK_CONFIRMED"
    INVALID_INPUT = "INVALID_INPUT"
    MAX_RETRIES = "MAX_RETRIES"
    NO_RESULTS = "NO_RESULTS"
    SESSION_EXPIRED = "SESSION_EXPIRED"
    GOODBYE = "GOODBYE"


DEFAULT_LANGUAGE = "hi-IN"
DEFAULT_TIMEOUT_SECONDS = 600
DEFAULT_MAX_RETRIES = 2
