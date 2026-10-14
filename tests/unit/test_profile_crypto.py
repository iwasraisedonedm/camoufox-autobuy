import os
from uuid import uuid4

import pytest
from cryptography.exceptions import InvalidTag

from autobuy.workers.profile_store.crypto import EnvelopeEncryptor, LocalKeyWrapper
from autobuy.workers.profile_store.service import profile_encryption_context


def test_profile_encryption_round_trip() -> None:
    profile_id = uuid4()
    encryptor = EnvelopeEncryptor(LocalKeyWrapper(os.urandom(32)))
    context = profile_encryption_context(profile_id)
    plaintext = b"synthetic browser profile bytes"

    artifact = encryptor.encrypt(plaintext, context=context)

    assert encryptor.decrypt(artifact, context=context) == plaintext
    assert plaintext not in artifact.to_bytes()


def test_profile_encryption_binds_profile_context() -> None:
    encryptor = EnvelopeEncryptor(LocalKeyWrapper(os.urandom(32)))
    artifact = encryptor.encrypt(
        b"profile",
        context=profile_encryption_context(uuid4()),
    )

    with pytest.raises(InvalidTag):
        encryptor.decrypt(
            artifact,
            context=profile_encryption_context(uuid4()),
        )
