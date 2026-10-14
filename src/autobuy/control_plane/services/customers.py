"""Customer account application service."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from autobuy.persistence.models import CustomerAccount


def normalize_email(value: str) -> str:
    return value.strip().casefold()


async def create_customer(session: AsyncSession, email: str) -> CustomerAccount:
    normalized = normalize_email(email)
    existing = await session.scalar(
        select(CustomerAccount).where(CustomerAccount.email == normalized)
    )
    if existing is not None:
        return existing

    customer = CustomerAccount(email=normalized)
    session.add(customer)
    await session.commit()
    await session.refresh(customer)
    return customer
