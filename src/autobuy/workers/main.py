"""Worker executable entry point."""

import asyncio
from uuid import UUID

from autobuy.adapters.registry import AdapterRegistry
from autobuy.control_plane.schemas import JobAssignmentRead
from autobuy.observability.logging import configure_logging
from autobuy.settings import get_settings
from autobuy.workers.runtime import WorkerRuntime


async def _unconfigured_handler(worker_id: UUID, assignment: JobAssignmentRead) -> None:
    raise RuntimeError(
        f"No execution handler configured for worker {worker_id} and job {assignment.job_id}"
    )


async def _main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)

    registry = AdapterRegistry()
    runtime = WorkerRuntime(settings, registry, _unconfigured_handler)
    await runtime.run_forever()


def run() -> None:
    asyncio.run(_main())


if __name__ == "__main__":
    run()
