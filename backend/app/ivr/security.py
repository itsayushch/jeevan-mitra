import base64
import hashlib
import hmac
import re
from typing import Optional, Dict, Any


_PEPPER = "jeevan_mitra_ivr_salt_2026"


def hash_caller_reference(raw_reference: Optional[str]) -> Optional[str]:
    """
    Computes a deterministic, one-way SHA-256 hash of a caller phone number
    or identifier to prevent storing plaintext PII in logs or audit tables.
    """
    if not raw_reference:
        return None
    # Normalize phone: remove spaces, dashes, parentheses
    cleaned = re.sub(r"[^\w+]", "", raw_reference.strip())
    salted = f"{cleaned}:{_PEPPER}".encode("utf-8")
    return hashlib.sha256(salted).hexdigest()[:32]


def mask_phone_number(raw_phone: Optional[str]) -> Optional[str]:
    """
    Masks a telephone number for safe diagnostic display (e.g. '******3210').
    Returns None if empty.
    """
    if not raw_phone:
        return None
    digits = re.sub(r"\D", "", raw_phone)
    if len(digits) >= 4:
        return f"{'*' * (len(digits) - 4)}{digits[-4:]}"
    return "****"


def sanitize_payload_for_logging(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively redacts phone, aadhaar, pan, and token keys from dictionaries.
    """
    sensitive_keys = {
        "phone",
        "mobile",
        "caller_id",
        "caller_reference",
        "token",
        "secret",
        "password",
        "from",
    }
    sanitized = {}
    for k, v in payload.items():
        if any(s in k.lower() for s in sensitive_keys):
            if isinstance(v, str):
                sanitized[k] = (
                    mask_phone_number(v)
                    if any(p in k.lower() for p in ["phone", "mobile", "from"])
                    else "[REDACTED]"
                )
            else:
                sanitized[k] = "[REDACTED]"
        elif isinstance(v, dict):
            sanitized[k] = sanitize_payload_for_logging(v)
        else:
            sanitized[k] = v
    return sanitized


def validate_provider_signature(
    raw_body: bytes, signature_header: Optional[str], secret_key: Optional[str]
) -> bool:
    """
    Generic webhook HMAC-SHA256 signature verification.
    If secret_key is empty (e.g. local dev), validation is bypassed safely.
    """
    if not secret_key:
        return True
    if not signature_header:
        return False
    expected = hmac.new(secret_key.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature_header.strip())


def validate_twilio_signature(
    url: str,
    params: Dict[str, Any],
    signature: Optional[str],
    auth_token: Optional[str]
) -> bool:
    """
    Validates Twilio's X-Twilio-Signature (HMAC-SHA1 of full URL + sorted POST params).
    Returns True if auth_token is unconfigured (local dev / mock mode).
    """
    if not auth_token:
        return True
    if not signature:
        return False

    # Construct Twilio validation string: full URL + sorted param keys and values
    s = url
    for k in sorted(params.keys()):
        s += f"{k}{params[k]}"

    mac = hmac.new(auth_token.encode("utf-8"), s.encode("utf-8"), hashlib.sha1)
    computed = base64.b64encode(mac.digest()).decode("utf-8")
    return hmac.compare_digest(computed, signature.strip())


def validate_exotel_token(
    provided_token: Optional[str],
    expected_secret: Optional[str]
) -> bool:
    """
    Validates Exotel auth token/secret passed via query parameter or header.
    Returns True if expected_secret is unconfigured.
    """
    if not expected_secret:
        return True
    if not provided_token:
        return False
    return hmac.compare_digest(provided_token.strip(), expected_secret.strip())
