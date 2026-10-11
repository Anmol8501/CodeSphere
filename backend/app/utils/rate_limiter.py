"""A tiny in-memory sliding-window rate limiter.

Good enough for a single development/server process. For multiple workers or
servers, swap the storage for Redis while keeping the same dependency interface.
"""

import threading
import time
from collections import defaultdict, deque

from fastapi import Request

from app.core.config import settings
from app.core.exceptions import AppError


class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int = 60, scope: str = "default"):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.scope = scope
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()

    def __call__(self, request: Request) -> None:
        """Use as a FastAPI dependency: `dependencies=[Depends(limiter)]` (per client IP)."""
        self.check(request.client.host if request.client else "unknown")

    def check(self, key: str, message: str = "Too many attempts. Please wait a minute and try again.") -> None:
        """Count one hit for `key` (e.g. "user:42"); raise 429 when over the limit."""
        if not settings.RATE_LIMIT_ENABLED:
            return
        now = time.monotonic()
        with self._lock:
            hits = self._hits[key]
            while hits and now - hits[0] > self.window_seconds:
                hits.popleft()
            if len(hits) >= self.max_requests:
                retry_after = int(self.window_seconds - (now - hits[0])) + 1
                raise AppError(429, message, headers={"Retry-After": str(retry_after)}, code="RATE_LIMITED")
            hits.append(now)


login_rate_limiter = RateLimiter(settings.LOGIN_RATE_LIMIT_PER_MINUTE, scope="login")
register_rate_limiter = RateLimiter(settings.REGISTER_RATE_LIMIT_PER_MINUTE, scope="register")
# Code execution is expensive: limited per student so nobody can flood the judge.
run_rate_limiter = RateLimiter(settings.RUN_RATE_LIMIT_PER_MINUTE, scope="run")
submit_rate_limiter = RateLimiter(settings.SUBMIT_RATE_LIMIT_PER_MINUTE, scope="submit")
