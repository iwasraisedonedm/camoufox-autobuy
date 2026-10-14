"""Monitoring-job creation and preflight application service."""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from autobuy.domain.enums import EntitlementStatus, JobStatus, RetailerProfileStatus, WorkflowMode
from autobuy.domain.errors import DomainError, ErrorCode
from autobuy.persistence.models import (
    JobEvent,
    MonitoringJob,
    PurchaseTarget,
    RetailerProfile,
    ServiceEntitlement,
)

ACTIVE_JOB_STATUSES: frozenset[JobStatus] = frozenset(
    {
        JobStatus.CREATED,
        JobStatus.PREFLIGHT,
        JobStatus.READY,
        JobStatus.QUEUED,
        JobStatus.MONITORING,
        JobStatus.ITEM_FOUND,
        JobStatus.VALIDATING,
        JobStatus.ADDING_TO_CART,
        JobStatus.CART_CONFIRMED,
        JobStatus.CHECKOUT_PREPARING,
        JobStatus.CHECKOUT_READY,
        JobStatus.AWAITING_CONFIRMATION,
        JobStatus.PURCHASE_AUTHORIZED,
        JobStatus.SUBMITTING,
        JobStatus.ACTION_REQUIRED,
        JobStatus.PAUSED,
        JobStatus.AMBIGUOUS,
    }
)


async def create_monitoring_job(
    session: AsyncSession,
    *,
    customer_id: UUID,
    entitlement_id: UUID,
    retailer_profile_id: UUID,
    purchase_target_id: UUID,
    workflow_mode: WorkflowMode,
    max_unit_price: Decimal,
    currency: str,
    quantity_requested: int,
    success_limit: int,
    expires_at: datetime,
) -> MonitoringJob:
    now = datetime.now(UTC)

    entitlement = await session.scalar(
        select(ServiceEntitlement)
        .where(ServiceEntitlement.id == entitlement_id)
        .with_for_update()
    )
    if entitlement is None or entitlement.customer_id != customer_id:
        raise DomainError(ErrorCode.ENTITLEMENT_REQUIRED, "Entitlement is unavailable")

    if entitlement.status == EntitlementStatus.REVOKED:
        raise DomainError(ErrorCode.ENTITLEMENT_REVOKED, "Entitlement has been revoked")
    if entitlement.status != EntitlementStatus.ACTIVE:
        raise DomainError(ErrorCode.ENTITLEMENT_REQUIRED, "Entitlement is not active")
    if not (entitlement.starts_at <= now < entitlement.expires_at):
        raise DomainError(ErrorCode.ENTITLEMENT_EXPIRED, "Entitlement has expired")

    remaining = (
        entitlement.successful_unit_allowance_total
        - entitlement.successful_unit_allowance_used
    )
    if remaining <= 0:
        raise DomainError(ErrorCode.ALLOWANCE_EXHAUSTED, "Purchase allowance is exhausted")
    if quantity_requested > remaining:
        raise DomainError(
            ErrorCode.ALLOWANCE_EXHAUSTED,
            "Requested quantity exceeds remaining purchase allowance",
        )

    if expires_at <= now or expires_at > entitlement.expires_at:
        raise DomainError(
            ErrorCode.ENTITLEMENT_EXPIRED,
            "Job expiration must be in the future and within the entitlement window",
        )

    target = await session.get(PurchaseTarget, purchase_target_id)
    if target is None or target.customer_id != customer_id:
        raise DomainError(ErrorCode.INVALID_TARGET, "Purchase target is unavailable")

    profile = await session.get(RetailerProfile, retailer_profile_id)
    if profile is None or profile.customer_id != customer_id:
        raise DomainError(
            ErrorCode.RETAILER_PROFILE_NOT_FOUND,
            "Retailer profile is unavailable",
        )
    if profile.status != RetailerProfileStatus.READY:
        raise DomainError(
            ErrorCode.RETAILER_REAUTH_REQUIRED,
            "Retailer profile is not ready for purchasing",
        )

    if target.retailer_offering_id != entitlement.retailer_offering_id:
        raise DomainError(ErrorCode.INVALID_TARGET, "Target does not match entitlement retailer")
    if profile.retailer_offering_id != entitlement.retailer_offering_id:
        raise DomainError(
            ErrorCode.RETAILER_PROFILE_NOT_FOUND,
            "Retailer profile does not match entitlement retailer",
        )

    active_count = await session.scalar(
        select(func.count(MonitoringJob.id)).where(
            MonitoringJob.entitlement_id == entitlement.id,
            MonitoringJob.status.in_(ACTIVE_JOB_STATUSES),
        )
    )
    if (active_count or 0) >= entitlement.concurrent_job_limit:
        raise DomainError(
            ErrorCode.CONCURRENT_JOB_LIMIT_REACHED,
            "Concurrent job limit has been reached",
        )

    job = MonitoringJob(
        customer_id=customer_id,
        entitlement_id=entitlement_id,
        retailer_profile_id=retailer_profile_id,
        purchase_target_id=purchase_target_id,
        workflow_mode=workflow_mode,
        max_unit_price=max_unit_price,
        currency=currency.upper(),
        quantity_requested=quantity_requested,
        success_limit=success_limit,
        expires_at=expires_at,
        status=JobStatus.READY,
    )
    session.add(job)
    await session.flush()
    session.add(
        JobEvent(
            job_id=job.id,
            event_type="JOB_CREATED",
            payload_json={"status": JobStatus.READY.value},
        )
    )
    await session.commit()
    await session.refresh(job)
    return job
