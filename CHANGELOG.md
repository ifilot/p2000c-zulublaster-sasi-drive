# Changelog

All notable changes to the P2000C SASI Distribution are recorded here. The
project uses stable [Semantic Versioning](https://semver.org/spec/v2.0.0.html):
MAJOR for incompatible distribution changes, MINOR for backwards-compatible
features, and PATCH for backwards-compatible fixes.

## [Unreleased]

## [1.2.2] - 2026-10-01

### Changed

- Sorted the games in the Navigator menu alphabetically.
- Removed the on-screen navigation and shortcut buttons from the browser emulator.
- Relicensed the project-owned code from MIT to GNU GPL v3 or later.
- Made source-built games use their locked build date even when an upstream
  Makefile assigns its own date.
- Replaced the immediate-exit Programmagids with a Dutch, multi-page CP/M guide
  under Documentatie; its small reader loads page text from a separate disk
  file. Microsoft BASIC now has its own Programmeren category.

## [1.2.1] - 2026-09-27

### Added

- Kakuro v1.0.0, with 95 number-crossword puzzles, to drive F: and the
  Navigator Games menu.

## [1.2.0] - 2026-09-27

### Added

- A neon-green, CRT-styled browser version of the complete P2000C emulator,
  booting the same Navigator SASI images as the physical machine.
- Automated GitHub Pages builds and deployment from the `master` branch.

### Changed

- The browser emulator uses WebAssembly for the Z80, terminal and SASI hardware
  models, with native keyboard controls, graphics, and the exact P2000C 8×12
  character generator rendered as a continuous CRT raster.
- The website now opens directly on the emulator and expands every native
  display dot into an exact 2×2 pixel block at a 1280×576 desktop canvas.
- The browser interface defaults to Dutch and provides a persistent NL/EN
  switch for all page copy, controls, status messages and accessibility labels.
- GitHub Pages ships the SASI disk images as gzip streams which the browser
  expands before mounting, reducing their combined transfer by roughly 97%.
- Navigator now starts through a 189-byte `MENU.COM` launcher which immediately
  displays `Inladen menu...`, then loads the hidden `MENU.BIN` application.
  Omitting its zero-filled BSS from disk reduces the application image from
  roughly 25 KiB to 12 KiB without changing its initialized memory layout.
- Navigator's normal title and footer no longer repeat the version or
  `SASI-distro` label. Help now identifies distribution v1.2.0, the GitHub
  repository and compilation date, and describes **S** as loading the
  screensaver. The **R** configuration-reload shortcut has been removed.


### Fixed

- Local `make site` builds pin their Z88DK and Emscripten toolchains, and
  consume the hash-verified Schaken release assets instead of a non-reproducing
  source rebuild.
- Re-locked the source-built Tetris binary to the repository pinned Z88DK
  digest so clean builds reproduce it.

## [1.0.1] - 2026-09-26

### Added

- `make dev` builds all four image variants from the current local game working
  trees, with source-fingerprinted caching and configurable parallel workers.

### Changed

- Updated Schaken to v1.1.0, Mijnenveger to v1.0.1, and Zeeslag to v1.0.2.
- Refreshed every external-game lock against the newest tagged upstream release;
  Othello remains at v1.0.1 and Tetris remains at v1.0.0.

### Fixed

- Development builds recover build locks left behind by interrupted processes,
  while continuing to reject concurrent builds owned by a live process.
- Programs launched from Navigator return automatically to Navigator through a
  temporary, guarded warm-boot switch; confirmed **Q** exits still reach CP/M.

## [1.0.0] - 2026-09-26

### Added

- Bootable SASI distributions for the standard P2000C and the CoPower RAM-board
  configuration, with both CP/M-prompt and P2000C Navigator editions.
- A Dutch text-mode Navigator with categorized menus, program descriptions,
  launch confirmation, quit confirmation, hardware-compatible cursor keys, and
  a screen-safe animated screensaver.
- Immutable external-game selection for Schaken, Mijnenveger, Zeeslag, Othello,
  and Tetris, including source or release hashes and verified output hashes.
- Versioned ZIP packages, manifests, standalone recovery tools, and SHA-256
  checksums suitable for direct SD-card deployment.
- Automated CP/M, menu, disk-image, CoPower, and emulator validation.

### Changed

- Releases are created only by `vMAJOR.MINOR.PATCH` tags whose value matches the
  repository `VERSION` file and newest changelog entry.
- Source-built game locks match clean builds with the pinned Z88DK image;
  Schaken also uses its current-Z88DK memory-arena fix.
- The P2000M MBASIC binary replaces the incompatible earlier copy.

### Removed

- WordStar, because the available installation expects an unavailable floppy
  drive and does not operate reliably from the SASI disk.
- Locally copied game binaries; release builds now obtain their pinned versions
  from their upstream repositories.
