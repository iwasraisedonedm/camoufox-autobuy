"""Entitlement grant and validation application service."""

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from autobuy.domain.enums import EntitlementStatus
from autobuy.domain.errors import DomainError, ErrorCode
from autobuy.persistence.models import CustomerAccount, RetailerOffering, ServiceEntitlement


async def grant_entitlement(
    session: AsyncSession,
    *,
    customer_id,
    retailer_offering_id,
    starts_at: datetime,
    expires_at: datetime,
    concurrent_job_limit: int,
    successful_unit_allowance_total: int,
    external_grant_reference: str,
) -> ServiceEntitlement:
    existing = await session.scalar(
        select(ServiceEntitlement).where(
            ServiceEntitlement.external_grant_reference == external_grant_reference
        )
    )
    if existing is not None:
        return existing

    if expires_at <= starts_at:
        raise DomainError(
            ErrorCode.ENTITLEMENT_REQUIRED,
            "Entitlement expiration must be after its start time",
        )

    customer = await session.get(CustomerAccount, customer_id)
    if customer is None:
        raise DomainError(ErrorCode.CUSTOMER_NOT_LINKED, "Customer account does not exist")

    offering = await session.get(RetailerOffering, retailer_offering_id)
    if offering is None or offering.status != "active":
        raise DomainError(ErrorCode.RETAILER_UNAVAILABLE, "Retailer offering is unavailable")

    now = datetime.now(UTC)
    status = (
        EntitlementStatus.ACTIVE if starts_at <= now < expires_at else EntitlementStatus.PENDING
    )

    entitlement = ServiceEntitlement(
        customer_id=customer_id,
        retailer_offering_id=retailer_offering_id,
        starts_at=starts_at,
        expires_at=expires_at,
        concurrent_job_limit=concurrent_job_limit,
        successful_unit_allowance_total=successful_unit_allowance_total,
        successful_unit_allowance_used=0,
        status=status,
        external_grant_reference=external_grant_reference,
    )
    session.add(entitlement)
    await session.commit()
    await session.refresh(entitlement)
    return entitlement
