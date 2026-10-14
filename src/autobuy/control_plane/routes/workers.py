"""Internal worker registration, heartbeat, and lease routes."""

from uuid import UUID

from fastapi import APIRouter

from autobuy.control_plane.dependencies import Coordinator, DbSession, InternalService
from autobuy.control_plane.schemas import (
    LeaseAcquireRequest,
    LeaseAcquireResponse,
    LeaseMutationRequest,
    LeaseRead,
    LeaseReapResponse,
    WorkerRead,
    WorkerRegisterRequest,
)
from autobuy.control_plane.services.workers import (
    acquire_lease,
    expire_stale_leases,
    heartbeat_worker,
    register_worker,
    release_lease,
    renew_lease,
)
from autobuy.settings import get_settings

router = APIRouter(prefix="/api/v1/internal", tags=["internal-workers"])


@router.post("/workers/register", response_model=WorkerRead)
async def register_worker_route(
    payload: WorkerRegisterRequest,
    session: DbSession,
    coordinator: Coordinator,
    _: InternalService,
):
    return await register_worker(
        session,
        coordinator,
        instance_id=payload.instance_id,
        version=payload.version,
    )


@router.post("/workers/{worker_id}/heartbeat", response_model=WorkerRead)
async def heartbeat_worker_route(
    worker_id: UUID,
    session: DbSession,
    coordinator: Coordinator,
    _: InternalService,
):
    return await heartbeat_worker(session, coordinator, worker_id=worker_id)


@router.post("/leases/acquire", response_model=LeaseAcquireResponse)
async def acquire_lease_route(
    payload: LeaseAcquireRequest,
    session: DbSession,
    coordinator: Coordinator,
    _: InternalService,
) -> LeaseAcquireResponse:
    lease, raw_token = await acquire_lease(
        session,
        coordinator,
        get_settings(),
        worker_id=payload.worker_id,
        retailer_profile_id=payload.retailer_profile_id,
    )
    return LeaseAcquireResponse.model_validate(lease).model_copy(update={"lease_token": raw_token})


@router.post("/leases/{lease_id}/renew", response_model=LeaseRead)
async def renew_lease_route(
    lease_id: UUID,
    payload: LeaseMutationRequest,
    session: DbSession,
    coordinator: Coordinator,
    _: InternalService,
):
    return await renew_lease(
        session,
        coordinator,
        get_settings(),
        lease_id=lease_id,
        worker_id=payload.worker_id,
        lease_token=payload.lease_token,
    )


@router.post("/leases/{lease_id}/release", response_model=LeaseRead)
async def release_lease_route(
    lease_id: UUID,
    payload: LeaseMutationRequest,
    session: DbSession,
    coordinator: Coordinator,
    _: InternalService,
):
    return await release_lease(
        session,
        coordinator,
        lease_id=lease_id,
        worker_id=payload.worker_id,
        lease_token=payload.lease_token,
    )


@router.post("/leases/reap-expired", response_model=LeaseReapResponse)
async def reap_expired_leases_route(
    session: DbSession,
    coordinator: Coordinator,
    _: InternalService,
) -> LeaseReapResponse:
    expired = await expire_stale_leases(session, coordinator)
    return LeaseReapResponse(expired_leases=expired)
