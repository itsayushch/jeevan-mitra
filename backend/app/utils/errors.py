from fastapi import HTTPException, status
from typing import Optional, Dict, Any

class AppError(HTTPException):
    def __init__(self, status_code: int, code: str, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=status_code,
            detail={
                "code": code,
                "message": message,
                "details": details or {}
            }
        )

class ConsentRequiredException(AppError):
    def __init__(self, consent_type: str, message: Optional[str] = None):
        msg = message or f"Consent for '{consent_type}' is required before accessing this service."
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            code="CONSENT_REQUIRED",
            message=msg,
            details={"consent_type": consent_type}
        )

class ConsentRevokedException(AppError):
    def __init__(self, consent_type: str, message: Optional[str] = None):
        msg = message or f"Consent for '{consent_type}' has been revoked. Processing is halted."
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            code="CONSENT_REVOKED",
            message=msg,
            details={"consent_type": consent_type}
        )

class UnauthorizedAccessException(AppError):
    def __init__(self, message: str = "You do not have permission to access this resource.", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            code="FORBIDDEN",
            message=message,
            details=details or {}
        )

class SessionExpiredOrInvalidException(AppError):
    def __init__(self, message: str = "Session is invalid or has expired."):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="SESSION_EXPIRED",
            message=message
        )

class EntityNotFoundException(AppError):
    def __init__(self, entity_type: str, entity_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="NOT_FOUND",
            message=f"{entity_type} '{entity_id}' not found.",
            details={"entity_type": entity_type, "entity_id": entity_id}
        )

class ValidationException(AppError):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message=message,
            details=details or {}
        )

class InvalidStateTransitionException(AppError):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="INVALID_STATE_TRANSITION",
            message=message,
            details=details or {}
        )
