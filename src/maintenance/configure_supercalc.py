# SPDX-FileCopyrightText: 2026 P2000C SASI Distribution contributors
# SPDX-License-Identifier: GPL-3.0-or-later

#!/usr/bin/env python3
"""Apply the P2000C terminal profile to SuperCalc 2 release 1.00."""
from __future__ import annotations

import argparse
from hashlib import sha256
from pathlib import Path


SOURCE_SHA256 = "cae2fa869e6a4f0a862fc8faf67ae85d482218726cfd9aad3a5ca299ad558c99"
OUTPUT_SHA256 = "1967497109491a0b3d7754ef132c735c541a70dc77c2cd826a2938500eca2412"


def configure(data: bytes) -> bytes:
    if sha256(data).hexdigest() != SOURCE_SHA256:
        raise ValueError("input is not the verified P2000M VT52 SC2.COM")
    configured = bytearray(data)
    configured[0x80:0x8F] = b"P2000C VT52   \0"
    configured[0xB9] = ord("C")                 # CTRL-C cancellation label
    configured[0xF4:0xFA] = bytes([1, 12, 0, 0, 0, 0])  # form-feed clear
    # Philips CP/M Reference, chapter 10. ESC p starts the terminal's
    # Intel HEX loader; it must never be used for VT52 inverse video here.
    configured[0xEB:0xF4] = bytes([1, 1]) + bytes(7)  # SOH: home
    configured[0x106:0x10F] = bytes([2, 27, ord("k")]) + bytes(6)
    configured[0x123:0x12C] = bytes([3, 27, ord("0"), 0x50]) + bytes(5)
    configured[0x12C:0x135] = bytes([3, 27, ord("0"), 0x40]) + bytes(5)
    configured[0x15F:0x167] = bytes([
        1, 0x05,  # up: Ctrl-E
        1, 0x18,  # down: Ctrl-X
        1, 0x13,  # left: Ctrl-S
        1, 0x04,  # right: Ctrl-D
    ])
    result = bytes(configured)
    if sha256(result).hexdigest() != OUTPUT_SHA256:
        raise ValueError("generated P2000C SC2.COM has an unexpected checksum")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.write_bytes(configure(args.source.read_bytes()))
    print(f"Wrote verified {args.output}")


if __name__ == "__main__":
    main()
