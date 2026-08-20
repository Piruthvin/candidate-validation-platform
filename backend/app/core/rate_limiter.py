import abc
import asyncio
import logging
import re
import time
from collections.abc import Awaitable, Callable
from typing import Any

import starlette.requests
import starlette.responses
from starlette.responses import JSONResponse, Response

logger = logging.getLogger(__name__)

# ── Path-based rate limit rules ─────────────────────────────────────────────
# Each entry: (path_regex, max_requests, window_seconds)
# Order matters — first match wins.

DEFAULT_LIMITS: list[tuple[str, int, int]] = [
    (r"^/health", 120, 60),
    (r"^/api/v1/validation/", 30, 60),
    (r"^/api/v1/reports/", 20, 60),
    (r"^/api/v1/ats/", 60, 60),
]

# Paths excluded from rate limiting entirely
EXCLUDED_PATHS: list[str] = [
    r"^/health",
    r"^/openapi\.json$",
    r"^/docs",
    r"^/redoc",
]


class RateLimitStorage(abc.ABC):
    """Abstract rate-limit counter storage.

    Implementations can be in-memory (default) or Redis-backed.
    Application code never changes — swap the implementation at startup.
    """

    @abc.abstractmethod
    async def check_and_increment(
        self,
        key: str,
        max_requests: int,
        window_seconds: int,
    ) -> tuple[bool, int, int]:
        """Atomically check and increment counter for *key*.

        Returns (allowed, remaining, retry_after_seconds).
        - allowed:  True if request should be allowed
        - remaining: requests remaining in this window
        - retry_after_seconds: 0 unless rate-limited, then seconds to wait
        """

    async def clear(self) -> None:
        """Reset all counters (used in tests)."""


class MemoryRateLimitStorage(RateLimitStorage):
    """In-memory sliding-window rate-limit storage.

    Thread-/coroutine-safe via asyncio.Lock.
    """

    def __init__(self) -> None:
        self._data: dict[str, tuple[float, int]] = {}
        self._lock: asyncio.Lock = asyncio.Lock()

    async def check_and_increment(
        self,
        key: str,
        max_requests: int,
        window_seconds: int,
    ) -> tuple[bool, int, int]:
        async with self._lock:
            now = time.monotonic()
            entry = self._data.get(key)
            if entry is None:
                self._data[key] = (now, 1)
                return True, max_requests - 1, 0

            window_start, count = entry
            elapsed = now - window_start

            if elapsed > window_seconds:
                self._data[key] = (now, 1)
                return True, max_requests - 1, 0

            if count >= max_requests:
                retry_after = int(window_seconds - elapsed) + 1
                return False, 0, retry_after

            self._data[key] = (window_start, count + 1)
            return True, max_requests - count - 1, 0

    async def clear(self) -> None:
        async with self._lock:
            self._data.clear()


class RateLimiterMiddleware:
    """ASGI middleware that applies configurable rate limits per path.

    Supports IP-based (default) and API-key-based identification.
    Falls back to in-memory storage; swap in a Redis-backed storage
    without touching application code.
    """

    def __init__(
        self,
        app: Callable[[dict, Callable, Callable], Awaitable[None]],
        storage: RateLimitStorage | None = None,
        limits: list[tuple[str, int, int]] | None = None,
        excluded: list[str] | None = None,
    ) -> None:
        self.app = app
        self.storage = storage or MemoryRateLimitStorage()
        self.limits = limits or DEFAULT_LIMITS
        self.excluded_patterns = [re.compile(p) for p in (excluded or EXCLUDED_PATHS)]

    def _match_limit(self, path: str) -> tuple[int, int] | None:
        for pattern, max_req, window in self.limits:
            if re.search(pattern, path):
                return max_req, window
        return None

    def _is_excluded(self, path: str) -> bool:
        for pattern in self.excluded_patterns:
            if pattern.search(path):
                return True
        return False

    async def __call__(self, scope: dict, receive: Callable, send: Callable) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = starlette.requests.Request(scope, receive)
        path = request.url.path

        if self._is_excluded(path):
            await self.app(scope, receive, send)
            return

        limit_config = self._match_limit(path)
        if limit_config is None:
            await self.app(scope, receive, send)
            return

        max_requests, window_seconds = limit_config

        client_ip = request.client.host if request.client else "unknown"
        api_key = request.headers.get("x-api-key") or request.headers.get("X-Api-Key")
        key = f"rl:{api_key or client_ip}:{path}"

        allowed, remaining, retry_after = await self.storage.check_and_increment(
            key, max_requests, window_seconds,
        )

        if allowed:
            async def send_with_headers(message: dict[str, Any]) -> None:
                if message["type"] == "http.response.start":
                    headers = starlette.datastructures.MutableHeaders(scope=message)
                    headers["X-RateLimit-Limit"] = str(max_requests)
                    headers["X-RateLimit-Remaining"] = str(remaining)
                await send(message)

            await self.app(scope, receive, send_with_headers)
        else:
            resp = JSONResponse(
                status_code=429,
                content={"detail": "Too Many Requests"},
                headers={
                    "X-RateLimit-Limit": str(max_requests),
                    "X-RateLimit-Remaining": "0",
                    "Retry-After": str(retry_after),
                },
            )
            await resp(scope, receive, send)
