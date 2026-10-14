"""Retailer-profile artifact metadata services."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from autobuy.control_plane.services.workers import validate_active_lease
from autobuy.domain.errors import DomainError, ErrorCode
from autobuy.orchestration.redis import RedisCoordinator
from autobuy.persistence.models import RetailerProfile


async def get_profile_artifact_metadata(
    session: AsyncSession,
    coordinator: RedisCoordinator,
    *,
    profile_id: UUID,
    worker_id: UUID,
    lease_id: UUID,
    lease_token: str,
) -> RetailerProfile:
    profile = await session.get(RetailerProfile, profile_id)
    if profile is None:
        raise DomainError(
            ErrorCode.RETAILER_PROFILE_NOT_FOUND,
            "Retailer profile does not exist",
        )

    await validate_active_lease(
        session,
        coordinator,
        lease_id=lease_id,
        worker_id=worker_id,
        retailer_profile_id=profile_id,
        lease_token=lease_token,
    )
    return profile


async def checkpoint_profile_artifact(
    session: AsyncSession,
    coordinator: RedisCoordinator,
    *,
    profile_id: UUID,
    worker_id: UUID,
    lease_id: UUID,
    lease_token: str,
    encrypted_artifact_ref: str,
    artifact_version: int,
) -> RetailerProfile:
    profile = await session.scalar(
        select(RetailerProfile).where(RetailerProfile.id == profile_id).with_for_update()
    )
    if profile is None:
        raise DomainError(
            ErrorCode.RETAILER_PROFILE_NOT_FOUND,
            "Retailer profile does not exist",
        )

    await validate_active_lease(
        session,
        coordinator,
        lease_id=lease_id,
        worker_id=worker_id,
        retailer_profile_id=profile_id,
        lease_token=lease_token,
    )

    expected_version = profile.artifact_version + 1
    if artifact_version != expected_version:
        raise DomainError(
            ErrorCode.RETAILER_PROFILE_LOCKED,
            f"Artifact version must advance from {profile.artifact_version} to {expected_version}",
        )

    profile.encrypted_artifact_ref = encrypted_artifact_ref
    profile.artifact_version = artifact_version
    await session.commit()
    await session.refresh(profile)
    return profile
