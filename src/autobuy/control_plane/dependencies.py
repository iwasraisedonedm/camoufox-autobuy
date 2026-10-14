"""FastAPI dependencies for persistence and internal service auth."""

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from autobuy.settings import get_settings


async def get_db_session(request: Request) -> AsyncIterator[AsyncSession]:
    async with request.app.state.database.session_factory() as session:
        yield session


DbSession = Annotated[AsyncSession, Depends(get_db_session)]


async def require_internal_service(
    authorization: Annotated[str | None, Header()] = None,
) -> None:
    settings = get_settings()
    expected = settings.internal_service_token
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Internal service authentication is not configured",
        )
    if authorization != f"Bearer {expected}":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid internal service credentials",
        )


InternalService = Annotated[None, Depends(require_internal_service)]
