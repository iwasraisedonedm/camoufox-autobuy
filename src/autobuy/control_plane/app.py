"""FastAPI application factory."""

from contextlib import asynccontextmanager
from typing import AsyncIterator
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from autobuy.domain.errors import DomainError
from autobuy.observability.logging import configure_logging
from autobuy.persistence.database import Database
from autobuy.settings import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)
    database = Database(settings)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        yield
        await database.close()

    app = FastAPI(
        title="AutoBuy Control Plane",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.state.database = database

    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next):  # type: ignore[no-untyped-def]
        request_id = request.headers.get("X-Request-ID") or str(uuid4())
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

    @app.exception_handler(DomainError)
    async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
        request_id = request.headers.get("X-Request-ID") or str(uuid4())
        return JSONResponse(
            status_code=409,
            content={
                "error": {
                    "code": exc.code.value,
                    "message": exc.message,
                    "reference_id": str(uuid4()),
                    "request_id": request_id,
                }
            },
        )

    from autobuy.control_plane.routes.health import router as health_router

    app.include_router(health_router)
    return app
