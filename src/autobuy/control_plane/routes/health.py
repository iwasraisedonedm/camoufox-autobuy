"""Liveness and readiness routes."""

from fastapi import APIRouter, Request
from sqlalchemy import text

router = APIRouter(prefix="/api/v1/health", tags=["health"])


@router.get("/live")
async def live() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready")
async def ready(request: Request) -> dict[str, str]:
    database = request.app.state.database
    coordinator = request.app.state.coordinator

    async with database.session_factory() as session:
        await session.execute(text("SELECT 1"))

    if not await coordinator.ping():
        raise RuntimeError("Redis readiness check failed")

    return {"status": "ready"}
