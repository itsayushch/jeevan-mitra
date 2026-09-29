from fastapi import HTTPException

class DomainException(HTTPException):
    def __init__(self, code: str, message: str, status_code: int = 400, details: dict = None):
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(status_code=status_code, detail=message)

class NotFoundException(DomainException):
    def __init__(self, resource: str):
        super().__init__(
            code="NOT_FOUND",
            message=f"{resource} not found",
            status_code=404
        )

class UnauthorizedException(DomainException):
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(
            code="UNAUTHORIZED",
            message=message,
            status_code=401
        )

class ForbiddenException(DomainException):
    def __init__(self, message: str = "Forbidden"):
        super().__init__(
            code="FORBIDDEN",
            message=message,
            status_code=403
        )
