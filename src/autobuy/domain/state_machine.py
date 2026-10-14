"""Explicit monitoring-job state transition validation."""

from autobuy.domain.enums import JobStatus
from autobuy.domain.errors import DomainError, ErrorCode

_ALLOWED: dict[JobStatus, frozenset[JobStatus]] = {
    JobStatus.CREATED: frozenset({JobStatus.PREFLIGHT, JobStatus.STOPPED}),
    JobStatus.PREFLIGHT: frozenset(
        {JobStatus.READY, JobStatus.ACTION_REQUIRED, JobStatus.FAILED, JobStatus.EXPIRED}
    ),
    JobStatus.READY: frozenset({JobStatus.QUEUED, JobStatus.PAUSED, JobStatus.STOPPED}),
    JobStatus.QUEUED: frozenset(
        {JobStatus.MONITORING, JobStatus.PAUSED, JobStatus.STOPPED, JobStatus.FAILED}
    ),
    JobStatus.MONITORING: frozenset(
        {
            JobStatus.ITEM_FOUND,
            JobStatus.PAUSED,
            JobStatus.ACTION_REQUIRED,
            JobStatus.EXPIRED,
            JobStatus.STOPPED,
            JobStatus.FAILED,
        }
    ),
    JobStatus.ITEM_FOUND: frozenset(
        {JobStatus.VALIDATING, JobStatus.MONITORING, JobStatus.FAILED}
    ),
    JobStatus.VALIDATING: frozenset(
        {JobStatus.ADDING_TO_CART, JobStatus.MONITORING, JobStatus.FAILED}
    ),
    JobStatus.ADDING_TO_CART: frozenset(
        {
            JobStatus.CART_CONFIRMED,
            JobStatus.MONITORING,
            JobStatus.ACTION_REQUIRED,
            JobStatus.FAILED,
        }
    ),
    JobStatus.CART_CONFIRMED: frozenset(
        {JobStatus.CHECKOUT_PREPARING, JobStatus.FAILED}
    ),
    JobStatus.CHECKOUT_PREPARING: frozenset(
        {JobStatus.CHECKOUT_READY, JobStatus.ACTION_REQUIRED, JobStatus.FAILED}
    ),
    JobStatus.CHECKOUT_READY: frozenset(
        {
            JobStatus.AWAITING_CONFIRMATION,
            JobStatus.PURCHASE_AUTHORIZED,
            JobStatus.ACTION_REQUIRED,
            JobStatus.FAILED,
        }
    ),
    JobStatus.AWAITING_CONFIRMATION: frozenset(
        {JobStatus.PURCHASE_AUTHORIZED, JobStatus.STOPPED, JobStatus.EXPIRED}
    ),
    JobStatus.PURCHASE_AUTHORIZED: frozenset({JobStatus.SUBMITTING, JobStatus.FAILED}),
    JobStatus.SUBMITTING: frozenset(
        {JobStatus.ORDER_CONFIRMED, JobStatus.AMBIGUOUS, JobStatus.FAILED}
    ),
    JobStatus.ORDER_CONFIRMED: frozenset({JobStatus.COMPLETED}),
    JobStatus.AMBIGUOUS: frozenset({JobStatus.ORDER_CONFIRMED, JobStatus.FAILED}),
    JobStatus.ACTION_REQUIRED: frozenset(
        {JobStatus.READY, JobStatus.MONITORING, JobStatus.STOPPED, JobStatus.EXPIRED}
    ),
    JobStatus.PAUSED: frozenset({JobStatus.READY, JobStatus.STOPPED, JobStatus.EXPIRED}),
    JobStatus.COMPLETED: frozenset(),
    JobStatus.FAILED: frozenset(),
    JobStatus.EXPIRED: frozenset(),
    JobStatus.STOPPED: frozenset(),
}


def validate_transition(current: JobStatus, target: JobStatus) -> None:
    if target not in _ALLOWED[current]:
        raise DomainError(
            ErrorCode.JOB_NOT_ACTIVE,
            f"Illegal job transition: {current.value} -> {target.value}",
        )
