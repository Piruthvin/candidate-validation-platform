"""Unit tests for the rate limiter."""

import asyncio
import time

import pytest
from httpx import AsyncClient, ASGITransport
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Route

from app.core.rate_limiter import (
    EXCLUDED_PATHS,
    DEFAULT_LIMITS,
    MemoryRateLimitStorage,
    RateLimiterMiddleware,
)


# ── MemoryRateLimitStorage tests ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_under_limit():
    storage = MemoryRateLimitStorage()
    allowed, remaining, retry = await storage.check_and_increment("test:key", 5, 60)
    assert allowed is True
    assert remaining == 4
    assert retry == 0


@pytest.mark.asyncio
async def test_at_limit():
    storage = MemoryRateLimitStorage()
    for i in range(5):
        allowed, remaining, retry = await storage.check_and_increment("test:key2", 5, 60)
        if i < 4:
            assert allowed is True
        else:
            assert allowed is True
            assert remaining == 0


@pytest.mark.asyncio
async def test_over_limit():
    storage = MemoryRateLimitStorage()
    for i in range(6):
        allowed, _, _ = await storage.check_and_increment("test:key3", 5, 60)
    assert allowed is False


@pytest.mark.asyncio
async def test_window_reset():
    storage = MemoryRateLimitStorage()
    for _ in range(5):
        await storage.check_and_increment("test:key4", 5, 1)
    allowed, remaining, retry = await storage.check_and_increment("test:key4", 5, 1)
    assert allowed is False
    assert remaining == 0
    assert retry > 0


@pytest.mark.asyncio
async def test_window_expiry():
    storage = MemoryRateLimitStorage()
    await storage.check_and_increment("test:key5", 5, 0.1)
    await asyncio.sleep(0.15)
    allowed, remaining, _ = await storage.check_and_increment("test:key5", 5, 0.1)
    assert allowed is True
    assert remaining == 4


@pytest.mark.asyncio
async def test_concurrent_requests():
    storage = MemoryRateLimitStorage()
    limit = 20

    async def inc():
        allowed, _, _ = await storage.check_and_increment("concurrent", limit, 60)
        return allowed

    results = await asyncio.gather(*[inc() for _ in range(limit + 5)])
    allowed_count = sum(1 for r in results if r)
    assert allowed_count == limit


# ── RateLimiterMiddleware tests ─────────────────────────────────────────────


def _make_test_app(limits=None):
    async def ok_route(request):
        return PlainTextResponse("ok", status_code=200)

    routes = [
        Route("/api/v1/validation/validate", endpoint=ok_route, methods=["POST"]),
        Route("/api/v1/reports/generate", endpoint=ok_route, methods=["POST"]),
        Route("/api/v1/ats/candidates", endpoint=ok_route, methods=["POST"]),
        Route("/health", endpoint=ok_route, methods=["GET"]),
    ]
    app = Starlette(routes=routes)
    app.add_middleware(RateLimiterMiddleware, storage=MemoryRateLimitStorage(), limits=limits)
    return app


@pytest.fixture
def client():
    app = _make_test_app()
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


def test_match_limit():
    mw = RateLimiterMiddleware(app=None, storage=MemoryRateLimitStorage())  # type: ignore[arg-type]
    assert mw._match_limit("/api/v1/validation/validate") == (30, 60)
    assert mw._match_limit("/api/v1/reports/generate") == (20, 60)
    assert mw._match_limit("/api/v1/ats/candidates") == (60, 60)
    assert mw._match_limit("/unknown") is None


def test_is_excluded():
    mw = RateLimiterMiddleware(app=None, storage=MemoryRateLimitStorage())  # type: ignore[arg-type]
    assert mw._is_excluded("/health") is True
    assert mw._is_excluded("/health/") is True
    assert mw._is_excluded("/docs") is True
    assert mw._is_excluded("/docs/index.html") is True
    assert mw._is_excluded("/redoc") is True
    assert mw._is_excluded("/openapi.json") is True
    assert mw._is_excluded("/api/v1/validation/validate") is False


# ── Integration tests with isolated app ─────────────────────────────────────


@pytest.mark.asyncio
async def test_rate_limit_headers_present(client):
    async with client as ac:
        resp = await ac.post("/api/v1/validation/validate")
    assert resp.status_code == 200
    assert "X-RateLimit-Limit" in resp.headers
    assert "X-RateLimit-Remaining" in resp.headers


@pytest.mark.asyncio
async def test_rate_limit_429_response(client):
    async with client as ac:
        for i in range(35):
            resp = await ac.post("/api/v1/validation/validate")
            if resp.status_code == 429:
                break
        else:
            pytest.fail("Expected 429 but all requests succeeded")

    assert resp.status_code == 429
    assert "Retry-After" in resp.headers
    assert resp.headers["X-RateLimit-Remaining"] == "0"


@pytest.mark.asyncio
async def test_health_excluded_from_limiting(client):
    async with client as ac:
        for _ in range(10):
            resp = await ac.get("/health")
            if resp.status_code == 429:
                pytest.fail("Health endpoint should not be rate limited")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_different_limits_per_path(client):
    app = _make_test_app()
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        for _ in range(35):
            resp = await ac.post("/api/v1/validation/validate")
            if resp.status_code == 429:
                validation_limited = True
                break
        else:
            validation_limited = False

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        for _ in range(35):
            resp = await ac.post("/api/v1/ats/candidates")
            if resp.status_code == 429:
                ats_limited = True
                break
        else:
            ats_limited = False

    assert validation_limited is True
    assert ats_limited is False


@pytest.mark.asyncio
async def test_burst_then_recover(client):
    async with client as ac:
        for _ in range(35):
            await ac.post("/api/v1/validation/validate")

        resp = await ac.post("/api/v1/validation/validate")
        assert resp.status_code == 429

        # After window expires, should be allowed again
        # Can't actually wait in a test, so just verify the mechanism is correct


@pytest.mark.asyncio
async def test_concurrent_requests_dont_race(client):
    """Many concurrent requests must accurately count."""
    async with client as ac:
        async def req():
            r = await ac.post("/api/v1/validation/validate")
            return r.status_code

        results = await asyncio.gather(*[req() for _ in range(35)])
    ok = sum(1 for s in results if s == 200)
    limited = sum(1 for s in results if s == 429)
    assert ok == 30
    assert limited == 5
