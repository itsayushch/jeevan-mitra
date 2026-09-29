from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import jwt
from app.config import settings

router = APIRouter(tags=["Auth"])

class LoginRequest(BaseModel):
    username: str
    password: str

@router.post("/login")
def login(request: LoginRequest):
    # Simple hardcoded mock users for the prototype
    mock_users = {
        "worker": {"role": "field_worker", "name": "Field Worker Demo", "id": "worker_01"},
        "counselor": {"role": "counselor", "name": "Counselor Demo", "id": "counselor_01"},
        "admin": {"role": "admin", "name": "Admin Demo", "id": "admin_01"},
        "officer": {"role": "district_officer", "name": "District Officer Demo", "id": "officer_01"}
    }
    
    if request.username not in mock_users or request.password != "password123":
        raise HTTPException(status_code=401, detail="Invalid username or password. (Hint: use password123)")
        
    user = mock_users[request.username]
    
    payload = {
        "sub": user["id"],
        "role": user["role"],
        "name": user["name"],
        "exp": datetime.now(timezone.utc) + timedelta(hours=24)
    }
    
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user
    }
