# CP/M software collection

[Documentation](../README.md)

## Browser character generator

The website's 2,265-byte `web/p2000c-font.png` is copied unchanged from
`p2000c-emulator/assets/font/P2000C font mini.png`. Its SHA-256 is
`daac2776c03a24beac228f0ed0f7ff04ee0fe44dce06d4fafc4e52bb6a9cb87d`.
The browser decodes the same 192×192 character sheet, 12-pixel sheet pitch,
and 8×12 glyph cells as the native emulator. This historical machine/reference
asset is not relicensed by the project's GPL license.


The collection is organized under `assets/software/cpm/` by software category. The `assets/software/core/`
directory contains the Philips CP/M utilities used by the reproducible disk
builds.

The locally developed utilities are sourced from the sibling
`p2000c-emulator` checkout:

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| `core/P2EDIT.COM` | 6,528 | `48c7d3c0b8c499c036162aced2ea305011dbe15d4b90c5fcadc8b38541c3c6c3` |
| `core/P2FILE.COM` | 4,608 | `17f2eae22894eb35c59953e6f2901973d491d838ca5a92f731608254e6875343` |

Zork I, II and III are available at `cpm/games/zork1/`,
`cpm/games/zork2/` and `cpm/games/zork3/`. Each game requires its matching
`ZORKn.COM` and `ZORKn.DAT` files.

Zork II and III were copied unchanged from
[`ifilot/p2000m-cpm`, commit `b6625d1633bc8731df9c5facea52ae4d02f08d94`](https://github.com/ifilot/p2000m-cpm/tree/b6625d1633bc8731df9c5facea52ae4d02f08d94/assets/zork).
The upstream notes credit Infocom and trace these files to
[`ifilot/p2000c-cpm-transfer`, commit `bb0aa2e2a9228aba0467ead7cc86ee6a4df10411`](https://github.com/ifilot/p2000c-cpm-transfer/tree/bb0aa2e2a9228aba0467ead7cc86ee6a4df10411/programs/games/zork),
without documenting an earlier binary source or license grant.

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| `cpm/games/zork2/ZORK2.COM` | 8,704 | `44047d3475a10f75a3c17837c950234543ff7eb9b1b5350f8a2848a05db39e8f` |
| `cpm/games/zork2/ZORK2.DAT` | 90,112 | `9ed69ceb4c8d2c419fd35ee966d5106a52f4f0cd7bbe7df3bcffd3d966ec24f3` |
| `cpm/games/zork3/ZORK3.COM` | 8,704 | `953a821aa39bc86af0d58d3c9cd09012f8bd4336dc70316e17bb7893cbad9909` |
| `cpm/games/zork3/ZORK3.DAT` | 82,944 | `01b84e5a3f63f84ec965f7bdd617ce01e2652f05044a1ec9cb040ab6ea2edcd9` |

To include all three games on F:, set its selection in `distribution.json` to:

```json
"F": ["cpm/games/zork1/*", "cpm/games/zork2/*", "cpm/games/zork3/*"]
```

At the F: prompt, run `ZORK1`, `ZORK2` or `ZORK3`. The default selection
includes all three. Startup with companion files is checked in emulation; this
is not a complete playthrough.
The expanded games selection has not yet been verified on P2000C hardware.

The binaries retain their original authorship and notices. Keeping software
in this historical library does not establish redistribution rights or prove
that it works. The default selection is controlled by `distribution.json`;
unselected files are not copied to the SD images. Do not treat the Python
package's license metadata as a license for third-party binaries.

## Microsoft BASIC-80 5.21

The default D: user 1 installation uses the 24,320-byte `MBASIC.COM` imported
unchanged from the sibling `p2000m-cpm` project. That project traces it to
Deramp's archived `MBASIC5.COM`. Its startup identifies BASIC-80 Rev. 5.21 for
CP/M, Microsoft 1977-1981, created July 28, 1981. SHA-256:
`29d957fc6899c24f6296a1662a27eca545d85ee3f7d70d2794c9d045d92ff157`.

The binary starts from the P2000C SASI drive in emulation, evaluates an
interactive calculation, runs a BASIC source file and returns to CP/M with
`SYSTEM`. The previous 23,424-byte MBASIC copy hung before displaying its
banner on both SASI and floppy media. The replacement still requires final
confirmation on physical P2000C hardware.

## Super-Chess 2000

The former archived CHESS.COM returned immediately to the prompt. It was
replaced with the 30,720-byte copy recovered through CP/M PIP from the sibling
emulator's `assets/images/cpm/chess.flp`; this is also byte-identical to its
`assets/media/files/chess/CHESS.COM`. SHA-256:
`c3ca83da047c406cd586e76e801ddd28a9be178db730bca6435f3f423f9ed9d6`.
The binary identifies Super-Chess 2000, Telecom Labor, Vienna, copyright 1984.
It uses the P2000C graphics display. Its startup and new-game board are checked
in emulation. It is included on F: as **Chess**, distinct from the newer **Schaken** game.

Additional archived candidates (Cijfers, Jackpot, Forest, K-Race,
Pirates, Solo, Woord, Galaxy, Trader, Stars and Slang) did not produce usable
startup screens in the SASI emulator probe. Trader requests BRUN.COM; several
others hang or return to the prompt. These copies remain outside the defaults.

## Locked external games

The games maintained in their own repositories are not copied into this
repository. [`games.lock.toml`](../../games.lock.toml) records the declared
upstream version and selects an exact immutable commit for this distribution.
For Tetris it also pins a GitHub source-archive SHA-256, a reproducible build
date, command, and the hash of the installed result. Schaken, Mijnenveger,
Zeeslag, Othello and Kakuro use hash-verified official release assets. The build
downloads the selected immutable sources or assets and rejects files with
a different hash.

| Program | Repository | Selected release | Installed file(s) |
| --- | --- | --- | --- |
| Schaken | [p2000c-chess](https://github.com/ifilot/p2000c-chess) | `v1.1.0` (`44bda2b5b5d119f4a7d20eb37257c0fd954a295d`) | `SCHAKEN.COM`, `SCHAKEN.GFX` |
| Mijnenveger | [p2000c-minesweeper](https://github.com/ifilot/p2000c-minesweeper) | `v1.0.1` (`177b0d40fe84c9da1dc95d16535215b65ef5fe59`) | `MINES.COM` |
| Zeeslag | [p2000c-battleship](https://github.com/ifilot/p2000c-battleship) | `v1.0.2` (`49b70781c2d0c3b13befdf1665ddcd228bed2afe`) | `ZEESLAG.COM` |
| Othello | [p2000c-othello](https://github.com/ifilot/p2000c-othello) | `v1.0.1` (`9a498d3483c7ba20ce1283d524d2c6e15bf0a219`) | `OTHELLO.COM` |
| Tetris | [p2000c-tetris](https://github.com/ifilot/p2000c-tetris) | `v1.0.0` (`619d73057e08e42403d52ca4f7c7e0f74e4b1e25`) | `TETRIS.COM` |
| Kakuro | [p2000c-kakuro](https://github.com/ifilot/p2000c-kakuro) | `v1.0.1` (`05c3d68e806671fcda3bddaed0b42ccf5618ff0e`) | `KAKURO.COM` |

Schaken, Mijnenveger, Zeeslag, Othello and Kakuro are pinned to their official
release assets. The first four source builds do not reproduce the deployed
binaries with the pinned Z88DK Docker image, so the release assets are the
reproducible choice. `DIAG.COM` is not part of the distro.

The first build stores verified artifacts in
`~/.cache/p2000c-disk-tool/games/<lock-hash>/`; set `P2000C_GAME_CACHE` to use
a different cache location. All games are installed on F: user 0. The source
builds invoke the upstream `make build` command and therefore require Docker
with the `z88dk/z88dk` image available. Changing a game requires updating the
lock data and deliberately releasing a new distro version.

Zeeslag, Mijnenveger, Schaken and Kakuro use the P2000C 512x252 graphics plane
during play. Tetris remains entirely in the 80x24 character display.

## Ladder and Pac-Man

Working Ladder and Pac-Man copies were recovered from the local sibling checkout
`p2000c-cpm-transfer/programs/games/misc/`. The alternate Jackpot copy still
shows corrupted introductory text and remains excluded.

| Supplied file | SHA-256 |
| --- | --- |
| `ladder/LADDER.COM` | `9911533351803c2a3eb6afd51b3a3d36d21322450610ba92e90a9d7960d95a12` |
| `ladder/LADDER.DAT` | `fa7af5be86b93e0e0e4baa018157dd33364e60b4429f55fbf6f0f5bbe25a6b3b` |
| `pacman/PAC.COM` | `e497adf99b85b5788434d7ff843b25aeb5adfbf2469617e08e7e1ed6ea738690` |

LADDER.DAT retains the P2000C terminal profile; only offsets E0h–E3h (down,
left, right, up) changed from `.<-Y` to `SADW`, giving visitors W/A/S/D
controls. The original file's hash is
`01e5df7fb8f0dd38c7673e3fa9c1b9bf7b9fb45aa2127b95b1ca2a35c93a1aaa`.
The title screen confirms these controls. Space jumps, P starts and E exits
from the title screen. The broken archived LADCONF is not deployed.

## Kermit

`communications/kermit/KERMIT.COM` is copied unchanged from the local checkout
of [ifilot/p2000c-kermit](https://github.com/ifilot/p2000c-kermit/tree/82a03ac15008decd2b0007efa23b7071a277d585/programs/utils),
commit `82a03ac15008decd2b0007efa23b7071a277d585`. SHA-256:
`6264dea27fa8fdcf87cf49cd87ce6819a30b015215501bc9839251972fdf13fb`.
The distribution includes it on A: for serial file transfers. At the CP/M
prompt, run `KERMIT`. See the upstream
[transfer guide](https://github.com/ifilot/p2000c-kermit#procedure) for cabling
and transfer commands. Serial transfers still require the appropriate hardware.

## SuperCalc 2

The default D: user 3 installation uses SuperCalc 2 1.00 files from the
reproducible import in the sibling `p2000m-cpm` project. That import traces the
files to Deramp's original Burcon CP/M `supercalc2.dsk` image (SHA-256
`b08ab3f8db3ee389061250fa1d781ed5b4d4824b3bfa5ff0345bbb423d396b52`).
The previous local SuperCalc archive returned immediately to CP/M and its core
files did not match this working set.

Only `SC2.COM`, `SC2.OVL` and `SC2.HLP` are deployed, using an explicit
allowlist in `distribution.json`. The overlay and help file are unchanged
from the P2000M import. The matching installer remains in the source archive
for maintenance, but is not needed to run the preconfigured application.
All sample worksheets and unrelated utilities are excluded. In particular,
the old `GRAFIEK.CAL` reproduces a `Protected Entry` error during loading and
contains unexpected help-text fragments, suggesting damaged contents.
No causal link to the reported SD-image boot failure has been established.

`SC2.COM` uses the installer-generated VT52 profile as its base,
with changes confined to Sorcim's terminal configuration area:

- terminal name `P2000C VT52`;
- form feed (`0Ch`) for the P2000C clear-screen operation;
- SOH (`01h`) for cursor home and `ESC k` for erase-to-end-of-screen;
- `ESC 0 50h` / `ESC 0 40h` for inverse/normal text at normal brightness;
- Ctrl-E/Ctrl-X/Ctrl-S/Ctrl-D (`05h/18h/13h/04h`) for up/down/left/right;
- Ctrl-C as the displayed command-cancellation key.

The resulting `SC2.COM` SHA-256 is
`1967497109491a0b3d7754ef132c735c541a70dc77c2cd826a2938500eca2412`.

The earlier adaptation retained VT52 `ESC p/q` for inverse video. On the
physical P2000C, `ESC p` enters the terminal's Intel HEX program loader
(Philips CP/M Reference Manual, chapter 10, page 10-5), explaining the blank
screen after Return. The emulator formerly ignored this command; it now fails
explicitly if software requests this unimplemented loader. The current profile
uses the Philips attribute commands from page 10-3. Cursor addressing remains
`ESC Y` with a 20h coordinate offset, as documented on page 10-7.
The checked
[`configure_supercalc.py`](../../src/maintenance/configure_supercalc.py)
utility reproduces it from the verified P2000M-profile executable while
rejecting an unexpected input or output hash.
Automated P2000C emulation checks startup, the clean worksheet display, all
four cursor directions, a formula yielding 42, saving and reloading a worksheet, and return
to CP/M. The physical keyboard still merits a final hardware check.
