from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import Settings
from app.core.logging import CorrelationMiddleware, setup_logging
from app.core.rate_limiter import MemoryRateLimitStorage, RateLimitStorage, RateLimiterMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    yield


_rate_limit_storage: RateLimitStorage = MemoryRateLimitStorage()


def get_rate_limit_storage() -> RateLimitStorage:
    return _rate_limit_storage


def create_application() -> FastAPI:
    settings = Settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    app.add_middleware(CorrelationMiddleware)

    app.add_middleware(
        RateLimiterMiddleware,
        storage=_rate_limit_storage,
    )

    cors_origins = settings.cors_origins or ["*"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=bool(cors_origins and "*" not in cors_origins),
        allow_methods=["*"],
        allow_headers=["*"],
    )

    from app.api.v1.validation import router as validation_router
    from app.api.v1.reports import router as reports_router
    from app.api.v1.ats import router as ats_router

    app.include_router(validation_router)
    app.include_router(reports_router)
    app.include_router(ats_router)

    @app.get("/health")
    async def health():
        checks = {}
        try:
            import httpx
            async with httpx.AsyncClient(timeout=5) as client:
                await client.get("https://google.com")
            checks["external_network"] = "ok"
        except Exception:
            checks["external_network"] = "degraded"

        checks["uptime"] = "ok"

        overall = "healthy" if all(v == "ok" for v in checks.values()) else "degraded"
        return {"status": overall, "checks": checks}

    return app


app = create_application()
