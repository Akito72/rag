from fastapi import APIRouter, Depends

from backend.app.api.deps import get_auth_service
from backend.app.schemas.auth import AuthResponse, LoginRequest, RegisterRequest
from backend.app.services.auth import AuthService


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse)
def register(payload: RegisterRequest, auth_service: AuthService = Depends(get_auth_service)) -> AuthResponse:
    return AuthResponse(**auth_service.register(payload.email, payload.password, payload.workspace_id))


@router.post("/token", response_model=AuthResponse)
def login(payload: LoginRequest, auth_service: AuthService = Depends(get_auth_service)) -> AuthResponse:
    return AuthResponse(**auth_service.login(payload.email, payload.password))
