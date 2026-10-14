from datetime import UTC, datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from autobuy.control_plane.schemas import OrderConfirmRequest


def test_order_confirmation_accepts_positive_quantity() -> None:
    payload = OrderConfirmRequest(
        retailer_order_reference="BBY-123",
        quantity_confirmed=2,
        unit_price=Decimal("499.99"),
        currency="USD",
        confirmed_at=datetime.now(UTC),
    )
    assert payload.quantity_confirmed == 2


def test_order_confirmation_rejects_zero_quantity() -> None:
    with pytest.raises(ValidationError):
        OrderConfirmRequest(
            retailer_order_reference="BBY-123",
            quantity_confirmed=0,
            unit_price=Decimal("499.99"),
            currency="USD",
            confirmed_at=datetime.now(UTC),
        )
