"""Purchase-target application service."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from autobuy.domain.errors import DomainError, ErrorCode
from autobuy.persistence.models import CustomerAccount, PurchaseTarget, RetailerOffering


async def create_purchase_target(
    session: AsyncSession,
    *,
    customer_id: UUID,
    retailer_offering_id: UUID,
    retailer_product_id: str,
    retailer_variant_id: str | None,
    url: str,
    display_name: str | None,
) -> PurchaseTarget:
    customer = await session.get(CustomerAccount, customer_id)
    if customer is None:
        raise DomainError(ErrorCode.CUSTOMER_NOT_LINKED, "Customer account does not exist")

    offering = await session.get(RetailerOffering, retailer_offering_id)
    if offering is None or offering.status != "active":
        raise DomainError(ErrorCode.RETAILER_UNAVAILABLE, "Retailer offering is unavailable")

    target = PurchaseTarget(
        customer_id=customer_id,
        retailer_offering_id=retailer_offering_id,
        retailer_product_id=retailer_product_id.strip(),
        retailer_variant_id=retailer_variant_id.strip() if retailer_variant_id else None,
        url=url.strip(),
        display_name=display_name.strip() if display_name else None,
    )
    session.add(target)
    await session.commit()
    await session.refresh(target)
    return target
