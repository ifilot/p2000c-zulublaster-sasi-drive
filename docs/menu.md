# P2000C program menu

[Documentation](README.md)

The menu is a native CP/M 2.2 application written in C and compiled with
Z88DK. It uses the P2000C's 80-column, 24-line character terminal, with a
Dutch interface, a `P2000C NAVIGATOR v1.0.1` title bar and a `Home Computer Museum | SASI-distro v1.0.1` footer,
inverse selection bar, DOS-style cascading category windows, help and a dim
moving screensaver. Navigator itself never enters graphics mode; a launched
game may do so.

## Build and boot

Install [Z88DK](https://github.com/z88dk/z88dk) with its classic CP/M libraries,
plus this project's usual Python, Make and `z80asm` dependencies:

```console
make menu ZCC=/path/to/z88dk/bin/zcc
make verify VARIANT=menu
make run ZCC=/path/to/z88dk/bin/zcc
```

If `zcc` is on PATH or installed under `~/z88dk/bin/` or
`~/z88dk/z88dk/bin/`, omit `ZCC`. `make run` defaults to the menu edition;
`make run VARIANT=pro` previews the CP/M prompt. The builder adds sibling executables to
PATH and finds `lib/config` in a standard Z88DK installation. An explicitly
set `ZCCCFG` takes precedence. The actual compilation is:

```console
zcc +cpm -O2 -m -create-app -pragma-define:CRT_ENABLE_COMMANDLINE=0 \
    src/menu/menu.c src/menu/platform.asm -o MENU
```

Copy `HD0_256.hda`, `HD1_256.hda` and `zuluscsi.ini` from `dist/menu/` to the
SD card as a set.
`make menu-coboard` produces `dist/menu-coboard/` for a machine with a
CoPower board. The Pro edition and its release archives still boot to the
CP/M prompt; the menu edition is an additional local build.

For just the program and compiled menu data:

```console
make menu-com ZCC=/path/to/z88dk/bin/zcc
```

This produces `dist/tools/MENU.COM` and `MENU.DAT`. Install both on A: in
user area 0. From CP/M, enter `USER 0` and then `A:MENU`. The compiled data is
always read from A: user 0, including when starting from another drive.
The menu-edition disk marks `MENU.DAT` as a CP/M System file, so ordinary
`DIR` does not show it; Navigator can still read it normally.
Use the menu edition for controlled automatic startup. Its guarded warm-boot
switch distinguishes a program returning to Navigator from **Q** exiting to CP/M.

## Using the menu

- **Up/Down** or **K/J** selects an item in the active window. The physical
  P2000C Ctrl-S/D/E/X codes and the emulator cursor codes are both accepted.
- **Right** or **RETURN** enters the selected category's program window.
- **Left** returns to the category window.
- In the program window, **RETURN** starts the selected program.
- **H** or **?** opens help; any key returns to the menu.
- **S** starts the screensaver immediately. Any key wakes it; that key is consumed.
- **R** reloads the configuration.
- **Q**, **Escape** or **Ctrl-C** asks for confirmation before returning to the
  CP/M prompt. Answer **J** to confirm or **N** to remain in Navigator.

After an application exits through the normal CP/M warm boot, Navigator starts
again automatically. Choose **Q** and confirm to return deliberately to the
CP/M prompt. Navigator does not remain resident and cannot protect the screen
while another application is running.

## Editing the menu

Edit `src/menu/menu.toml` on the modern build system. `make menu` validates it
and compiles it to the compact `MENU.DAT` consumed by the P2000C. Do not edit
`MENU.DAT` by hand; it is versioned and protected by a CRC so incomplete or
corrupt updates are rejected cleanly.

```toml
[menu]
title = "Welcome to your Philips P2000C {version}"
footer = "Home Computer Museum | SASI-distro {version}"
screensaver_seconds = 120

[[categories]]
label = "Office"
description = "Writing, spreadsheets and other productivity programs."

[[categories.programs]]
label = "SuperCalc"
drive = "D"
user = 3
command = "SC2"
arguments = ""
description = "Create spreadsheets and calculations."

[[categories]]
label = "Games"
description = "Classic games and interactive fiction."

[[categories.programs]]
label = "Zork I"
drive = "F"
user = 0
command = "ZORK1"
description = "Explore the Great Underground Empire."
```

`{version}` in `menu.title` or `menu.footer` expands to the canonical distro version from the repository-root `VERSION` file. Descriptions may use TOML multiline strings. The compiler folds whitespace so
they wrap cleanly over the three description lines. `arguments` and
`description` may be omitted when empty. All displayed text must be printable
ASCII because it is rendered by the P2000C character ROM.

| Field | Limit / meaning |
| --- | --- |
| Category label | 1–24 characters |
| Program label | 1–24 characters |
| Drive | A–G; use only drives actually installed and accessible |
| User | 0–15; selected before opening the program and its data |
| Command | 1–8 letters, digits, `_`, `-`, `$`; omit `.COM` |
| Arguments | Up to 100 characters; uppercased like a CP/M command line |
| Description | Up to 200 characters |

There can be eight categories, 32 programs in total and up to 14 programs in
one category. A title and footer may each contain up to 48 characters.
`screensaver_seconds` accepts 5–3600 approximate seconds; `0` disables automatic
activation.

During a distribution build, every menu command is checked against the files
installed in its drive and user area. Unknown TOML keys, invalid limits and
missing COM files stop the host build with a precise error. At runtime,
Navigator checks the format version, declared lengths and CRC before showing
anything from `MENU.DAT`. A missing or damaged file still permits help, screen
rest and a confirmed exit to CP/M.

Entries launch COM files, not CCP commands such as `DIR`, `USER` or `SUBMIT`
scripts. Arguments support the normal command tail and the first two default
FCBs, including drive prefixes and `*`/`?` wildcards. There is no shell quoting
or redirection. Companion data and overlays must be installed in the target
program's drive/user area. Changing `distribution.json` does not generate new
menu entries automatically; keep the two configurations in sync.

The default beginner-facing menu omits the file manager, Kermit transfer,
menu-configuration shortcut and floppy-track capture utility to prevent
accidental storage or configuration changes. Their binaries remain available
to experienced users from the CP/M prompt.

The **Microsoft BASIC** entry launches `D:` user 1, command `MBASIC`. The
bundled binary is Microsoft BASIC-80 5.21 imported unchanged from the sibling
`p2000m-cpm` project. On the P2000C emulator it starts from SASI, executes an
interactive calculation and a saved BASIC program, and returns to CP/M with
`SYSTEM`. The previous MBASIC binary and the WordStar deployment were removed
after both failed on physical P2000C hardware.
P2FILE probes floppy drives; insert readable CP/M disks in B: and C: before
using it. The editor, SuperCalc, Kermit, Zork, Zeeslag and Tetris applications
were smoke-tested.

## Memory and terminal details

`menu.c` contains the UI, binary data reader, saver and launch preparation.
`platform.asm` supplies a short calibrated delay and the final program-load
trampoline, where returning to C after overwriting the menu is impossible.
The application is around 27 KiB, below the requested 32 KiB budget.

Before loading, the menu checks the COM's record count against the normal
CP/M 2.2 CCP boundary. The loader and its private FCB are copied into the
soon-to-be-discarded CCP workspace, 512 bytes below the BDOS entry. They load
the new COM at 0100h, replacing the menu; default FCBs are at 005Ch/006Ch,
the command tail at 0080h, and DMA is restored to 0080h. Entry C contains the
default drive and the stack has a zero return address for warm boot.
After transfer, the application can use the former menu and loader memory.
The loader does not reduce the normal COM loading limit or change BDOS's
reported memory boundary. A read failure during replacement prints `!` and
warm-boots rather than executing a partial program.

The menu edition also adjusts the bundled BIOS warm-reload continuation. One
seven-byte helper clears the reloaded startup-command length, allowing **Q** to
reach the prompt. A second helper selects A: user 0 while retaining `A:MENU`.
Navigator selects that helper immediately before replacing itself with an
application, so the next warm boot executes the menu command regardless of the
application's drive or user area. When Navigator starts again it selects the
prompt helper. Only the three-byte BIOS jump changes in RAM; no menu code
remains resident and applications retain the complete transient program area.
The builder guards the exact instruction sequence. Separate configuration
profiles preserve both helpers when editing startup settings (maximum 55
characters for this edition).

Terminal output uses Philips ESC Y cursor positioning, ESC 0 attributes,
ESC c/C cursor visibility, and form feed. The window borders use the native
P2000C table glyphs at A9h, AAh, B9h, BAh, D0h and FAh; the program never enters
graphics mode. Navigation repaints only the previous and new selection rows,
which avoids visible attribute trails on the serial terminal. The saver erases
and moves its dim label approximately once
per second, keeping the rest of the screen blank. CP/M 2.2 has no standard
clock; timing uses a calibrated 4 MHz delay plus BDOS/interrupt overhead and
will vary on accelerated emulators. It reduces static-screen exposure;
it cannot guarantee against CRT ageing or burn-in.

## Validation

```console
clang-format --dry-run --Werror src/menu/menu.c
ZCC=/path/to/z88dk/bin/zcc make test
```

`src/menu/.clang-format` keeps the C source on the Google style baseline with
an 80-column limit. `tests/test_menu.py` compiles the real COM and boots it in the bundled P2000C
emulator. Tests cover native table glyphs, cascading category navigation,
help, cold/warm startup, a real application, a 48 KiB replacement program,
drive/user selection, command tails, default FCBs, malformed configuration,
missing programs, and screensaver movement/wake-up. Tests skip when Z88DK is
unavailable. Physical P2000C keyboard, CRT appearance and timing still need a
hardware check.
