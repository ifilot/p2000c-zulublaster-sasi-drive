# Headless test emulator

[Development](development.md)

`tools/emulator/` contains only the native machine core, CPU interpreters,
terminal model and command-line runner. It executes the actual Z80 CP/M code
and 8088 CoPower driver with SASI and floppy images. There is no Qt, audio,
window, network download or external checkout dependency. `make run` remains
the separate graphical preview.

Install CMake, a C/C++20 compiler, `z80asm` and pytest:

```console
make emulator
make test-emulator
```

The first command builds `build/emulator/p2000c-mini` in Release mode. Tests
also build it automatically, once per session; subsequent builds are incremental.
`make test` and GitHub Actions include these execution tests.

Python sends a complete scenario to one native process, keeping instruction
execution in C++. For example, after `make pro`, with `PYTHONPATH=src`:

```python
from p2000c_disk.emulator import emulator_command, run_scenario

command = emulator_command()
state = run_scenario([
    "--hard-disk-0", "dist/pro/HD0_256.hda",
    "--hard-disk-1", "dist/pro/HD1_256.hda",
    "--fast-storage",
    "--wait-for", "A>", "--send", "DIR\\r",
], command=command)
print("\n".join(state["screen"]))
```

The result includes the 80×24 screen, cursor, CPU state, graphics state and
optional memory dumps. Failed waits raise `CalledProcessError`; its `stdout`
contains the final diagnostic JSON. Each wait has a cycle limit and Python
also enforces a wall-clock timeout. See the executable's `--help` for actions.

Images are copied to temporary files by default. Only `--write-through`
modifies supplied images; tests use it exclusively with disposable media.
`--copower-ram 256` and `--copower-ram 512` select physical board capacity.
The former tests the original driver's 127 KiB formatted RAM disk; the latter
tests its 508 KiB profile. No source patching or separate board build is needed.

`P2000C_IPL` can override the bundled IPL and `P2000C_EMULATOR` can select a
compatible external runner. The full suite requires `--copower-ram` support.
This is a functional test model, not proof of electrical behaviour or exact
hardware timing; physical P2000C testing remains the final check.

## Source and licenses

The core and CLI were copied from
[ifilot/p2000c-emulator](https://github.com/ifilot/p2000c-emulator/tree/2211223c4554a2f5266da60d7e09911fdadc0ce3),
commit `2211223c4554a2f5266da60d7e09911fdadc0ce3`.
Only `src/core`, the two CPU interpreters and `tools/p2000c_cli/p2000c_cli.cpp`
were retained. Local changes add selectable CoPower capacity and the standalone
build. The emulator is GPLv3; its license is retained in
[`tools/emulator/LICENSE`](../../tools/emulator/LICENSE). It runs as a separate
executable from the Python disk tools.

- Z80: superzazu/z80, commit `d64fe10a2274e5e40019b1086bf7d8990cbc5f23`;
  its MIT license is retained in `src/third_party/superzazu_z80/LICENSE`.
- 8088: the upstream emulator's adaptation of ghaerr/blink16, commit
  `162d824f782fe53cd6e1608b7f99cdcc09388abb`; its ISC license and attribution
  are retained in `src/third_party/blink16_8086/`.
- `firmware/IPLDUMP.BIN` is the 4 KiB historical Philips IPL dump from that
  same emulator checkout (`tools/ipldump/IPLDUMP.BIN`), not GPL source.
  SHA-256: `1b0e8be4af071659f2fcfa2b7a6d9aac893943f5e09a1537999843c82e66eee5`.
  Upstream does not establish redistribution rights for historical firmware.

Keep vendor notices when updating this subset, record the new source commit,
and rerun the execution suite. The mini emulator is a development tool and is
not copied into SD-card packages.
