import json
import logging
import os
import re
import sys
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# Context variable for holding active request ID across async tasks
request_id_ctx_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)

# Patterns to automatically redact from log strings
REDACTION_PATTERNS = [
    # JWT Bearer tokens
    (re.compile(r"Bearer\s+[A-Za-z0-9\-_=]+\.[A-Za-z0-9\-_=]+\.?[A-Za-z0-9\-_=]*", re.IGNORECASE), "Bearer [REDACTED_JWT]"),
    (re.compile(r"ey[A-Za-z0-9\-_]{15,}\.[A-Za-z0-9\-_]{15,}\.[A-Za-z0-9\-_]{10,}", re.IGNORECASE), "[REDACTED_JWT]"),
    # Passwords in query strings or JSON key-values
    (re.compile(r'(["\']?(?:password|passphrase|secret|client_secret)["\']?\s*[:=]\s*["\'])([^"\']+)(["\'])', re.IGNORECASE), r'\1[REDACTED]\3'),
    # API keys and tokens in JSON / query
    (re.compile(r'(["\']?(?:api_key|apiKey|token|access_token|refresh_token|jwt_secret)["\']?\s*[:=]\s*["\'])([^"\']+)(["\'])', re.IGNORECASE), r'\1[REDACTED]\3'),
    # Aadhaar numbers (12 digits with or without spaces)
    (re.compile(r'\b\d{4}\s\d{4}\s\d{4}\b'), "[REDACTED_AADHAAR]"),
    (re.compile(r'\b(?<!\d)\d{12}(?!\d)\b'), "[REDACTED_AADHAAR]"),
    # Indian mobile numbers (10 digits starting with 6-9, optional +91 prefix)
    (re.compile(r'(?:\+?91[\s-]?)?[6-9]\d{9}\b'), "[REDACTED_PHONE]"),
    # Email addresses
    (re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b'), "[REDACTED_EMAIL]"),
]

SENSITIVE_KEYS = {
    "password", "passphrase", "secret", "client_secret", "jwt_secret",
    "token", "access_token", "refresh_token", "api_key", "authorization",
    "cookie", "set-cookie", "x-worker-api-key", "aadhaar", "phone", "mobile",
    "raw_transcript", "diary_notes", "caseworker_notes", "notes", "evidence_path",
    "credentials", "private_key"
}


def redact_text(text: str) -> str:
    """Sanitizes sensitive patterns in arbitrary strings."""
    if not isinstance(text, str):
        return text
    result = text
    for pattern, replacement in REDACTION_PATTERNS:
        result = pattern.sub(replacement, result)
    return result


def redact_data(data: Any) -> Any:
    """Recursively redacts sensitive keys and values in nested dictionaries or lists."""
    if isinstance(data, dict):
        cleaned = {}
        for k, v in data.items():
            if str(k).lower() in SENSITIVE_KEYS:
                cleaned[k] = "[REDACTED]"
            else:
                cleaned[k] = redact_data(v)
        return cleaned
    elif isinstance(data, list):
        return [redact_data(item) for item in data]
    elif isinstance(data, str):
        return redact_text(data)
    return data


class RedactingJsonFormatter(logging.Formatter):
    """Outputs machine-readable JSON logs with automatic PII/credential redaction."""
    def format(self, record: logging.LogRecord) -> str:
        req_id = request_id_ctx_var.get() or getattr(record, "request_id", None)
        raw_msg = record.getMessage()
        sanitized_msg = redact_text(raw_msg)

        log_entry: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": sanitized_msg,
            "request_id": req_id,
        }
        if hasattr(record, "props") and isinstance(record.props, dict):
            log_entry["props"] = redact_data(record.props)
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)


class RedactingConsoleFormatter(logging.Formatter):
    """Outputs human-readable console logs with automatic PII/credential redaction."""
    def format(self, record: logging.LogRecord) -> str:
        req_id = request_id_ctx_var.get() or getattr(record, "request_id", None)
        req_prefix = f" [{req_id}]" if req_id else ""
        raw_msg = record.getMessage()
        sanitized_msg = redact_text(raw_msg)
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        formatted = f"{timestamp} [{record.levelname}] [{record.name}]{req_prefix}: {sanitized_msg}"
        if record.exc_info:
            formatted += f"\n{self.formatException(record.exc_info)}"
        return formatted


def setup_logger(name: str = "jeevanmitra", force_json: bool = False) -> logging.Logger:
    """Configures structured logger with redaction filters."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    use_json = (
        force_json
        or (os.getenv("LOG_FORMAT", "").lower() == "json")
        or (os.getenv("APP_ENV", "").lower() in ["production", "staging"])
    )

    handler = logging.StreamHandler(sys.stdout)
    if use_json:
        handler.setFormatter(RedactingJsonFormatter())
    else:
        handler.setFormatter(RedactingConsoleFormatter())

    logger.addHandler(handler)
    logger.propagate = False
    return logger
