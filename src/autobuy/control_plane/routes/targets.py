"""Purchase-target routes."""

from fastapi import APIRouter, status

from autobuy.control_plane.dependencies import DbSession
from autobuy.control_plane.schemas import PurchaseTargetCreate, PurchaseTargetRead
from autobuy.control_plane.services.targets import create_purchase_target
from autobuy.persistence.models import PurchaseTarget

router = APIRouter(prefix="/api/v1/targets", tags=["targets"])


@router.post("", response_model=PurchaseTargetRead, status_code=status.HTTP_201_CREATED)
async def create_target_route(
    payload: PurchaseTargetCreate,
    session: DbSession,
) -> PurchaseTarget:
    return await create_purchase_target(
        session,
        customer_id=payload.customer_id,
        retailer_offering_id=payload.retailer_offering_id,
        retailer_product_id=payload.retailer_product_id,
        retailer_variant_id=payload.retailer_variant_id,
        url=payload.url,
        display_name=payload.display_name,
    )
