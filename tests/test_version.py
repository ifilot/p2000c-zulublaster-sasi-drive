# SPDX-FileCopyrightText: 2026 P2000C SASI Distribution contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Ensure semantic distro version metadata and release notes cannot drift."""
import tomllib
from pathlib import Path

import pytest

from p2000c_disk.changelog import release_notes
from p2000c_disk.release import PREFIX
from p2000c_disk.version import DISPLAY_VERSION, VERSION, validate_semantic_version


def test_version_is_shared_by_packaging_menu_changelog_and_archives():
    root = Path(__file__).parents[1]
    assert (root / "VERSION").read_text() == "1.2.3\n"
    assert VERSION == "1.2.3"
    assert DISPLAY_VERSION == "v1.2.3"
    metadata = tomllib.loads((root / "pyproject.toml").read_text())
    assert metadata["project"]["license"]["text"] == "GPL-3.0-or-later"
    assert ("License :: OSI Approved :: GNU General Public License v3 or later "
            "(GPLv3+)" in metadata["project"]["classifiers"])
    assert metadata["tool"]["setuptools"]["dynamic"]["version"]["file"] == ["VERSION"]
    menu = (root / "src/menu/menu.toml").read_text()
    assert "{version}" not in menu
    menu_program = (root / "src/menu/menu.c").read_text()
    assert '"SASI-distributie: " NAVIGATOR_VERSION' in menu_program
    assert PREFIX == "p2000c-zulublaster-v1.2.3-"
    notes = release_notes()
    assert notes.startswith("## [1.2.3] - 2026-10-01\n")
    assert "### Changed" in notes


@pytest.mark.parametrize("value", ["v1.0.0", "1.0", "1.0.0.0", "01.0.0", "1.01.0", "1.0.01"])
def test_release_version_must_be_stable_semver(value):
    with pytest.raises(ValueError, match="MAJOR.MINOR.PATCH"):
        validate_semantic_version(value)
