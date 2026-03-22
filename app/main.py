from __future__ import annotations

import uuid
from contextlib import asynccontextmanager

from cachetools import TTLCache
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.routes import airports, bookings, flights, health, offers
from app.config import get_settings
from app.core.errors import AppError, app_error_handler, error_body
from app.legacy.circuit import CircuitBreaker
from app.legacy.client import LegacyClient
from app.services.airports import AirportIndex


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    breaker = CircuitBreaker(settings.circuit_failure_threshold, settings.circuit_open_seconds)
    client = LegacyClient(settings, breaker)
    app.state.settings = settings
    app.state.legacy_client = client
    app.state.airport_index = AirportIndex(settings)
    app.state.booking_cache = TTLCache(maxsize=512, ttl=settings.booking_cache_ttl_seconds)
    yield
    await client.aclose()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Flight Booking BFF",
        description="Wrapper over the legacy mock travel API — normalized contracts for frontend clients.",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next):
        rid = request.headers.get("X-Request-Id") or str(uuid.uuid4())
        request.state.request_id = rid
        response = await call_next(request)
        response.headers["X-Request-Id"] = rid
        return response

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        rid = getattr(request.state, "request_id", None) or str(uuid.uuid4())
        return JSONResponse(
            status_code=422,
            content=error_body(
                "VALIDATION_ERROR",
                "Request validation failed",
                {"fields": exc.errors()},
                rid,
            ),
        )

    app.add_exception_handler(AppError, app_error_handler)

    app.include_router(health.router)
    app.include_router(flights.router, prefix="/v1")
    app.include_router(offers.router, prefix="/v1")
    app.include_router(bookings.router, prefix="/v1")
    app.include_router(airports.router, prefix="/v1")

    return app


app = create_app()
