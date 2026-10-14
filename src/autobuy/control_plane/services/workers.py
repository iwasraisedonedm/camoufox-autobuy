"""Worker registration, heartbeat, and lease lifecycle services."""

from __future__ import annotations

import hashlib
import hmac
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from autobuy.domain.enums import JobStatus, LeaseStatus, RetailerProfileStatus, WorkerStatus
from autobuy.domain.errors import DomainError, ErrorCode
from autobuy.orchestration.redis import RedisCoordinator, generate_lease_token
from autobuy.persistence.models import (
    JobEvent,
    MonitoringJob,
    PurchaseTarget,
    RetailerOffering,
    RetailerProfile,
    Worker,
    WorkerLease,
)
from autobuy.settings import Settings

SAFE_RECOVERY_JOB_STATUSES: frozenset[JobStatus] = frozenset(
    {
        JobStatus.READY,
        JobStatus.QUEUED,
        JobStatus.MONITORING,
        JobStatus.ITEM_FOUND,
        JobStatus.VALIDATING,
    }
)

REVIEW_RECOVERY_JOB_STATUSES: frozenset[JobStatus] = frozenset(
    {
        JobStatus.ADDING_TO_CART,
        JobStatus.CART_CONFIRMED,
        JobStatus.CHECKOUT_PREPARING,
        JobStatus.CHECKOUT_READY,
        JobStatus.AWAITING_CONFIRMATION,
        JobStatus.PURCHASE_AUTHORIZED,
    }
)


def _hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


async def register_worker(
    session: AsyncSession,
    coordinator: RedisCoordinator,
    *,
    instance_id: str,
    version: str,
) -> Worker:
    worker = await session.scalar(select(Worker).where(Worker.instance_id == instance_id))
    now = datetime.now(UTC)

    if worker is None:
        worker = Worker(
            instance_id=instance_id,
            version=version,
            status=WorkerStatus.REGISTERED,
            started_at=now,
            last_heartbeat_at=now,
        )
        session.add(worker)
    else:
        worker.version = version
        worker.status = WorkerStatus.REGISTERED
        worker.last_heartbeat_at = now

    await session.commit()
    await session.refresh(worker)
    await coordinator.set_worker_heartbeat(worker.id)
    return worker


async def heartbeat_worker(
    session: AsyncSession,
    coordinator: RedisCoordinator,
    *,
    worker_id: UUID,
) -> Worker:
    worker = await session.get(Worker, worker_id)
    if worker is None:
        raise DomainError(ErrorCode.WORKER_UNAVAILABLE, "Worker does not exist")

    worker.last_heartbeat_at = datetime.now(UTC)
    if worker.status in {WorkerStatus.STARTING, WorkerStatus.REGISTERED}:
        worker.status = WorkerStatus.IDLE

    await session.commit()
    await session.refresh(worker)
    await coordinator.set_worker_heartbeat(worker.id)
    return worker


async def acquire_lease(
    session: AsyncSession,
    coordinator: RedisCoordinator,
    settings: Settings,
    *,
    worker_id: UUID,
    retailer_profile_id: UUID,
) -> tuple[WorkerLease, str]:
    worker = await session.get(Worker, worker_id)
    if worker is None:
        raise DomainError(ErrorCode.WORKER_UNAVAILABLE, "Worker does not exist")
    if not await coordinator.has_worker_heartbeat(worker.id):
        raise DomainError(ErrorCode.WORKER_UNAVAILABLE, "Worker heartbeat is stale")

    profile = await session.get(RetailerProfile, retailer_profile_id)
    if profile is None:
        raise DomainError(
            ErrorCode.RETAILER_PROFILE_NOT_FOUND,
            "Retailer profile does not exist",
        )
    if profile.status not in {
        RetailerProfileStatus.AUTHENTICATED,
        RetailerProfileStatus.READY,
        RetailerProfileStatus.LOCKED,
    }:
        raise DomainError(
            ErrorCode.RETAILER_PROFILE_LOCKED,
            "Retailer profile is not eligible for a worker lease",
        )

    existing = await session.scalar(
        select(WorkerLease).where(
            WorkerLease.retailer_profile_id == retailer_profile_id,
            WorkerLease.status == LeaseStatus.ACTIVE,
        )
    )
    if existing is not None:
        raise DomainError(
            ErrorCode.RETAILER_PROFILE_LOCKED,
            "Retailer profile already has an active lease",
        )

    token = generate_lease_token()
    now = datetime.now(UTC)
    lease = WorkerLease(
        worker_id=worker.id,
        retailer_profile_id=profile.id,
        lease_token_hash=token.digest,
        acquired_at=now,
        expires_at=now + timedelta(seconds=settings.worker_lease_ttl_seconds),
        status=LeaseStatus.ACTIVE,
    )
    session.add(lease)
    await session.flush()

    locked = await coordinator.acquire_profile_lock(
        profile.id,
        lease.id,
        ttl_seconds=settings.worker_lease_ttl_seconds,
    )
    if not locked:
        await session.rollback()
        raise DomainError(
            ErrorCode.RETAILER_PROFILE_LOCKED,
            "Retailer profile runtime is already owned",
        )

    try:
        worker.status = WorkerStatus.LEASED
        profile.status = RetailerProfileStatus.LOCKED
        await session.commit()
        await session.refresh(lease)
    except Exception:
        await coordinator.release_profile_lock(profile.id, lease.id)
        raise

    return lease, token.raw


async def validate_active_lease(
    session: AsyncSession,
    coordinator: RedisCoordinator,
    *,
    lease_id: UUID,
    worker_id: UUID,
    retailer_profile_id: UUID,
    lease_token: str,
) -> WorkerLease:
    lease = await session.get(WorkerLease, lease_id)
    if lease is None or lease.status != LeaseStatus.ACTIVE:
        raise DomainError(ErrorCode.LEASE_INVALID, "Lease is not active")
    if lease.worker_id != worker_id or lease.retailer_profile_id != retailer_profile_id:
        raise DomainError(ErrorCode.LEASE_INVALID, "Lease does not match worker/profile")
    if lease.expires_at <= datetime.now(UTC):
        raise DomainError(ErrorCode.LEASE_EXPIRED, "Lease has expired")
    if not hmac.compare_digest(lease.lease_token_hash, _hash_token(lease_token)):
        raise DomainError(ErrorCode.LEASE_INVALID, "Lease token is invalid")
    if not await coordinator.owns_profile_lock(retailer_profile_id, lease_id):
        raise DomainError(ErrorCode.LEASE_EXPIRED, "Lease coordination lock is not active")
    return lease


async def renew_lease(
    session: AsyncSession,
    coordinator: RedisCoordinator,
    settings: Settings,
    *,
    lease_id: UUID,
    worker_id: UUID,
    lease_token: str,
) -> WorkerLease:
    lease = await session.scalar(
        select(WorkerLease).where(WorkerLease.id == lease_id).with_for_update()
    )
    if lease is None or lease.status != LeaseStatus.ACTIVE:
        raise DomainError(ErrorCode.LEASE_INVALID, "Lease is not active")
    if lease.worker_id != worker_id:
        raise DomainError(ErrorCode.LEASE_INVALID, "Lease does not belong to worker")
    if not hmac.compare_digest(lease.lease_token_hash, _hash_token(lease_token)):
        raise DomainError(ErrorCode.LEASE_INVALID, "Lease token is invalid")

    renewed = await coordinator.renew_profile_lock(
        lease.retailer_profile_id,
        lease.id,
        ttl_seconds=settings.worker_lease_ttl_seconds,
    )
    if not renewed:
        lease.status = LeaseStatus.EXPIRED
        await session.commit()
        raise DomainError(ErrorCode.LEASE_EXPIRED, "Lease coordination lock has expired")

    lease.expires_at = datetime.now(UTC) + timedelta(seconds=settings.worker_lease_ttl_seconds)
    await session.commit()
    await session.refresh(lease)
    return lease


async def release_lease(
    session: AsyncSession,
    coordinator: RedisCoordinator,
    *,
    lease_id: UUID,
    worker_id: UUID,
    lease_token: str,
) -> WorkerLease:
    lease = await session.scalar(
        select(WorkerLease).where(WorkerLease.id == lease_id).with_for_update()
    )
    if lease is None:
        raise DomainError(ErrorCode.LEASE_INVALID, "Lease does not exist")
    if lease.worker_id != worker_id:
        raise DomainError(ErrorCode.LEASE_INVALID, "Lease does not belong to worker")
    if not hmac.compare_digest(lease.lease_token_hash, _hash_token(lease_token)):
        raise DomainError(ErrorCode.LEASE_INVALID, "Lease token is invalid")
    if lease.status != LeaseStatus.ACTIVE:
        return lease

    lease.status = LeaseStatus.RELEASED
    lease.released_at = datetime.now(UTC)

    profile = await session.get(RetailerProfile, lease.retailer_profile_id)
    if profile is not None and profile.status == RetailerProfileStatus.LOCKED:
        profile.status = RetailerProfileStatus.READY

    worker = await session.get(Worker, worker_id)
    if worker is not None:
        active_count = await session.scalar(
            select(func.count(WorkerLease.id)).where(
                WorkerLease.worker_id == worker_id,
                WorkerLease.status == LeaseStatus.ACTIVE,
                WorkerLease.id != lease.id,
            )
        )
        if (active_count or 0) == 0:
            worker.status = WorkerStatus.IDLE

    await session.commit()
    await coordinator.release_profile_lock(lease.retailer_profile_id, lease.id)
    await session.refresh(lease)
    return lease


async def expire_stale_leases(
    session: AsyncSession,
    coordinator: RedisCoordinator,
) -> int:
    now = datetime.now(UTC)
    leases = list(
        (
            await session.scalars(
                select(WorkerLease)
                .where(
                    WorkerLease.status == LeaseStatus.ACTIVE,
                    WorkerLease.expires_at <= now,
                )
                .with_for_update(skip_locked=True)
            )
        ).all()
    )
    if not leases:
        return 0

    requeue: list[tuple[str, UUID]] = []

    for lease in leases:
        lease.status = LeaseStatus.EXPIRED
        lease.released_at = now

        profile = await session.get(RetailerProfile, lease.retailer_profile_id)
        if profile is not None and profile.status == RetailerProfileStatus.LOCKED:
            profile.status = RetailerProfileStatus.READY

        worker = await session.get(Worker, lease.worker_id)
        if worker is not None and not await coordinator.has_worker_heartbeat(worker.id):
            worker.status = WorkerStatus.LOST

        jobs = list(
            (
                await session.scalars(
                    select(MonitoringJob).where(
                        MonitoringJob.retailer_profile_id == lease.retailer_profile_id,
                        MonitoringJob.status.in_(
                            SAFE_RECOVERY_JOB_STATUSES
                            | REVIEW_RECOVERY_JOB_STATUSES
                            | {JobStatus.SUBMITTING, JobStatus.AMBIGUOUS}
                        ),
                    )
                )
            ).all()
        )

        for job in jobs:
            if job.status in SAFE_RECOVERY_JOB_STATUSES:
                target = await session.get(PurchaseTarget, job.purchase_target_id)
                offering = (
                    await session.get(RetailerOffering, target.retailer_offering_id)
                    if target is not None
                    else None
                )
                if offering is not None and offering.status == "active":
                    job.status = JobStatus.QUEUED
                    session.add(
                        JobEvent(
                            job_id=job.id,
                            event_type="JOB_RECOVERED_AFTER_LEASE_EXPIRY",
                            payload_json={"retailer_code": offering.retailer_code},
                        )
                    )
                    requeue.append((offering.retailer_code, job.id))
                else:
                    job.status = JobStatus.ACTION_REQUIRED
            elif job.status == JobStatus.SUBMITTING:
                job.status = JobStatus.AMBIGUOUS
                session.add(
                    JobEvent(
                        job_id=job.id,
                        event_type="PURCHASE_AMBIGUOUS_AFTER_WORKER_LOSS",
                        payload_json={},
                    )
                )
            elif job.status in REVIEW_RECOVERY_JOB_STATUSES:
                job.status = JobStatus.ACTION_REQUIRED
                session.add(
                    JobEvent(
                        job_id=job.id,
                        event_type="RECOVERY_REVIEW_REQUIRED",
                        payload_json={},
                    )
                )

        await coordinator.release_profile_lock(lease.retailer_profile_id, lease.id)

    await session.commit()

    for retailer_code, job_id in requeue:
        await coordinator.enqueue_job(retailer_code, job_id)

    return len(leases)
