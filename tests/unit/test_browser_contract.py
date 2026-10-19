"""Contract-level tests without a real browser or retailer account."""

import pytest

from autobuy.workers.browser_contract import (
    BrowserEngine,
    BrowserProfileIncompatibleError,
    validate_profile_engine,
)


@pytest.mark.parametrize("engine", list(BrowserEngine))
def test_profile_can_be_reused_by_same_engine(engine: BrowserEngine) -> None:
    validate_profile_engine(engine, engine)


def test_chromium_profile_cannot_be_restored_into_camoufox() -> None:
    with pytest.raises(BrowserProfileIncompatibleError):
        validate_profile_engine(BrowserEngine.PATCHRIGHT, BrowserEngine.CAMOUFOX)


def test_camoufox_profile_cannot_be_restored_into_patchright() -> None:
    with pytest.raises(BrowserProfileIncompatibleError):
        validate_profile_engine(BrowserEngine.CAMOUFOX, BrowserEngine.PATCHRIGHT)
