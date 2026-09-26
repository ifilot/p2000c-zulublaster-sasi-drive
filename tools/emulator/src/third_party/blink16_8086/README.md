# blink16 8086 core

This directory contains an instance-safe embedding of the 8086 interpreter
from the `blink16` branch of Greg Haerr's blink16 project:

- Upstream: <https://github.com/ghaerr/blink16>
- Imported commit: `162d824f782fe53cd6e1608b7f99cdcc09388abb`
- License: ISC; see `LICENSE`

The upstream source header credits the original emulator to Andrew Jenner's
reenigne project, DOS enhancements to TK Chia, and ELKS support plus a
substantial rewrite and disassembler work to Greg Haerr. The pinned blink16
repository supplies the included ISC notice, with copyright 2022 Justine
Alexandra Roberts Tunney.

The P2000C adaptation removes executable-loader and debugger coupling, routes
memory and I/O through callbacks, models reset/HLT/external interrupts, and
wraps physical addresses to the 8088's 20-bit bus. The instruction decoder and
execution logic remain derived from upstream `blink16/8086.c`.
