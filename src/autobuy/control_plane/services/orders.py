"""Transactional confirmed-order accounting."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from autobuy.domain.enums import AttemptStatus, EntitlementStatus, JobStatus
from autobuy.domain.errors import DomainError, ErrorCode
from autobuy.persistence.models import (
    JobEvent,
    MonitoringJob,
    Order,
    PurchaseAttempt,
    ServiceEntitlement,
)


async def confirm_order(
    session: AsyncSession,
    *,
    attempt_id: UUID,
    retailer_order_reference: str,
    quantity_confirmed: int,
    unit_price,
    currency: str,
    confirmed_at,
) -> Order:
    existing = await session.scalar(select(Order).where(Order.purchase_attempt_id == attempt_id))
    if existing is not None:
        return existing

    attempt = await session.scalar(
        select(PurchaseAttempt).where(PurchaseAttempt.id == attempt_id).with_for_update()
    )
    if attempt is None:
        raise DomainError(
            ErrorCode.PURCHASE_CONFIRMATION_FAILED,
            "Purchase attempt does not exist",
        )
    if attempt.state not in {
        AttemptStatus.SUBMISSION_STARTED,
        AttemptStatus.AMBIGUOUS,
        AttemptStatus.RECONCILING,
    }:
        raise DomainError(
            ErrorCode.PURCHASE_CONFIRMATION_FAILED,
            "Purchase attempt is not confirmable",
        )

    job = await session.scalar(
        select(MonitoringJob).where(MonitoringJob.id == attempt.job_id).with_for_update()
    )
    if job is None:
        raise DomainError(ErrorCode.JOB_NOT_FOUND, "Monitoring job does not exist")

    entitlement = await session.scalar(
        select(ServiceEntitlement)
        .where(ServiceEntitlement.id == job.entitlement_id)
        .with_for_update()
    )
    if entitlement is None:
        raise DomainError(
            ErrorCode.ENTITLEMENT_REQUIRED,
            "Entitlement does not exist",
        )

    remaining = (
        entitlement.successful_unit_allowance_total - entitlement.successful_unit_allowance_used
    )
    if quantity_confirmed > remaining:
        raise DomainError(
            ErrorCode.ALLOWANCE_EXHAUSTED,
            "Confirmed quantity exceeds remaining allowance",
        )

    order = Order(
        customer_id=job.customer_id,
        retailer_profile_id=job.retailer_profile_id,
        job_id=job.id,
        purchase_attempt_id=attempt.id,
        retailer_order_reference=retailer_order_reference.strip(),
        quantity_confirmed=quantity_confirmed,
        unit_price=unit_price,
        currency=currency.upper(),
        confirmed_at=confirmed_at,
    )
    session.add(order)

    entitlement.successful_unit_allowance_used += quantity_confirmed
    if entitlement.successful_unit_allowance_used >= entitlement.successful_unit_allowance_total:
        entitlement.status = EntitlementStatus.EXHAUSTED

    attempt.state = AttemptStatus.CONFIRMED
    attempt.finished_at = confirmed_at
    job.status = JobStatus.ORDER_CONFIRMED

    session.add(
        JobEvent(
            job_id=job.id,
            attempt_id=attempt.id,
            event_type="ORDER_CONFIRMED",
            payload_json={
                "quantity_confirmed": quantity_confirmed,
                "currency": currency.upper(),
            },
        )
    )

    await session.commit()
    await session.refresh(order)
    return order
