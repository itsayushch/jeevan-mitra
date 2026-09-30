import os
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Any, Protocol
import jwt
from passlib.context import CryptContext

# Secret constants (in a real app, read these from env)
SECRET_KEY = os.getenv("JWT_SECRET", "change-this-secret-in-production-1234567890!")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15

# Passlib context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class PasswordHasher(Protocol):
    def hash(self, password: str) -> str: ...
    def verify(self, password: str, password_hash: str) -> bool: ...

class BcryptHasher:
    def hash(self, password: str) -> str:
        return pwd_context.hash(password)
        
    def verify(self, password: str, password_hash: str) -> bool:
        return pwd_context.verify(password, password_hash)

hasher = BcryptHasher()

def create_access_token(subject: str, session_id: str, expires_delta: Optional[timedelta] = None) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
    to_encode = {"exp": expire, "sub": str(subject), "sid": session_id}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> dict:
    try:
        decoded_token = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return decoded_token
    except jwt.ExpiredSignatureError:
        raise ValueError("Token expired")
    except jwt.InvalidTokenError:
        raise ValueError("Invalid token")

def generate_refresh_token() -> str:
    """Generate a secure opaque refresh token."""
    return secrets.token_urlsafe(64)

def hash_refresh_token(token: str) -> str:
    """Hash the opaque refresh token for storage."""
    return hashlib.sha256(token.encode('utf-8')).hexdigest()
