# Development

[Documentation](../README.md)

The repository produces CP/M prompt and program-menu SD-card editions. The optional
[menu](../menu.md) is C compiled with Z88DK, with a small Z80 loader boundary. Its main folders are:

| Folder | Purpose |
| --- | --- |
| `assets/` | Boot tracks, ZuluBlaster configuration, bracket and CP/M software |
| `src/` | Python build/disk engine, assembly programs and maintenance tools |
| `tests/` | Filesystem, build and emulator tests |
| `tools/emulator/` | Small headless C++ emulator and test firmware |
| `docs/` | All guides, photos and technical evidence |
| `dist/` | Generated packages; ignored by Git |

`distribution.json` is the software-selection input. The Makefile invokes
`python -m p2000c_disk.distribution` with `PYTHONPATH=src`. `payload.py` validates
inputs; `assembly.py` builds the Z80 programs; `distribution.py` stages,
populates, verifies and publishes packages. The remaining Python modules
implement the disk format and copy-on-write filesystem operations.

The disk engine is retained for builds, recovery and regression testing:

```console
PYTHONPATH=src python3 -m p2000c_disk --help
PYTHONPATH=src python3 -m p2000c_disk verify /path/to/HD0_256.hda
PYTHONPATH=src python3 -m p2000c_disk ls /path/to/HD0_256.hda --partition low
```

Use `get`/`put` for transfers and `extract-system` for reserved tracks; consult
each subcommand's `--help`. `src/maintenance/floppy_extract.py` reads captured
floppy formats; `diskdefs` describes them for external CP/M tools.

## Validation

Install pytest, CMake, a C/C++20 compiler and `z80asm`, then run `make test`.
The bundled [headless emulator](emulator.md) compiles automatically and executes
the CP/M, track-capture and CoPower tests. Use `make test-emulator`
for just those tests, or `make emulator` to build the core alone. No Qt,
external emulator checkout or download is needed. Optional reference-image
tests still skip when their external fixtures are absent.

## Cleanup decisions

The old standalone ordered/split experimental build commands and single-drive
boot input were retired. The unused catalog generator and duplicate top-level
guides were removed. MS-DOS and UCSD software were removed from the working
collection because these packages target CP/M; historical tracked files remain
recoverable from Git. The CP/M library and recovery tools remain available for
future program selections. The original 8 KiB CoPower capture is preserved in
`docs/technical/evidence/` alongside its analysis. Optional reference disk
images for tests belong under ignored `tests/fixtures/references/`; they are
not included in generated packages. Tests needing absent images skip as before.
