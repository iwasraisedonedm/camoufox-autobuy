"""Customer account routes."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from autobuy.control_plane.dependencies import DbSession
from autobuy.control_plane.schemas import CustomerCreate, CustomerRead
from autobuy.control_plane.services.customers import create_customer
from autobuy.persistence.models import CustomerAccount

router = APIRouter(prefix="/api/v1/customers", tags=["customers"])


@router.post("", response_model=CustomerRead, status_code=status.HTTP_201_CREATED)
async def create_customer_route(payload: CustomerCreate, session: DbSession) -> CustomerAccount:
    return await create_customer(session, payload.email)


@router.get("/{customer_id}", response_model=CustomerRead)
async def get_customer(customer_id: UUID, session: DbSession) -> CustomerAccount:
    customer = await session.get(CustomerAccount, customer_id)
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer
