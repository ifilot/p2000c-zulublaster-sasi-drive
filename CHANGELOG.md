# Changelog

All notable changes to the P2000C SASI Distribution are recorded here. The
project uses stable [Semantic Versioning](https://semver.org/spec/v2.0.0.html):
MAJOR for incompatible distribution changes, MINOR for backwards-compatible
features, and PATCH for backwards-compatible fixes.

## [Unreleased]

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
