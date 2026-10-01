# SPDX-FileCopyrightText: 2026 P2000C SASI Distribution contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Host-side assembly of standalone CP/M diagnostics."""
from __future__ import annotations

import os
from pathlib import Path

import shutil
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[2]


def assemble_program(source: Path, destination: Path, assembler: str = "z80asm",
                     *, maximum_size: int = 0xFEFF, cwd: Path | None = None) -> None:
    executable = shutil.which(assembler)
    if executable is None:
        raise ValueError(f"Assembler not found: {assembler}; install z80asm")
    subprocess.run([str(Path(executable).resolve()), "-o", str(destination.resolve()),
                    str(source.resolve())], cwd=cwd, check=True, capture_output=True, text=True)
    if not destination.is_file() or not 0 < destination.stat().st_size <= maximum_size:
        raise ValueError(f"Assembler did not produce a valid-sized {destination.name}")


def build_trkdump(dist: Path, assembler: str = "z80asm", root: Path = ROOT) -> Path:
    destination = dist / "tools"
    destination.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".trkdump-", dir=destination) as temporary:
        stage = Path(temporary) / "TRKDUMP.COM"
        assemble_program(root / "src/asm/trkdump.asm", stage, assembler,
                         maximum_size=0x4000 - 0x100)
        os.replace(stage, destination / stage.name)
    shutil.copyfile(root / "docs/diagnostics.md", destination / "README.md")
    return destination / "TRKDUMP.COM"
