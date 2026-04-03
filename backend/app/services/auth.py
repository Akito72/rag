import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import HTTPException, status

from backend.app.repositories.auth import AuthRepository


class AuthService:
    def __init__(
        self,
        repository: AuthRepository,
        jwt_secret_key: str,
        jwt_algorithm: str,
        access_token_expire_minutes: int,
    ) -> None:
        self.repository = repository
        self.jwt_secret_key = jwt_secret_key
        self.jwt_algorithm = jwt_algorithm
        self.access_token_expire_minutes = access_token_expire_minutes

    def register(self, email: str, password: str, workspace_id: str):
        if self.repository.get_user_by_email(email) is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already exists.")
        password_hash = self._hash_password(password)
        user = self.repository.create_user(email, password_hash)
        self.repository.add_user_to_workspace(user.id, workspace_id, role="owner")
        self.repository.session.commit()
        workspace_ids = self.repository.list_workspace_ids_for_user(user.id)
        return self._build_auth_response(user.id, workspace_ids)

    def login(self, email: str, password: str):
        user = self.repository.get_user_by_email(email)
        if user is None or not self._verify_password(password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials.")
        workspace_ids = self.repository.list_workspace_ids_for_user(user.id)
        return self._build_auth_response(user.id, workspace_ids)

    def decode_token(self, token: str) -> dict:
        try:
            return jwt.decode(token, self.jwt_secret_key, algorithms=[self.jwt_algorithm])
        except jwt.InvalidTokenError as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid bearer token.") from exc

    def _build_auth_response(self, user_id: str, workspace_ids: list[str]) -> dict:
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=self.access_token_expire_minutes)
        payload = {
            "sub": user_id,
            "workspace_ids": workspace_ids,
            "exp": expires_at,
        }
        token = jwt.encode(payload, self.jwt_secret_key, algorithm=self.jwt_algorithm)
        return {
            "access_token": token,
            "user_id": user_id,
            "workspace_ids": workspace_ids,
        }

    def _hash_password(self, password: str) -> str:
        salt = secrets.token_hex(16)
        derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000)
        return f"{salt}${derived.hex()}"

    def _verify_password(self, password: str, stored_hash: str) -> bool:
        salt, hashed = stored_hash.split("$", maxsplit=1)
        derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000)
        return hmac.compare_digest(derived.hex(), hashed)
