"""Generic worker process coordination loop."""

from __future__ import annotations

import asyncio
import socket
from collections.abc import Awaitable, Callable
from contextlib import suppress
from uuid import UUID

import structlog

from autobuy import __version__
from autobuy.adapters.registry import AdapterRegistry
from autobuy.control_plane.schemas import JobAssignmentRead
from autobuy.orchestration.redis import RedisCoordinator
from autobuy.settings import Settings
from autobuy.workers.client import WorkerControlPlaneClient

logger = structlog.get_logger(__name__)

AssignmentHandler = Callable[[UUID, JobAssignmentRead], Awaitable[None]]


class WorkerRuntime:
    def __init__(
        self,
        settings: Settings,
        registry: AdapterRegistry,
        handler: AssignmentHandler,
    ) -> None:
        self._settings = settings
        self._registry = registry
        self._handler = handler
        self._coordinator = RedisCoordinator(settings)
        self._client = WorkerControlPlaneClient(settings)
        self._worker_id: UUID | None = None
        self._stopping = asyncio.Event()

    async def close(self) -> None:
        self._stopping.set()
        await self._client.close()
        await self._coordinator.close()

    async def run_forever(self) -> None:
        retailer_codes = self._registry.retailer_codes()
        if not retailer_codes:
            raise RuntimeError("Worker cannot start without registered retailer adapters")

        instance_id = socket.gethostname()
        worker = await self._client.register(instance_id, __version__)
        self._worker_id = worker.id

        heartbeat_task = asyncio.create_task(self._heartbeat_loop(worker.id))
        try:
            while not self._stopping.is_set():
                handled = False
                for retailer_code in retailer_codes:
                    job_id = await self._coordinator.dequeue_job(
                        retailer_code,
                        timeout_seconds=self._settings.worker_poll_timeout_seconds,
                    )
                    if job_id is None:
                        continue
                    assignment = await self._client.assignment(job_id)
                    await self._handler(worker.id, assignment)
                    handled = True
                    if self._stopping.is_set():
                        break
                if not handled:
                    await asyncio.sleep(0)
        finally:
            self._stopping.set()
            heartbeat_task.cancel()
            with suppress(asyncio.CancelledError):
                await heartbeat_task
            await self.close()

    async def _heartbeat_loop(self, worker_id: UUID) -> None:
        while not self._stopping.is_set():
            await self._client.heartbeat(worker_id)
            try:
                await asyncio.wait_for(
                    self._stopping.wait(),
                    timeout=self._settings.worker_heartbeat_interval_seconds,
                )
            except TimeoutError:
                continue
