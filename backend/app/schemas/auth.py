from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List

class LoginRequest(BaseModel):
    email_or_phone: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    # Note: refresh_token is typically set as an HttpOnly cookie, but we can return it conditionally
    # if required by non-browser clients.

class UserScopeResponse(BaseModel):
    district_id: Optional[str] = None
    block_id: Optional[str] = None
    scope_type: str

class UserResponse(BaseModel):
    id: str
    email: Optional[str] = None
    phone: Optional[str] = None
    display_name: str
    is_active: bool
    is_superuser: bool
    roles: List[str]
    scopes: List[UserScopeResponse]

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=12)

class BootstrapAdminRequest(BaseModel):
    bootstrap_secret: str
    email: str
    password: str = Field(..., min_length=12)
    display_name: str
