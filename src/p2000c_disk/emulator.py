# SPDX-FileCopyrightText: 2026 P2000C SASI Distribution contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Build and drive the repository's headless native emulator.

Python sends a whole scenario to one process; the CPU loop stays in C++.
Disk writes use disposable copies unless --write-through is explicitly passed.
"""
from __future__ import annotations

import argparse
from collections.abc import Sequence
import json
import os
from pathlib import Path
import subprocess

from .assembly import ROOT

SOURCE = ROOT / "tools/emulator"
BUILD = ROOT / "build/emulator"
IPL = SOURCE / "firmware/IPLDUMP.BIN"


def build_emulator(build_dir: Path = BUILD) -> Path:
    """Configure and incrementally compile an optimized, Qt-free executable."""
    subprocess.run(["cmake", "-S", str(SOURCE), "-B", str(build_dir),
                    "-DCMAKE_BUILD_TYPE=Release"], check=True)
    subprocess.run(["cmake", "--build", str(build_dir), "--config", "Release",
                    "--parallel", "2"], check=True)
    filename = "p2000c-mini.exe" if os.name == "nt" else "p2000c-mini"
    for binary in (build_dir / filename, build_dir / "Release" / filename):
        if binary.is_file():
            return binary.resolve()
    raise FileNotFoundError(f"CMake did not produce {filename} in {build_dir}")


def emulator_command() -> list[str]:
    """Use the bundled runner/ROM by default; retain explicit external overrides."""
    executable = os.environ.get("P2000C_EMULATOR") or str(build_emulator())
    ipl = Path(os.environ.get("P2000C_IPL", str(IPL)))
    if not ipl.is_file():
        raise FileNotFoundError(f"IPL ROM not found: {ipl}")
    return [executable, "--ipl", str(ipl)]


def run_scenario(arguments: Sequence[str], *, command: Sequence[str] | None = None,
                 timeout: float = 60) -> dict:
    """Run ordered CLI actions and return screen, CPU and memory state as JSON.

    Supply a command from emulator_command() when running several scenarios to
    avoid repeating the incremental build check. A failed wait raises
    CalledProcessError with the diagnostic JSON in its stdout attribute.
    """
    result = subprocess.run([*(command if command is not None else emulator_command()),
                             *arguments, "--output", "json"],
                            capture_output=True, text=True, timeout=timeout, check=True)
    return json.loads(result.stdout)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the headless P2000C test core")
    parser.parse_args()
    print(build_emulator())


if __name__ == "__main__":
    main()
