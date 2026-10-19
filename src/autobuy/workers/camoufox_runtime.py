"""Camoufox browser runtime for an isolated, leased retailer profile.

The caller must obtain the exclusive RetailerProfile lease, restore its
encrypted artifact into an ephemeral private directory, then invoke this
runtime. Profile encryption, checkpointing and disposal belong to the
worker profile-store subsystem, not this module.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import cast

from camoufox.async_api import AsyncCamoufox
from playwright.async_api import BrowserContext


def validate_profile_directory(path: Path) -> Path:
    """Reject unsafe profile locations before handing them to a browser."""
    resolved = path.resolve()
    if not path.is_absolute():
        raise ValueError("Retailer profile path must be absolute")
    if resolved == Path(resolved.anchor) or resolved == Path.home().resolve():
        raise ValueError("Refusing to use a system root or home directory as a profile")
    if resolved.is_symlink() or path.is_symlink():
        raise ValueError("Profile directory must not be a symbolic link")
    return resolved


@asynccontextmanager
async def open_camoufox_profile(
    profile_directory: Path,
    *,
    headless: bool = True,
) -> AsyncIterator[BrowserContext]:
    """Open one persistent Firefox context per exclusively leased profile.

    Never share a profile directory between concurrent workers. The caller
    owns cleanup and encrypted checkpointing after this context closes.
    No account credentials or browser state are emitted to logs.
    """
    directory = validate_profile_directory(profile_directory)
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    async with AsyncCamoufox(
        persistent_context=True,
        user_data_dir=str(directory),
        headless=headless,
    ) as context:
        yield cast(BrowserContext, context)
