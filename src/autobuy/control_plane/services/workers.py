"""Worker registration, heartbeat, and lease lifecycle services."""

from __future__ import annotations

import hashlib
import hmac
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from autobuy.domain.enums import LeaseStatus, RetailerProfileStatus, WorkerStatus
from autobuy.domain.errors import DomainError, ErrorCode
from autobuy.orchestration.redis import RedisCoordinator, generate_lease_token
from autobuy.persistence.models import RetailerProfile, Worker, WorkerLease
from autobuy.settings import Settings


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

    lease.expires_at = datetime.now(UTC) + timedelta(
        seconds=settings.worker_lease_ttl_seconds
    )
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
