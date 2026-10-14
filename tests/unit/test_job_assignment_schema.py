from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from autobuy.control_plane.schemas import JobAssignmentRead
from autobuy.domain.enums import WorkflowMode


def test_job_assignment_is_transport_agnostic() -> None:
    assignment = JobAssignmentRead(
        job_id=uuid4(),
        retailer_code="bestbuy",
        retailer_profile_id=uuid4(),
        purchase_target_id=uuid4(),
        retailer_product_id="sku-1",
        retailer_variant_id=None,
        product_url="https://example.invalid/product",
        workflow_mode=WorkflowMode.AUTO_PURCHASE,
        max_unit_price=Decimal("100.00"),
        currency="USD",
        quantity_requested=1,
        expires_at=datetime.now(UTC) + timedelta(hours=1),
    )

    assert assignment.retailer_code == "bestbuy"
