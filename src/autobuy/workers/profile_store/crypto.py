"""Envelope encryption for sensitive retailer-profile artifacts."""

from __future__ import annotations

import base64
import json
import os
from dataclasses import asdict, dataclass
from typing import Protocol

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

_PROFILE_ALGORITHM = "AES-256-GCM"
_WRAP_ALGORITHM = "AES-256-GCM"


class KeyWrapper(Protocol):
    """Wrap/unwrap data-encryption keys.

    Production implementations should delegate to the configured KMS.
    """

    @property
    def key_id(self) -> str: ...

    def wrap_key(self, plaintext_key: bytes, *, context: bytes) -> tuple[bytes, bytes]: ...

    def unwrap_key(
        self,
        wrapped_key: bytes,
        wrap_nonce: bytes,
        *,
        context: bytes,
    ) -> bytes: ...


@dataclass(frozen=True, slots=True)
class EncryptedArtifact:
    version: int
    algorithm: str
    key_wrap_algorithm: str
    key_id: str
    nonce_b64: str
    ciphertext_b64: str
    wrapped_key_b64: str
    wrap_nonce_b64: str

    def to_bytes(self) -> bytes:
        return json.dumps(asdict(self), separators=(",", ":"), sort_keys=True).encode("utf-8")

    @classmethod
    def from_bytes(cls, raw: bytes) -> EncryptedArtifact:
        data = json.loads(raw.decode("utf-8"))
        if not isinstance(data, dict):
            raise ValueError("Encrypted profile artifact must be a JSON object")
        return cls(
            version=int(data["version"]),
            algorithm=str(data["algorithm"]),
            key_wrap_algorithm=str(data["key_wrap_algorithm"]),
            key_id=str(data["key_id"]),
            nonce_b64=str(data["nonce_b64"]),
            ciphertext_b64=str(data["ciphertext_b64"]),
            wrapped_key_b64=str(data["wrapped_key_b64"]),
            wrap_nonce_b64=str(data["wrap_nonce_b64"]),
        )


class LocalKeyWrapper:
    """Local-development key wrapper.

    The key must come from an ignored local secret source. Do not use this provider as
    the production KMS implementation.
    """

    def __init__(self, key: bytes, *, key_id: str = "local-dev") -> None:
        if len(key) != 32:
            raise ValueError("Local key-encryption key must be exactly 32 bytes")
        self._key = key
        self._key_id = key_id

    @property
    def key_id(self) -> str:
        return self._key_id

    def wrap_key(self, plaintext_key: bytes, *, context: bytes) -> tuple[bytes, bytes]:
        nonce = os.urandom(12)
        wrapped = AESGCM(self._key).encrypt(nonce, plaintext_key, context)
        return wrapped, nonce

    def unwrap_key(
        self,
        wrapped_key: bytes,
        wrap_nonce: bytes,
        *,
        context: bytes,
    ) -> bytes:
        return AESGCM(self._key).decrypt(wrap_nonce, wrapped_key, context)


class EnvelopeEncryptor:
    """Encrypt/decrypt profile blobs with a random per-artifact data key."""

    def __init__(self, key_wrapper: KeyWrapper) -> None:
        self._key_wrapper = key_wrapper

    def encrypt(self, plaintext: bytes, *, context: bytes) -> EncryptedArtifact:
        data_key = AESGCM.generate_key(bit_length=256)
        nonce = os.urandom(12)
        ciphertext = AESGCM(data_key).encrypt(nonce, plaintext, context)
        wrapped_key, wrap_nonce = self._key_wrapper.wrap_key(data_key, context=context)
        return EncryptedArtifact(
            version=1,
            algorithm=_PROFILE_ALGORITHM,
            key_wrap_algorithm=_WRAP_ALGORITHM,
            key_id=self._key_wrapper.key_id,
            nonce_b64=base64.b64encode(nonce).decode("ascii"),
            ciphertext_b64=base64.b64encode(ciphertext).decode("ascii"),
            wrapped_key_b64=base64.b64encode(wrapped_key).decode("ascii"),
            wrap_nonce_b64=base64.b64encode(wrap_nonce).decode("ascii"),
        )

    def decrypt(self, artifact: EncryptedArtifact, *, context: bytes) -> bytes:
        if artifact.version != 1:
            raise ValueError("Unsupported encrypted artifact version")
        if artifact.algorithm != _PROFILE_ALGORITHM:
            raise ValueError("Unsupported profile encryption algorithm")
        if artifact.key_wrap_algorithm != _WRAP_ALGORITHM:
            raise ValueError("Unsupported key-wrap algorithm")
        if artifact.key_id != self._key_wrapper.key_id:
            raise ValueError("Encrypted artifact key ID does not match configured key wrapper")

        nonce = base64.b64decode(artifact.nonce_b64, validate=True)
        ciphertext = base64.b64decode(artifact.ciphertext_b64, validate=True)
        wrapped_key = base64.b64decode(artifact.wrapped_key_b64, validate=True)
        wrap_nonce = base64.b64decode(artifact.wrap_nonce_b64, validate=True)

        data_key = self._key_wrapper.unwrap_key(
            wrapped_key,
            wrap_nonce,
            context=context,
        )
        return AESGCM(data_key).decrypt(nonce, ciphertext, context)
