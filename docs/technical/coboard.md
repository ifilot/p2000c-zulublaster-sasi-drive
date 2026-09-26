# Returned CoBoard floppy capture

[Documentation](../README.md) · [CoPower build status](../building.md#copower-status)

Inspected on 2026-09-13. The returned image is
`/mnt/d/tmp/zulublaster/HD0_256.hda` (digit zero in HD0).
Both filesystems pass verification. A: contains one track capture,
`COBOARD.TRK`, with 64 CP/M records: exactly 8,192 bytes.

The file was extracted without modifying the returned image:

```console
PYTHONPATH=src python3 -m p2000c_disk get /mnt/d/tmp/zulublaster/HD0_256.hda COBOARD.TRK docs/technical/evidence/COBOARD-FLOPPY.TRK --partition low --no-clobber
```

The original [floppy-track capture](evidence/COBOARD-FLOPPY.TRK) is preserved
alongside this analysis. It is historical evidence, not the SASI deployment
boot tracks in `assets/boot/`.

| Item | SHA-256 |
| --- | --- |
| Returned HD0 image | `256172f510e0fdd35d289ba6dc07dc3a5e925a7162776f36d17a0379db4d5e1c` |
| Extracted COBOARD.TRK | `d5b5cb8a758ac3343aad70ddc8d460c5b71f97de02cc9906e02ae3d1306f2ac1` |

## Configuration in the captured tracks

The boot display identifies **63K CP/M 2.2**, with this drive configuration
at file offset `0x1A3C`:

```text
A:640K-FL1 B:640K-FL2 C:256K-MEM D:640K-FL3
```

| Original drive | Displayed role |
| --- | --- |
| A: | 640 KB floppy drive 1 |
| B: | 640 KB floppy drive 2 |
| C: | 256 KB RAM drive |
| D: | 640 KB floppy drive 3 |

Other embedded settings include keyboard `PC UK/NG`, video `PCDK`, printer
`TEC  ESA`, and the greeting `Hallo Jan,`.

Two plausible disk parameter blocks support the floppy and RAM geometry:

| Field | At `0x19B9` (floppy) | At `0x19C8` (RAM) |
| --- | ---: | ---: |
| Sectors per track, in 128-byte records | 32 | 32 |
| Block shift / block mask | 5 / 31 | 4 / 15 |
| Extent mask | 3 | 1 |
| Maximum allocation block | 157 | 127 |
| Maximum directory entry | 127 | 63 |
| Reserved allocation bitmap | `80/00` | `80/00` |
| Directory checksum size | 32 | 0 |
| Reserved tracks | 2 | 0 |

The static RAM DPB describes 128 allocation blocks of 2,048 bytes, or 256 KiB
including directory space. **This is not necessarily the runtime geometry.**
Startup selects between the separate P2092 memory expansion and the P2093
8088 CoPower implementation, then patches the DPB and displayed size.

## How the CoPower driver works

The capture contains both Z80 initialization/BIOS code and a small 8088
program. File offsets below refer to the extracted, unmodified 8,192 bytes.
Initialization addresses use the initial load origin `D600`; relocated BIOS
addresses must not be calculated from that origin.

1. The Z80 startup probes the ordinary banked RAM expansion using ports `1E`
   and `FF` (around file offset `1B2F`). If that path is unavailable, it
   installs a nine-byte 8088 bootstrap at shared Z80 address `FFF0` and
   releases the CoPower board through port `31` (offsets `1B4A–1B57`).
2. The 8088 reset vector jumps to `F000:F298`, the worker initializer at
   file offset `1C98`. The top 64 KiB of 8088 address space maps to Z80 RAM;
   CoPower local RAM starts at physical zero. This agrees with the memory
   map in section 4.3 of the
   [Philips P2093 manual](https://electrickery.hosting.philpem.me.uk/comp/p2000c/doc/P2093_CoPowerBoard0-8.pdf).
3. That initializer flips and restores a word at `7FFF:000F` (physical
   `7FFFF/80000`). The XOR of the before/after values is written back into
   a Z80 instruction operand at `F160`. This is a coarse boundary probe,
   **not a full memory test**.
4. Z80 code at file offsets `1B5F–1B87` selects a size profile and installs
   the CoPower transfer routine at runtime address `FD53`. The three profile
   records at `1C57`, `1C60`, `1C69` encode **956K, 508K, 127K** respectively.
   The third record is the fallback when the boundary probe changes no bits.
5. The 8088 installs its interrupt vector and resident transfer code in the
   first `55h` bytes of local RAM. Its stack and transfer limit also occupy
   the first 256 bytes. Disk transfers add `10h` paragraphs to their local
   address, so filesystem storage starts at physical `00100`, not zero.
6. For a read/write, the Z80 publishes the RAM offset and direction in a
   shared mailbox at `FD89–FD8C`, with buffer/count information at `FF9C/FF9E`.
   It writes interrupt vector zero to port `30`, then waits for the 8088 to
   replace the busy status. The 8088 interrupt handler copies bytes between
   shared Z80 RAM and local RAM using `REP MOVSB`, reports status, and returns
   to its interruptible `HLT` loop. The BIOS handles CP/M's 128-byte records
   through its normal sector buffering.

The original driver compares its resident 8088 code before reinstalling it.
When different, it installs the code and initializes 16 KiB from `00100` to
`040FF` with `E5`. Matching code lets it preserve the existing RAM disk.
This is consistent with the manual's description of persistence across reset;
it does not imply persistence across power loss.

## The 256 KiB question

The Philips manual documents physical **128, 256 and 512 KiB** CoPower
configurations (section 10.3 of the
[hardware chapters](https://electrickery.hosting.philpem.me.uk/comp/p2000c/doc/P2093_CoPowerBoard9-10.pdf)).
However, this captured driver does not have a dedicated 256 KiB CoPower
profile. With contiguous 256 KiB RAM, the probe at `7FFFF/80000` finds neither
byte writable and selects **127K**, just as it would for a 128 KiB board.
The static `256K-MEM` string therefore does not establish a 256 KiB CoPower
disk. The 956K table entry is present in the code; it is not evidence that
the documented board can physically be upgraded to that capacity.

Boot experiments with the captured tracks give:

| Simulated CoPower RAM | Runtime label | Block size | DSM / DRM | Filesystem / file capacity |
| --- | --- | --- | --- | --- |
| 256 KiB, contiguous | `C:127K-MEM` | 1 KiB | 126 / 31 | 127 KiB / 126 KiB |
| 512 KiB, contiguous | `C:508K-MEM` | 4 KiB | 126 / 127 | 508 KiB / 504 KiB |

File capacity excludes the directory's one allocation block. The 256-byte
resident area and rounding to whole blocks account for the additional space
outside the filesystem. The 256 KiB case leaves the upper half unused by
the original disk profile. The code establishes the behavior, not the
developers' reason for it; confirmation on the real board remains necessary.

**Decision: preserve this original sizing and driver implementation.** We
will not enlarge the RAM disk or modify the captured tracks. The
retired RAMTEST utility verified all physical 256 KiB independently,
without requiring a RAM disk at C: or G:.

On 2026-09-13, RAMTEST passed all four patterns
on the physical P2000C, with no bank alias detected. The independent hardware
test passes; G: is still absent from the ordinary SASI boot system because
that system has no RAM driver configured. The photograph does not validate
the separate RAM-disk integration or the original driver's runtime geometry.

To reproduce the boot experiment, construct a temporary 640 KiB floppy image
with the captured tracks first and `E5` fill for the remaining bytes, then
boot it with the sibling `p2000c-emulator` CLI using `--copower --floppy-a`.
The normal emulator provides 512 KiB. The 256 KiB experiment used a temporary
copy of its board implementation limiting local reads/writes to `40000`
bytes; neither the original emulator nor the capture was changed. This
models contiguous memory, not the board's electrical address decoding.

## Relationship to the desired SASI configuration

The capture contains neither of the recognized split-SASI DPBs. Its drive
table is the original floppy configuration, not the desired A–F SASI/floppy
configuration with a RAM drive added at G:. It must not be copied straight
to `assets/boot/hdboot-coboard.trk` or used as replacement SASI boot tracks.

The combined system described below now supplies that A–G configuration.
The original floppy capture remains unchanged.

There is no separately copied `COCONF.DAT` in the returned images. The
`CONFIG.DAT` on A: is byte-identical to `assets/software/core/CONFIG.DAT`, so it does not
provide additional configuration tables from the found floppy. HD0 high and
both HD1 filesystems are empty.

## Combined SASI boot system

`assets/boot/hdboot-coboard.trk` is an 8,192-byte combined boot system. It was
generated by the original CONFIG 1.2 under CP/M with A/D on hard disk 1
low/high, E/F on hard disk 2 low/high, B/C as 640 KiB floppies and G as RAM.
Keyboard/video remain UK/NL and the printer is EMPTY. The resulting system
is 62K CP/M, matching the ordinary SASI build.

The archived CoPower CBIOS copies contained mixed file data. Clean CBIOS61/62/63
were recovered through CP/M PIP from the emulator's original CoPower floppy
image, which handles the floppy sector ordering. Those corrected inputs are
at `assets/software/cpm/system/copower-tools/`. Other archived copies were
not silently substituted.

The clean vendor initializer probes `3FFFF/40000` and offers 127/254/508 KiB
profiles. That differs from the initializer on the captured floppy. To
preserve the requested behavior, generation restores the capture's exact
27-byte sizing tables at `1C57–1C71` and 187-byte 8088 initializer/handler at
`1C98–1D52`. Their addresses and shared transfer interface match the generated
system. Only those two spans change after CONFIG. The donor is stored as
`assets/boot/coboard-driver.bin`; it contains no unrelated floppy data.

| Artifact | SHA-256 |
| --- | --- |
| CONFIG output before restoring recovered driver | `b40393849fac889bac5ac0c8d7864ae2021ae1e04f111941b41981995af50f7c` |
| Recovered 214-byte donor | `81b4605b10bbd06d9dc4ae0c79b71ecaf011081830fc75bed7509787d075b2d8` |
| Combined boot tracks | `401a12434c78dcb766e2de342dc8c6503b622827989cf21f2ec027076236bc54` |

Reproduce and compare without changing the bundled tracks:

```console
python3 src/maintenance/generate_coboard.py --emulator /path/to/p2000c_cli --ipl /path/to/IPLDUMP.BIN --check
```

The script uses temporary disks and checks hashes before publishing anything.
Ordinary builds need neither the emulator nor its IPL ROM. The configuration
editor permits changing only the confirmed CCP autostart buffer in this system;
all other bytes must match the reviewed combined image.

Validation covers CP/M startup, G: browsing, all four SASI mappings,
a 126 KiB binary copy to G: and back across a CP/M warm boot on simulated
256/512 KiB boards, and byte-for-byte regeneration. On 2026-09-13, the RAM disk
was confirmed working on physical hardware.
File retention across physical RESET remains unconfirmed; the reports did
not specify capacity or file-comparison results.
