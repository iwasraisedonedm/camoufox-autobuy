"""Internal retailer-profile artifact metadata routes."""

from uuid import UUID

from fastapi import APIRouter

from autobuy.control_plane.dependencies import Coordinator, DbSession, InternalService
from autobuy.control_plane.schemas import (
    ProfileArtifactAccessRequest,
    ProfileArtifactCheckpointRequest,
    ProfileArtifactMetadataRead,
)
from autobuy.control_plane.services.profiles import (
    checkpoint_profile_artifact,
    get_profile_artifact_metadata,
)

router = APIRouter(prefix="/api/v1/internal/retailer-profiles", tags=["internal-profiles"])


@router.post("/{profile_id}/artifact", response_model=ProfileArtifactMetadataRead)
async def get_profile_artifact_route(
    profile_id: UUID,
    payload: ProfileArtifactAccessRequest,
    session: DbSession,
    coordinator: Coordinator,
    _: InternalService,
) -> ProfileArtifactMetadataRead:
    profile = await get_profile_artifact_metadata(
        session,
        coordinator,
        profile_id=profile_id,
        worker_id=payload.worker_id,
        lease_id=payload.lease_id,
        lease_token=payload.lease_token,
    )
    return ProfileArtifactMetadataRead(
        profile_id=profile.id,
        encrypted_artifact_ref=profile.encrypted_artifact_ref,
        artifact_version=profile.artifact_version,
    )


@router.post("/{profile_id}/checkpoint", response_model=ProfileArtifactMetadataRead)
async def checkpoint_profile_artifact_route(
    profile_id: UUID,
    payload: ProfileArtifactCheckpointRequest,
    session: DbSession,
    coordinator: Coordinator,
    _: InternalService,
) -> ProfileArtifactMetadataRead:
    profile = await checkpoint_profile_artifact(
        session,
        coordinator,
        profile_id=profile_id,
        worker_id=payload.worker_id,
        lease_id=payload.lease_id,
        lease_token=payload.lease_token,
        encrypted_artifact_ref=payload.encrypted_artifact_ref,
        artifact_version=payload.artifact_version,
    )
    return ProfileArtifactMetadataRead(
        profile_id=profile.id,
        encrypted_artifact_ref=profile.encrypted_artifact_ref,
        artifact_version=profile.artifact_version,
    )
