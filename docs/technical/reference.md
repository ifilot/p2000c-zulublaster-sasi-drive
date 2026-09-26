# Hardware and original SD-card reference

[Documentation](../README.md) · [Installation](../../README.md)

The supplied files at `/mnt/d/tmp/zulublaster` were inspected on 2026-09-13.
The original images were not modified. The required drive map is A: SASI
boot, B:/C: floppies, D:/E:/F: SASI. Emulator tests with distinct partition
markers confirmed A=HD0 low, D=HD0 high, E=HD1 low, F=HD1 high.

Both original images use the 8,192-byte system preserved at
`assets/boot/hdboot-split.trk`. Their logs describe IDs 0 and 1, 256-byte
sectors, FAT32 media and termination enabled. The build retains the active
ZuluBlaster settings in `assets/zuluscsi.ini`, with normal INI line endings.
The old single-filesystem boot input was retired because it used a different
drive configuration.

## Mounting photographs

The [bracket STL](../../assets/hardware/zulublasterbracket.stl) has a bounding
box of 100 × 4 × 138 coordinate units; STL does not encode units. The tested
print uses PLA, 15% infill, a 0.4 mm nozzle and 0.2 mm layers. Use four M3 ×
8 mm screws; 6 mm screws also fit. The photographs document placement and
routing. The installation guide gives the build order; neither document is an
electrical pinout.

| Photograph | What it shows |
| --- | --- |
| [Board and bracket](../photos/IMG20260913081231.jpg) | Board mounting points |
| [Installed bracket](../photos/IMG20260913082705.jpg) | Position and cable ties |
| [Chassis supports](../photos/IMG20260913081424.jpg) | Clearance beneath the crossbar |
| [Cable routing](../photos/IMG20260913081442.jpg) | Ribbon and power routing |
| [Rear connection](../photos/IMG20260913081307.jpg) | Ribbon at the opening marked 50 |
| [Wiring close-up](../photos/IMG20260913081238.jpg) | Reference red/black connections |
| [Wider wiring view](../photos/IMG20260913081248.jpg) | Wiring context |

The returned CoPower floppy capture and its hashes are recorded separately
in the [RAM driver analysis](coboard.md).
