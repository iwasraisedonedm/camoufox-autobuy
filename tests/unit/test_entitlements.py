from datetime import UTC, datetime, timedelta

import pytest

from autobuy.domain.entitlements import (
    EntitlementSnapshot,
    can_start_job,
    consume_confirmed_units,
)


def _snapshot(**overrides: object) -> EntitlementSnapshot:
    now = datetime.now(UTC)
    values: dict[str, object] = {
        "starts_at": now - timedelta(hours=1),
        "expires_at": now + timedelta(hours=1),
        "concurrent_job_limit": 2,
        "active_job_count": 0,
        "allowance_total": 3,
        "allowance_used": 0,
    }
    values.update(overrides)
    return EntitlementSnapshot(**values)  # type: ignore[arg-type]


def test_can_start_active_entitlement() -> None:
    assert can_start_job(_snapshot(), datetime.now(UTC))


def test_concurrency_limit_blocks_new_job() -> None:
    assert not can_start_job(_snapshot(active_job_count=2), datetime.now(UTC))


def test_confirmed_units_consume_allowance() -> None:
    assert consume_confirmed_units(_snapshot(allowance_used=1), 2) == 3


def test_overconsumption_is_rejected() -> None:
    with pytest.raises(ValueError):
        consume_confirmed_units(_snapshot(allowance_used=2), 2)
