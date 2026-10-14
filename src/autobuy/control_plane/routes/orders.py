"""Internal confirmed-order routes."""

from uuid import UUID

from fastapi import APIRouter

from autobuy.control_plane.dependencies import DbSession, InternalService
from autobuy.control_plane.schemas import OrderConfirmRequest, OrderRead
from autobuy.control_plane.services.orders import confirm_order
from autobuy.persistence.models import Order

router = APIRouter(prefix="/api/v1/internal/attempts", tags=["internal-orders"])


@router.post("/{attempt_id}/confirm-order", response_model=OrderRead)
async def confirm_order_route(
    attempt_id: UUID,
    payload: OrderConfirmRequest,
    session: DbSession,
    _: InternalService,
) -> Order:
    return await confirm_order(
        session,
        attempt_id=attempt_id,
        retailer_order_reference=payload.retailer_order_reference,
        quantity_confirmed=payload.quantity_confirmed,
        unit_price=payload.unit_price,
        currency=payload.currency,
        confirmed_at=payload.confirmed_at,
    )
