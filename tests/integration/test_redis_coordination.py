from uuid import uuid4

import pytest

from autobuy.orchestration.redis import RedisCoordinator
from autobuy.settings import Settings


@pytest.mark.asyncio
async def test_redis_coordination_round_trip() -> None:
    settings = Settings(redis_namespace=f"test-{uuid4().hex}")
    coordinator = RedisCoordinator(settings)

    worker_id = uuid4()
    profile_id = uuid4()
    lease_id = uuid4()
    job_id = uuid4()

    try:
        assert await coordinator.ping()

        await coordinator.set_worker_heartbeat(worker_id)
        assert await coordinator.has_worker_heartbeat(worker_id)

        assert await coordinator.acquire_profile_lock(profile_id, lease_id)
        assert not await coordinator.acquire_profile_lock(profile_id, uuid4())
        assert await coordinator.renew_profile_lock(profile_id, lease_id)

        await coordinator.enqueue_job("bestbuy", job_id)
        assert await coordinator.dequeue_job("bestbuy") == job_id

        assert await coordinator.increment_rate_counter("worker-test", window_seconds=10) == 1
        assert await coordinator.increment_rate_counter("worker-test", window_seconds=10) == 2

        assert await coordinator.release_profile_lock(profile_id, lease_id)
    finally:
        await coordinator.close()
