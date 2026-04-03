import hashlib
import time

from fastapi import Request
import redis

from backend.app.core.config import settings


class RateLimiter:
    def __init__(self, client: redis.Redis, limit: int, window_seconds: int) -> None:
        self.client = client
        self.limit = limit
        self.window_seconds = window_seconds

    def check(self, request: Request) -> tuple[bool, int]:
        identity = self._build_identity(request)
        now_window = int(time.time() // self.window_seconds)
        key = f"rate_limit:{identity}:{now_window}"
        current = self.client.incr(key)
        if current == 1:
            self.client.expire(key, self.window_seconds)
        remaining = max(self.limit - int(current), 0)
        return int(current) <= self.limit, remaining

    def _build_identity(self, request: Request) -> str:
        auth_header = request.headers.get("authorization", "")
        api_key = request.headers.get("x-api-key", "")
        client_host = request.client.host if request.client else "unknown"
        raw = f"{client_host}|{auth_header}|{api_key}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def should_skip_rate_limit(request: Request) -> bool:
    if request.url.path in {"/health", "/ready", "/metrics"}:
        return True
    return request.method == "OPTIONS"
