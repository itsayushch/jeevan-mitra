from pydantic import BaseModel, ConfigDict
from typing import Any, Dict, Generic, List, Optional, TypeVar
from datetime import datetime

T = TypeVar("T")

class BaseSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

class ApiResponse(BaseSchema, Generic[T]):
    data: T
    meta: Optional[Dict[str, Any]] = None

class PaginatedResponse(BaseSchema, Generic[T]):
    items: List[T]
    total: int
    limit: int
    offset: int
    has_more: bool

class ErrorDetail(BaseSchema):
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None

class ErrorResponse(BaseSchema):
    error: ErrorDetail

class PaginationParams(BaseSchema):
    limit: int = 10
    offset: int = 0
    sort: Optional[str] = None

class MessageResponse(BaseSchema):
    message: str
