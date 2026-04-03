from dataclasses import dataclass

from fastapi import Header, HTTPException, status

from backend.app.core.config import settings


@dataclass(slots=True)
class AuthContext:
    user_id: str | None
    workspace_ids: list[str]
    is_admin: bool = False


def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    configured_key = settings.api_key
    if not configured_key:
        return
    if x_api_key != configured_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key.")

def enforce_workspace_access(auth_context: AuthContext, workspace_id: str) -> None:
    if auth_context.is_admin or "*" in auth_context.workspace_ids:
        return
    if workspace_id not in auth_context.workspace_ids:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Workspace access denied.")
