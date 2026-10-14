"""Encrypted retailer-profile artifact lifecycle."""

from __future__ import annotations

from uuid import UUID

from autobuy.workers.profile_store.crypto import EncryptedArtifact, EnvelopeEncryptor
from autobuy.workers.profile_store.storage import ObjectStore


def profile_encryption_context(profile_id: UUID) -> bytes:
    return f"autobuy:retailer-profile:{profile_id}".encode("utf-8")


def profile_object_key(profile_id: UUID, artifact_version: int) -> str:
    if artifact_version < 1:
        raise ValueError("Artifact version must be positive")
    return f"retailer-profiles/{profile_id}/{artifact_version}.json.enc"


class ProfileArtifactService:
    def __init__(self, store: ObjectStore, encryptor: EnvelopeEncryptor) -> None:
        self._store = store
        self._encryptor = encryptor

    async def save(
        self,
        profile_id: UUID,
        artifact_version: int,
        plaintext_profile: bytes,
    ) -> str:
        context = profile_encryption_context(profile_id)
        artifact = self._encryptor.encrypt(plaintext_profile, context=context)
        key = profile_object_key(profile_id, artifact_version)
        await self._store.put(key, artifact.to_bytes())
        return key

    async def load(self, profile_id: UUID, object_key: str) -> bytes:
        raw = await self._store.get(object_key)
        artifact = EncryptedArtifact.from_bytes(raw)
        return self._encryptor.decrypt(
            artifact,
            context=profile_encryption_context(profile_id),
        )

    async def delete(self, object_key: str) -> None:
        await self._store.delete(object_key)
