"""Transport-agnostic retailer adapter contract."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Protocol
from uuid import UUID

from autobuy.domain.enums import RetailerHealth


@dataclass(frozen=True, slots=True)
class LoginStatus:
    authenticated: bool
    reauth_required: bool
    account_reference: str | None
    observed_at: datetime


@dataclass(frozen=True, slots=True)
class TargetSnapshot:
    job_id: UUID
    retailer_product_id: str
    retailer_variant_id: str | None
    product_url: str
    quantity: int
    max_unit_price: Decimal
    currency: str


@dataclass(frozen=True, slots=True)
class ProductSnapshot:
    retailer_code: str
    retailer_product_id: str
    retailer_variant_id: str | None
    title: str | None
    available: bool
    unit_price: Decimal | None
    currency: str
    observed_at: datetime


@dataclass(frozen=True, slots=True)
class CartResult:
    accepted: bool
    quantity: int
    cart_reference: str | None
    failure_code: str | None


@dataclass(frozen=True, slots=True)
class CheckoutResult:
    ready: bool
    total: Decimal | None
    currency: str
    action_required: bool
    failure_code: str | None


@dataclass(frozen=True, slots=True)
class OrderResult:
    confirmed: bool
    retailer_order_reference: str | None
    quantity_confirmed: int
    unit_price: Decimal | None
    currency: str
    failure_code: str | None
    ambiguous: bool


@dataclass(frozen=True, slots=True)
class RetailerHealthObservation:
    state: RetailerHealth
    observed_at: datetime
    detail: str | None = None


class RetailerAdapter(Protocol):
    retailer_code: str
    version: str

    async def login_status(self) -> LoginStatus: ...

    async def product_snapshot(self, target: TargetSnapshot) -> ProductSnapshot: ...

    async def add_to_cart(self, product: ProductSnapshot, quantity: int) -> CartResult: ...

    async def prepare_checkout(self) -> CheckoutResult: ...

    async def submit_order(self) -> OrderResult: ...

    async def reconcile_order(self, attempt_reference: str) -> OrderResult: ...

    async def health_check(self) -> RetailerHealthObservation: ...

    async def close(self) -> None: ...


class RetailerAdapterFactory(Protocol):
    retailer_code: str
    version: str

    async def create(self, retailer_profile_id: UUID) -> RetailerAdapter: ...
