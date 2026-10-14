"""Pure entitlement policy helpers."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class EntitlementSnapshot:
    starts_at: datetime
    expires_at: datetime
    concurrent_job_limit: int
    active_job_count: int
    allowance_total: int
    allowance_used: int

    @property
    def allowance_remaining(self) -> int:
        return max(0, self.allowance_total - self.allowance_used)


def can_start_job(entitlement: EntitlementSnapshot, now: datetime) -> bool:
    return (
        entitlement.starts_at <= now < entitlement.expires_at
        and entitlement.allowance_remaining > 0
        and entitlement.active_job_count < entitlement.concurrent_job_limit
    )


def consume_confirmed_units(
    entitlement: EntitlementSnapshot,
    confirmed_units: int,
) -> int:
    if confirmed_units < 0:
        raise ValueError("confirmed_units cannot be negative")
    if confirmed_units > entitlement.allowance_remaining:
        raise ValueError("confirmed units exceed remaining allowance")
    return entitlement.allowance_used + confirmed_units
