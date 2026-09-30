from fastapi import APIRouter, Depends, Request, Response, Cookie, HTTPException
from app.schemas.auth import LoginRequest, TokenResponse, ChangePasswordRequest, BootstrapAdminRequest, UserResponse, UserScopeResponse
from app.services.auth_service import AuthService
from app.dependencies.auth import get_current_user, Actor, get_current_actor, require_authenticated_user
from app.database import get_db

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

@router.post("/bootstrap-admin")
def bootstrap_admin(req: BootstrapAdminRequest, request: Request):
    with get_db() as conn:
        return AuthService.bootstrap_admin(conn, req, request.client.host if request.client else "unknown")

@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, request: Request, response: Response):
    with get_db() as conn:
        res = AuthService.login(conn, req, request.client.host if request.client else "unknown", request.headers.get("user-agent", ""))
        
        # Set HttpOnly cookie for refresh token
        response.set_cookie(
            key="refresh_token",
            value=res["refresh_token"],
            httponly=True,
            secure=request.url.scheme == "https",
            samesite="lax",
            max_age=30 * 24 * 60 * 60 # 30 days
        )
        
        return {"access_token": res["access_token"], "token_type": "bearer"}

@router.post("/refresh", response_model=TokenResponse)
def refresh(request: Request, response: Response, refresh_token: str = Cookie(None)):
    if not refresh_token:
        # Fallback to authorization header or body for non-browser clients if needed
        raise HTTPException(status_code=401, detail="Refresh token missing")
        
    with get_db() as conn:
        res = AuthService.refresh(conn, refresh_token, request.client.host if request.client else "unknown", request.headers.get("user-agent", ""))
        
        response.set_cookie(
            key="refresh_token",
            value=res["refresh_token"],
            httponly=True,
            secure=request.url.scheme == "https",
            samesite="lax",
            max_age=30 * 24 * 60 * 60
        )
        
        return {"access_token": res["access_token"], "token_type": "bearer"}

@router.post("/logout")
def logout(request: Request, response: Response, actor: Actor = Depends(require_authenticated_user), refresh_token: str = Cookie(None)):
    if refresh_token:
        with get_db() as conn:
            AuthService.logout(conn, refresh_token, actor.actor_id)
    response.delete_cookie("refresh_token")
    return {"message": "Logged out successfully"}

@router.get("/me", response_model=UserResponse)
def get_me(actor: Actor = Depends(get_current_user)):
    return UserResponse(
        id=actor.db_user["id"],
        email=actor.db_user.get("email"),
        phone=actor.db_user.get("phone"),
        display_name=actor.db_user["display_name"],
        is_active=bool(actor.db_user["is_active"]),
        is_superuser=bool(actor.db_user.get("is_superuser")),
        roles=actor.roles,
        scopes=[UserScopeResponse(**s) for s in actor.scopes]
    )

@router.post("/change-password")
def change_password(req: ChangePasswordRequest, actor: Actor = Depends(get_current_user)):
    with get_db() as conn:
        AuthService.change_password(conn, actor.actor_id, req)
    return {"message": "Password changed successfully. All other sessions have been logged out."}
