"""Redis-backed ephemeral coordination.

PostgreSQL remains authoritative. Redis contains only reconstructable coordination state.
"""

from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from typing import Any, Final, cast
from uuid import UUID

from redis.asyncio import Redis
from redis.asyncio.client import Pipeline

from autobuy.settings import Settings

_RELEASE_LOCK_SCRIPT: Final[str] = """
if redis.call("get", KEYS[1]) == ARGV[1] then
    return redis.call("del", KEYS[1])
end
return 0
"""


@dataclass(frozen=True, slots=True)
class LeaseToken:
    raw: str
    digest: str


def generate_lease_token() -> LeaseToken:
    raw = secrets.token_urlsafe(32)
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return LeaseToken(raw=raw, digest=digest)


class RedisCoordinator:
    """Ephemeral coordination facade.

    Keys are namespaced by environment and are safe to reconstruct from durable state.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        redis_factory = cast(Any, Redis.from_url)  # pyright: ignore[reportUnknownMemberType]
        self._redis: Redis = redis_factory(settings.redis_url, decode_responses=True)
        self._prefix = f"{settings.redis_namespace}:{settings.environment}"

    def _key(self, *parts: object) -> str:
        return ":".join((self._prefix, *(str(part) for part in parts)))

    async def close(self) -> None:
        await self._redis.aclose()

    async def ping(self) -> bool:
        ping = cast(Any, self._redis.ping)  # pyright: ignore[reportUnknownMemberType]
        return bool(await ping())

    async def set_worker_heartbeat(self, worker_id: UUID) -> None:
        await self._redis.set(
            self._key("worker", worker_id, "heartbeat"),
            "1",
            ex=self._settings.worker_heartbeat_ttl_seconds,
        )

    async def has_worker_heartbeat(self, worker_id: UUID) -> bool:
        return bool(await self._redis.exists(self._key("worker", worker_id, "heartbeat")))

    async def acquire_profile_lock(
        self,
        profile_id: UUID,
        lease_id: UUID,
        *,
        ttl_seconds: int | None = None,
    ) -> bool:
        ttl = ttl_seconds or self._settings.worker_lease_ttl_seconds
        return bool(
            await self._redis.set(
                self._key("profile", profile_id, "lease"),
                str(lease_id),
                nx=True,
                ex=ttl,
            )
        )

    async def owns_profile_lock(self, profile_id: UUID, lease_id: UUID) -> bool:
        current = await self._redis.get(self._key("profile", profile_id, "lease"))
        return current == str(lease_id)

    async def renew_profile_lock(
        self,
        profile_id: UUID,
        lease_id: UUID,
        *,
        ttl_seconds: int | None = None,
    ) -> bool:
        key = self._key("profile", profile_id, "lease")
        current = await self._redis.get(key)
        if current != str(lease_id):
            return False
        ttl = ttl_seconds or self._settings.worker_lease_ttl_seconds
        await self._redis.expire(key, ttl)
        return True

    async def release_profile_lock(self, profile_id: UUID, lease_id: UUID) -> bool:
        result = await self._redis.eval(
            _RELEASE_LOCK_SCRIPT,
            1,
            self._key("profile", profile_id, "lease"),
            str(lease_id),
        )
        return bool(result)

    async def enqueue_job(self, retailer_code: str, job_id: UUID) -> None:
        await self._redis.rpush(self._key("queue", retailer_code), str(job_id))

    async def dequeue_job(
        self,
        retailer_code: str,
        *,
        timeout_seconds: int = 1,
    ) -> UUID | None:
        result = await self._redis.blpop(
            self._key("queue", retailer_code),
            timeout=timeout_seconds,
        )
        if result is None:
            return None
        _, raw_job_id = result
        if isinstance(raw_job_id, bytes):
            raw_job_id = raw_job_id.decode("utf-8")
        return UUID(raw_job_id)

    async def increment_rate_counter(
        self,
        bucket: str,
        *,
        window_seconds: int,
    ) -> int:
        key = self._key("rate", bucket)
        pipeline: Pipeline = self._redis.pipeline(transaction=True)
        pipeline.incr(key)
        pipeline.expire(key, window_seconds, nx=True)
        count, _ = await pipeline.execute()
        return int(count)
