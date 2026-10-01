# SPDX-FileCopyrightText: 2026 P2000C SASI Distribution contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Smoke-test the released P2000C-native Othello game on F:."""
import shutil
import subprocess

import pytest

from p2000c_disk.distribution import build_distribution


@pytest.mark.integration
def test_released_othello_starts_and_uses_bitmap_graphics(tmp_path, headless_emulator):
    if not shutil.which("z80asm"):
        pytest.skip("install z80asm")
    package = build_distribution("pro", tmp_path)
    result = subprocess.run([
        *headless_emulator,
        "--hard-disk-0", str(package / "HD0_256.hda"),
        "--hard-disk-1", str(package / "HD1_256.hda"), "--fast-storage",
        "--wait-for", "A>", "--send", "F:\\rOTHELLO\\r", "--run", "3000000",
        "--send", "1", "--run", "3000000",
        "--output", "json",
    ], capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stdout + result.stderr
    assert '"graphics_mode": "high-512"' in result.stdout
    assert '"nonzero_graphics_bytes": 0' not in result.stdout
