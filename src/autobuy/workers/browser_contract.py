"""Browser execution boundary shared by isolated worker runtimes.

Browser-specific objects stay behind this interface. Customer profile ownership,
encryption, and leases remain responsibilities of the worker infrastructure.
"""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from typing import Protocol


class BrowserEngine(StrEnum):
    CAMOUFOX = "camoufox"
    PATCHRIGHT = "patchright"


class BrowserProfileIncompatibleError(ValueError):
    """A browser profile cannot be restored by a different engine."""


def validate_profile_engine(
    stored_engine: BrowserEngine, requested_engine: BrowserEngine
) -> None:
    """Reject restoring a profile produced by an incompatible browser engine."""
    if stored_engine != requested_engine:
        raise BrowserProfileIncompatibleError(
            f"Profile engine {stored_engine.value!r} is incompatible "
            f"with requested engine {requested_engine.value!r}"
        )


class BrowserRuntime(Protocol):
    """Minimum lifecycle contract for a single leased customer runtime."""

    @property
    def engine(self) -> BrowserEngine: ...

    async def start(self, profile_dir: Path) -> None: ...

    async def close(self) -> None: ...
