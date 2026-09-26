# Builds and software selection

[Documentation](README.md) · [Installation](../README.md)

The project produces a CP/M prompt edition and an optional [program-menu edition](menu.md):

| Command | Output | Startup |
| --- | --- | --- |
| `make pro` | `dist/pro/` | CP/M prompt |
| `make menu` | `dist/menu/` | Text-mode program menu (Z88DK required) |
| `make menu-coboard` | `dist/menu-coboard/` | Program menu, G: RAM enabled |
| `make pro-coboard` | `dist/pro-coboard/` | CP/M prompt, G: RAM enabled |
| `make dev` | `dist/dev/{pro,pro-coboard,menu,menu-coboard}/` | All editions with local game working trees |

`make all` builds all four editions from the versions in `games.lock.toml`.
`make dev` instead reads the sibling `p2000c-chess`, `p2000c-minesweeper`,
`p2000c-battleship`, `p2000c-othello`, and `p2000c-tetris` repositories. It
copies and builds their current working trees, including uncommitted source
files, without changing those repositories. Set `GAME_REPOS=/path/to/parent`
when the five repositories do not share this repository’s parent directory.
Development output is kept under `dist/dev/` so it cannot replace a locked
release build accidentally. Built games are cached in `dist/dev/.game-cache/`
using a fingerprint of each working tree. A later `make dev` therefore rebuilds
only games whose tracked or untracked source files changed. Local games and the
four image variants are built with two workers by default. Set `DEV_JOBS=1` for
sequential operation or raise it on a machine with enough CPU and memory.

Every package reads its semantic version from the repository-root `VERSION`
file; the current SASI distribution is `v1.0.1`. All variants carry that version
in `manifest.json` and root `VERSION.txt`, and release ZIP filenames include it.
Releases use stable Semantic Versioning (`MAJOR.MINOR.PATCH`). Increment MAJOR
for incompatible distribution changes, MINOR for backwards-compatible features,
and PATCH for backwards-compatible fixes. The newest `CHANGELOG.md` entry must
match `VERSION`; a tag named `v` plus that version is the only event that
publishes a GitHub release. Its release notes come directly from that changelog
entry.

`make verify VARIANT=pro` checks its
hashes, disk structures and empty autostart command. Builds stage and verify a
complete package before replacing its output folder. Save edited disk images
outside `dist/`.

Install Python 3.11+, GNU Make and `z80asm`. The Python build uses only the
standard library. Override `PYTHON=/path/to/python` or
`ASSEMBLER=/path/to/z80asm` when needed.

## Preview without hardware

On Linux or WSL with WSLg, `make run` builds a disposable menu package with Z88DK and opens
it in the graphical [P2000C emulator](https://github.com/ifilot/p2000c-emulator).
It boots to the program menu. Use `make run VARIANT=pro` for the CP/M prompt.
Both preview floppy drives contain blank disposable media. Close the window to
discard all changes. Use
`make run COBOARD=1` to preview G:. The launcher finds the sibling emulator
build or `p2000c` on PATH; set `EMULATOR=/path/to/p2000c` to override it.

## Select programs

[distribution.json](../distribution.json) contains only the `drives` mapping.
Paths and glob patterns are relative to `assets/software/`. Keep the four
keys **A, D, E, F**; B: and C: are floppies and G: is optional RAM. A list
installs files in CP/M user area zero. A user-area object keeps packages with
the same 8.3 name separate.

User areas range from `"0"` to `"15"`. Include companion data and overlay
files. Duplicate names within an area, missing patterns and paths outside the
software library are rejected. `TRKDUMP.COM` on A: and `README.COM` on D:
user 0 are build-reserved.

The default layout has ASM/LOAD/DDT/ED and Kermit on A:, games on F:, and:

| User | Contents | Start command |
| ---: | --- | --- |
| 0 | README, P2EDIT and P2FILE | `README`, `P2EDIT`, `P2FILE` |
| 1 | Microsoft BASIC-80 | `MBASIC` |
| 2 | Microsoft COBOL compiler, overlays, library and linker | `COBOL` |
| 3 | SuperCalc 2 | `SC2` |

## CoPower

`make pro-coboard` uses the bundled combined SASI/CoPower boot system. Copy
the three SD files from `dist/pro-coboard/` as one set. Do not enable it on a
machine without the board. A 256 KiB board reports **G:127K-MEM**; the
emulator's 512 KiB profile reports **G:508K-MEM**. Ordinary builds have no G:.
See [diagnostics](diagnostics.md#check-the-ram-disk) and
[generation details](technical/coboard.md#combined-sasi-boot-system).
