"""Authenticated worker client for control-plane operations."""

from __future__ import annotations

from uuid import UUID

import httpx

from autobuy.control_plane.schemas import (
    JobAssignmentRead,
    LeaseAcquireResponse,
    LeaseMutationRequest,
    WorkerRead,
    WorkerRegisterRequest,
)
from autobuy.settings import Settings


class WorkerControlPlaneClient:
    def __init__(self, settings: Settings) -> None:
        if not settings.internal_service_token:
            raise RuntimeError("AUTOBUY_INTERNAL_SERVICE_TOKEN is required for workers")
        self._client = httpx.AsyncClient(
            base_url=settings.control_plane_base_url.rstrip("/"),
            headers={"Authorization": f"Bearer {settings.internal_service_token}"},
            timeout=httpx.Timeout(10.0),
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def register(self, instance_id: str, version: str) -> WorkerRead:
        response = await self._client.post(
            "/api/v1/internal/workers/register",
            json=WorkerRegisterRequest(instance_id=instance_id, version=version).model_dump(
                mode="json"
            ),
        )
        response.raise_for_status()
        return WorkerRead.model_validate(response.json())

    async def heartbeat(self, worker_id: UUID) -> WorkerRead:
        response = await self._client.post(
            f"/api/v1/internal/workers/{worker_id}/heartbeat"
        )
        response.raise_for_status()
        return WorkerRead.model_validate(response.json())

    async def assignment(self, job_id: UUID) -> JobAssignmentRead:
        response = await self._client.get(f"/api/v1/internal/jobs/{job_id}/assignment")
        response.raise_for_status()
        return JobAssignmentRead.model_validate(response.json())

    async def acquire_lease(
        self,
        worker_id: UUID,
        retailer_profile_id: UUID,
    ) -> LeaseAcquireResponse:
        response = await self._client.post(
            "/api/v1/internal/leases/acquire",
            json={
                "worker_id": str(worker_id),
                "retailer_profile_id": str(retailer_profile_id),
            },
        )
        response.raise_for_status()
        return LeaseAcquireResponse.model_validate(response.json())

    async def renew_lease(
        self,
        lease_id: UUID,
        worker_id: UUID,
        lease_token: str,
    ) -> None:
        payload = LeaseMutationRequest(worker_id=worker_id, lease_token=lease_token)
        response = await self._client.post(
            f"/api/v1/internal/leases/{lease_id}/renew",
            json=payload.model_dump(mode="json"),
        )
        response.raise_for_status()

    async def release_lease(
        self,
        lease_id: UUID,
        worker_id: UUID,
        lease_token: str,
    ) -> None:
        payload = LeaseMutationRequest(worker_id=worker_id, lease_token=lease_token)
        response = await self._client.post(
            f"/api/v1/internal/leases/{lease_id}/release",
            json=payload.model_dump(mode="json"),
        )
        response.raise_for_status()
