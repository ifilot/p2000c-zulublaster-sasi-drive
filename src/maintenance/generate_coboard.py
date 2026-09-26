#!/usr/bin/env python3
"""Reproduce the bundled CoPower tracks using the original CONFIG under CP/M.

Normal distribution builds use the bundled result and need no emulator/ROM.
This maintenance operation runs only on temporary media.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
from pathlib import Path
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from p2000c_disk.assembly import ROOT
from p2000c_disk.builder import build_image
from p2000c_disk.config import COBOARD_SYSTEM_SHA256
from p2000c_disk.filesystem import put_files

VENDOR_SYSTEM_SHA256 = "b40393849fac889bac5ac0c8d7864ae2021ae1e04f111941b41981995af50f7c"
DONOR_SHA256 = "81b4605b10bbd06d9dc4ae0c79b71ecaf011081830fc75bed7509787d075b2d8"


def generate(emulator: Path, ipl: Path) -> bytes:
    with tempfile.TemporaryDirectory(prefix="coboard-config-") as temporary:
        image = Path(temporary) / "HD0_256.hda"
        build_image(image, ROOT / "assets/boot/hdboot-split.trk")
        put_files(image, sorted((ROOT / "assets/software/core").iterdir()), partition="low")
        put_files(image, sorted((ROOT / "assets/software/cpm/system/copower-tools").glob("CBIOS*.COM")),
                  partition="low")
        command = [str(emulator), "--ipl", str(ipl), "--hard-disk-0", str(image),
                   "--fast-storage", "--copower", "--write-through"]

        def wait(text):
            command.extend(["--wait-for", text])

        def send(text):
            command.extend(["--send", text])

        def run(cycles=1000000):
            command.extend(["--run", str(cycles)])

        wait("A>")
        send("CONFIG\\r")
        wait("Select or <CR>")
        send("\\r")
        wait("MAIN MENU")
        send("2")
        wait("Following tables")
        send("1")
        wait("Name of table")
        send("p2012hd\\r")
        run()
        send("2")
        run()
        # LF selects the next drive. H12/H13 are HD1 low/high; H22/H23 HD2.
        send("H12\\nF12\\nF22\\nH13\\nH22\\nH23\\nR")
        run(12000000)
        send("\\x1b")
        run()
        send("3")
        wait("Name of table to save")
        send("SASIRAM\\r")
        run(2000000)
        send("0")
        run()
        send("1")
        run(3000000)
        # Disk SASIRAM, UK/NL keyboard and video, EMPTY printer.
        send("4\\x06S\\x068\\x061\\r")
        wait("Default at startup")
        send("N")
        wait("Printer timeout")
        send("10\\r")
        wait("Autostart string")
        send("\\r")
        wait("Welcome message")
        send("Hello P2000C\\r")
        wait("Check that the correct disk")
        send("\\r")
        wait("MAIN MENU")
        run()
        result = subprocess.run(command, capture_output=True, text=True, timeout=60)
        if result.returncode:
            raise ValueError(result.stdout + result.stderr)
        system = bytearray(image.read_bytes()[:8192])
    if sha256(system).hexdigest() != VENDOR_SYSTEM_SHA256:
        raise ValueError("CONFIG output differs from the reviewed vendor system; no tracks published")
    donor = (ROOT / "assets/boot/coboard-driver.bin").read_bytes()
    if len(donor) != 214 or sha256(donor).hexdigest() != DONOR_SHA256:
        raise ValueError("Recovered driver data changed; no tracks published")
    # Exact bytes recovered from Ivo's floppy: three 9-byte size profiles,
    # followed by the 187-byte 8088 initializer/resident handler. The vendor
    # build uses the same initializer/mailbox addresses and transfer ABI.
    system[0x1C57:0x1C72] = donor[:27]
    system[0x1C98:0x1D53] = donor[27:]
    if sha256(system).hexdigest() != COBOARD_SYSTEM_SHA256:
        raise ValueError("Combined system differs from the reviewed result")
    return bytes(system)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--emulator", required=True, type=Path)
    parser.add_argument("--ipl", required=True, type=Path)
    parser.add_argument("--output", type=Path, default=ROOT / "assets/boot/hdboot-coboard.trk")
    parser.add_argument("--check", action="store_true", help="compare without changing the output")
    args = parser.parse_args()
    try:
        system = generate(args.emulator, args.ipl)
        if args.check:
            if args.output.read_bytes() != system:
                raise ValueError("Bundled tracks differ from regenerated tracks")
            print("Regenerated CoPower tracks match byte-for-byte")
        else:
            args.output.write_bytes(system)
            print(f"Wrote {args.output}")
    except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
