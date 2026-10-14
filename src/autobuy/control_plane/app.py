"""FastAPI application factory."""

from collections.abc import AsyncGenerator, Awaitable, Callable
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response

from autobuy.control_plane.routes.customers import router as customers_router
from autobuy.control_plane.routes.entitlements import router as entitlements_router
from autobuy.control_plane.routes.health import router as health_router
from autobuy.control_plane.routes.jobs import router as jobs_router
from autobuy.control_plane.routes.orders import router as orders_router
from autobuy.control_plane.routes.targets import router as targets_router
from autobuy.domain.errors import DomainError
from autobuy.observability.logging import configure_logging
from autobuy.orchestration.redis import RedisCoordinator
from autobuy.persistence.database import Database
from autobuy.settings import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)
    database = Database(settings)
    coordinator = RedisCoordinator(settings)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
        yield
        await coordinator.close()
        await database.close()

    app = FastAPI(
        title="AutoBuy Control Plane",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.state.database = database
    app.state.coordinator = coordinator

    @app.middleware("http")
    async def request_id_middleware(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

    @app.exception_handler(DomainError)
    async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
        request_id = getattr(request.state, "request_id", str(uuid4()))
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

    app.include_router(health_router)
    app.include_router(customers_router)
    app.include_router(entitlements_router)
    app.include_router(targets_router)
    app.include_router(jobs_router)
    app.include_router(orders_router)
    return app
