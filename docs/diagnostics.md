# Diagnostics

[Documentation](README.md) · [Installation](../README.md)

Both editions include TRKDUMP on A:. `make trkdump` also builds a standalone
COM under `dist/tools/`. A loose COM at the SD card root is not visible to
CP/M: it must be inside a hard-disk filesystem.

## Check the RAM disk

**Hardware result, 2026-09-13:** The RAM disk works on physical hardware with
the standard CP/M package. The independent full-256-KiB memory
test also passed; that diagnostic has now been retired. File retention across
hardware RESET remains a separate check.

Run `make pro-coboard`, copy its three SD files to the card and boot.
On a 256 KiB board, confirm **G:127K-MEM** appears alongside A–F, then run:

```text
DIR G:
PIP G:=A:P2EDIT.COM[OV]
DIR G:
STAT G:DSK:
```

`[OV]` requests a binary copy with verification. Press Ctrl-C followed
by RETURN at the CP/M prompt and check `DIR G:` again. Then try hardware RESET and check again.
The original driver is intended to retain files across RESET; it does not
retain them across power loss. Confirm A:, D:, E: and F: are still readable.

For a host-side comparison, copy the file back under a new name:

```text
PIP A:EDITBACK.COM=G:P2EDIT.COM[O]
```

Preserve any existing EDITBACK.COM before doing this. Bring back the card's
HD0 image and compare its EDITBACK.COM and P2EDIT.COM using the disk tool.
Report the boot display and any disk-error messages. Emulation has already
verified a full 126 KiB binary round trip on the 256 KiB board model.

## Capture a floppy's boot tracks

Boot the normal SASI A–F system, select user 0 and insert a P2000C 640 KB floppy
in drive B: (physical floppy 1) or C: (physical floppy 2). Run:

```text
A:
USER 0
TRKDUMP B:
```

The program reads both reserved 4 KiB tracks without writing to the floppy.
It writes `A:COBOARD.TMP`, reads back and verifies all 8,192 bytes, then renames
it to `A:COBOARD.TRK`. Existing TMP/TRK files are never overwritten. Success:

```text
SUCCESS: A:COBOARD.TRK contains 8192 verified bytes.
```

To retain one capture before another, use `REN FIRST.TRK=COBOARD.TRK`.
On failure, keep the message and any TMP file for inspection. After success,
bring the SD card back and copy its HD0 image outside `dist/`. Extract with:

```console
PYTHONPATH=src python3 -m p2000c_disk get /path/to/HD0_RETURNED.hda COBOARD.TRK /path/to/COBOARD-FLOPPY.TRK --partition low --no-clobber
```

This captures boot tracks, not the whole floppy. If needed, use
`PIP A:COCONF.DAT=B:CONFIG.DAT` to copy CONFIG tables separately, preserving
any existing COCONF.DAT first. A floppy capture is not ready-made SASI boot
tracks. See the [CoPower analysis](technical/coboard.md).

TRKDUMP uses BIOS READ and validates the drive geometries and sector
translation. It captures into RAM before creating files and compares the
complete saved file, including EOF. Source is `src/asm/trkdump.asm` in host
`z80asm` syntax, not CP/M ASM.COM syntax. Its returned real-hardware capture
is the evidence used in the CoPower analysis.
