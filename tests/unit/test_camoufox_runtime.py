"""Fast profile-path guard tests; no browser binary or retailer required."""

from pathlib import Path

import pytest

from autobuy.workers.camoufox_runtime import validate_profile_directory


def test_profile_must_be_absolute() -> None:
    with pytest.raises(ValueError, match="absolute"):
        validate_profile_directory(Path("relative/profile"))


def test_profile_must_not_be_root() -> None:
    with pytest.raises(ValueError, match="root"):
        validate_profile_directory(Path("/"))


def test_profile_accepts_isolated_location(tmp_path: Path) -> None:
    path = tmp_path / "retailer-session"
    assert validate_profile_directory(path) == path.resolve()


def test_profile_rejects_symlink(tmp_path: Path) -> None:
    original = tmp_path / "original"
    original.mkdir()
    link = tmp_path / "linked"
    link.symlink_to(original, target_is_directory=True)
    with pytest.raises(ValueError, match="symbolic link"):
        validate_profile_directory(link)
