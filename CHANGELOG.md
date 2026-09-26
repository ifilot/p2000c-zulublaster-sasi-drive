# Changelog

All notable changes to the P2000C SASI Distribution are recorded here. The
project uses stable [Semantic Versioning](https://semver.org/spec/v2.0.0.html):
MAJOR for incompatible distribution changes, MINOR for backwards-compatible
features, and PATCH for backwards-compatible fixes.

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
- The P2000M MBASIC binary replaces the incompatible earlier copy.

### Removed

- WordStar, because the available installation expects an unavailable floppy
  drive and does not operate reliably from the SASI disk.
- Locally copied game binaries; release builds now obtain their pinned versions
  from their upstream repositories.
