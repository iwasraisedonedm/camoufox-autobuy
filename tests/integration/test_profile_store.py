import os
from uuid import uuid4

import pytest

from autobuy.workers.profile_store.crypto import EnvelopeEncryptor, LocalKeyWrapper
from autobuy.workers.profile_store.service import ProfileArtifactService
from autobuy.workers.profile_store.storage import FilesystemObjectStore


@pytest.mark.asyncio
async def test_profile_artifact_filesystem_round_trip(tmp_path) -> None:
    profile_id = uuid4()
    store = FilesystemObjectStore(tmp_path)
    service = ProfileArtifactService(
        store,
        EnvelopeEncryptor(LocalKeyWrapper(os.urandom(32))),
    )

    object_key = await service.save(profile_id, 1, b"synthetic-profile-state")

    assert await store.exists(object_key)
    assert await service.load(profile_id, object_key) == b"synthetic-profile-state"

    await service.delete(object_key)
    assert not await store.exists(object_key)
