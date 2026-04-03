import time
from uuid import uuid4

from fastapi import Request, status
from starlette.responses import JSONResponse

from backend.app.core.config import settings
from backend.app.core.metrics import REQUEST_COUNT, REQUEST_LATENCY
from backend.app.core.rate_limit import RateLimiter, should_skip_rate_limit
from backend.app.core.redis_client import get_redis_client

async def request_context_middleware(request: Request, call_next):
    request_id = request.headers.get("x-request-id") or str(uuid4())
    request.state.request_id = request_id
    start = time.perf_counter()

    if not should_skip_rate_limit(request):
        limiter = RateLimiter(get_redis_client(), settings.rate_limit_requests, settings.rate_limit_window_seconds)
        allowed, remaining = limiter.check(request)
        if not allowed:
            response = JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Rate limit exceeded."},
            )
            response.headers["x-request-id"] = request_id
            response.headers["x-ratelimit-limit"] = str(settings.rate_limit_requests)
            response.headers["x-ratelimit-window-seconds"] = str(settings.rate_limit_window_seconds)
            return response

    response = await call_next(request)
    duration = time.perf_counter() - start
    REQUEST_COUNT.labels(request.method, request.url.path, str(response.status_code)).inc()
    REQUEST_LATENCY.labels(request.method, request.url.path).observe(duration)
    response.headers["x-request-id"] = request_id
    if not should_skip_rate_limit(request):
        response.headers["x-ratelimit-limit"] = str(settings.rate_limit_requests)
        response.headers["x-ratelimit-window-seconds"] = str(settings.rate_limit_window_seconds)
    return response
