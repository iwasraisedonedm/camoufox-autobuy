"""Private entitlement-management routes."""

from fastapi import APIRouter, status

from autobuy.control_plane.dependencies import DbSession, InternalService
from autobuy.control_plane.schemas import EntitlementGrant, EntitlementRead
from autobuy.control_plane.services.entitlements import grant_entitlement
from autobuy.persistence.models import ServiceEntitlement

router = APIRouter(prefix="/api/v1/internal/entitlements", tags=["internal-entitlements"])


@router.post("/grant", response_model=EntitlementRead, status_code=status.HTTP_201_CREATED)
async def grant_entitlement_route(
    payload: EntitlementGrant,
    session: DbSession,
    _: InternalService,
) -> ServiceEntitlement:
    return await grant_entitlement(
        session,
        customer_id=payload.customer_id,
        retailer_offering_id=payload.retailer_offering_id,
        starts_at=payload.starts_at,
        expires_at=payload.expires_at,
        concurrent_job_limit=payload.concurrent_job_limit,
        successful_unit_allowance_total=payload.successful_unit_allowance_total,
        external_grant_reference=payload.external_grant_reference,
    )
