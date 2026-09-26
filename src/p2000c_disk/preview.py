"""Build a disposable SD-card preview and open the P2000C desktop emulator."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from .distribution import ROOT, VARIANTS, build_distribution


def find_emulator(value: str | None, root: Path = ROOT) -> Path:
    candidates = ([value] if value else
                  [str(root.parent / "p2000c-emulator/build/p2000c"), "p2000c"])
    for candidate in candidates:
        executable = shutil.which(candidate)
        if executable:
            return Path(executable).resolve()
    raise ValueError("Graphical P2000C emulator not found. Build ../p2000c-emulator "
                     "or set EMULATOR=/path/to/p2000c (not p2000c_cli). "
                     "See docs/building.md#preview-without-hardware")


def preview(variant: str = "menu", *, coboard: bool = False,
            emulator: str | None = None, config: Path | None = None,
            assembler: str = "z80asm", coboard_system: Path | None = None,
            root: Path = ROOT, zcc: str = "zcc") -> int:
    executable = find_emulator(emulator, root)
    # The desktop app uses Qt native settings. On Linux, XDG_CONFIG_HOME
    # isolates both its preferences and the CoPower switch for this session.
    if not sys.platform.startswith("linux"):
        raise ValueError("make run currently supports Linux/WSL; on other platforms "
                         "open the built HDA files in the graphical emulator")
    if not (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")):
        raise ValueError("No graphical display found. Run from a Linux desktop or "
                         "WSL with WSLg; make run opens a graphical window")
    with tempfile.TemporaryDirectory(prefix="zulublaster-preview-") as temporary:
        work = Path(temporary)
        settings = work / "config/P2000C Emulator Project/P2000C Emulator.conf"
        settings.parent.mkdir(parents=True)
        settings.write_text("[machine]\n"
                            f"copowerEnabled={'true' if coboard else 'false'}\n"
                            "storageDelays=false\nspeed=1\n", encoding="utf-8")
        environment = dict(os.environ, XDG_CONFIG_HOME=str(work / "config"),
                           XDG_DATA_HOME=str(work / "data"), XDG_CACHE_HOME=str(work / "cache"))
        print(f"Building {variant}{'-coboard' if coboard else ''} preview...", flush=True)
        package = build_distribution(variant, work / "disks", coboard=coboard,
                                     coboard_system=coboard_system, config=config,
                                     assembler=assembler, root=root, zcc=zcc)
        command = [str(executable)]
        # Blank removable media keep both physical drives deterministic while
        # IPL boots from the disposable SASI images.
        for drive in "ab":
            floppy = work / f"floppy-{drive}.flp"
            floppy.write_bytes(bytes([0xE5]) * (640 * 1024))
            command += [f"--floppy-{drive}", str(floppy)]
        command += ["--hard-disk-0", str(package / "HD0_256.hda"),
                    "--hard-disk-1", str(package / "HD1_256.hda")]
        print("Opening emulator. Close its window to finish; preview changes are discarded.", flush=True)
        with subprocess.Popen(command, env=environment) as process:
            try:
                result = process.wait()
                return result if result >= 0 else 128 - result
            except KeyboardInterrupt:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
                return 130


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--variant", choices=VARIANTS, default="menu")
    parser.add_argument("--coboard", action="store_true")
    parser.add_argument("--emulator")
    parser.add_argument("--config", type=Path, default=ROOT / "distribution.json")
    parser.add_argument("--assembler", default="z80asm")
    parser.add_argument("--zcc", default=os.environ.get("ZCC", "zcc"))
    parser.add_argument("--coboard-system", type=Path)
    args = parser.parse_args(argv)
    try:
        return preview(**vars(args))
    except KeyboardInterrupt:
        return 130
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        detail = exc.stderr if isinstance(exc, subprocess.CalledProcessError) else str(exc)
        print(f"error: {detail}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
