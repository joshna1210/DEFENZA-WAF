from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.services import auth_service
from app.middlewares.security_middleware import require_role

router = APIRouter(prefix="/api/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    username: str
    password: str
    role: str = "soc_analyst"  # "admin" | "soc_analyst"


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str


@router.post("/register", response_model=TokenResponse)
async def register(payload: RegisterRequest):
    if payload.role not in ("admin", "soc_analyst"):
        raise HTTPException(status_code=400, detail="role must be admin or soc_analyst")
    try:
        await auth_service.create_user(payload.username, payload.password, payload.role)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    token = auth_service.create_access_token(payload.username, payload.role)
    return TokenResponse(access_token=token, role=payload.role)


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest):
    user = await auth_service.authenticate(payload.username, payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = auth_service.create_access_token(user["username"], user["role"])
    return TokenResponse(access_token=token, role=user["role"])


@router.get("/admin-only-check")
async def admin_only_check(user: dict = Depends(require_role("admin"))):
    return {"message": f"Hello admin {user['sub']}"}
