from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from pydantic import ValidationError

from autobuy.control_plane.schemas import EntitlementGrant


def test_entitlement_grant_rejects_zero_allowance() -> None:
    now = datetime.now(UTC)
    with pytest.raises(ValidationError):
        EntitlementGrant(
            customer_id=uuid4(),
            retailer_offering_id=uuid4(),
            starts_at=now,
            expires_at=now + timedelta(days=1),
            concurrent_job_limit=1,
            successful_unit_allowance_total=0,
            external_grant_reference="grant-1",
        )
