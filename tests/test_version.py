"""Ensure semantic distro version metadata and release notes cannot drift."""
import tomllib
from pathlib import Path

import pytest

from p2000c_disk.changelog import release_notes
from p2000c_disk.release import PREFIX
from p2000c_disk.version import DISPLAY_VERSION, VERSION, validate_semantic_version


def test_version_is_shared_by_packaging_menu_changelog_and_archives():
    root = Path(__file__).parents[1]
    assert (root / "VERSION").read_text() == "1.0.0\n"
    assert VERSION == "1.0.0"
    assert DISPLAY_VERSION == "v1.0.0"
    assert tomllib.loads((root / "pyproject.toml").read_text())["tool"]["setuptools"]["dynamic"]["version"]["file"] == ["VERSION"]
    menu = (root / "src/menu/menu.toml").read_text()
    assert "{version}" in menu
    assert PREFIX == "p2000c-zulublaster-v1.0.0-"
    notes = release_notes()
    assert notes.startswith("## [1.0.0] - 2026-09-26\n")
    assert "### Added" in notes


@pytest.mark.parametrize("value", ["v1.0.0", "1.0", "1.0.0.0", "01.0.0", "1.01.0", "1.0.01"])
def test_release_version_must_be_stable_semver(value):
    with pytest.raises(ValueError, match="MAJOR.MINOR.PATCH"):
        validate_semantic_version(value)
