# SPDX-FileCopyrightText: 2026 P2000C SASI Distribution contributors
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

from pathlib import Path

import pytest

from p2000c_disk import constants
from p2000c_disk.emulator import emulator_command


@pytest.fixture(scope="session")
def headless_emulator():
    """Compile once per test session; compilation failures must fail tests."""
    return emulator_command()


@pytest.fixture
def blank_image(tmp_path: Path) -> Path:
    path = tmp_path / "blank.hda"
    chunk = bytes([constants.DEFAULT_FILL_BYTE]) * (1024 * 1024)
    with path.open("wb") as stream:
        remaining = constants.IMAGE_SIZE
        while remaining:
            part = chunk[: min(len(chunk), remaining)]
            stream.write(part)
            remaining -= len(part)
    return path
