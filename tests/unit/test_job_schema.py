from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from autobuy.control_plane.schemas import MonitoringJobCreate


def _payload() -> dict[str, object]:
    return {
        "customer_id": uuid4(),
        "entitlement_id": uuid4(),
        "retailer_profile_id": uuid4(),
        "purchase_target_id": uuid4(),
        "workflow_mode": "auto_purchase",
        "max_unit_price": Decimal("999.99"),
        "currency": "USD",
        "quantity_requested": 1,
        "success_limit": 1,
        "expires_at": datetime.now(UTC) + timedelta(hours=1),
    }


def test_job_schema_accepts_auto_purchase() -> None:
    model = MonitoringJobCreate.model_validate(_payload())
    assert model.workflow_mode == "auto_purchase"


def test_job_schema_rejects_zero_quantity() -> None:
    payload = _payload()
    payload["quantity_requested"] = 0
    with pytest.raises(ValidationError):
        MonitoringJobCreate.model_validate(payload)
