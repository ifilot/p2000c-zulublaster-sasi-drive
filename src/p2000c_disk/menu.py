# SPDX-FileCopyrightText: 2026 P2000C SASI Distribution contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Compile the host-side TOML menu and the Z88DK CP/M executable."""
from __future__ import annotations

from datetime import date
import argparse
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import tempfile
import tomllib
from typing import Mapping, Sequence

from .assembly import ROOT, assemble_program
from .version import DISPLAY_VERSION

MAGIC = b"P2MN"
FORMAT_VERSION = 1
MAX_CATEGORIES, MAX_ITEMS, MAX_CATEGORY_ITEMS = 8, 32, 14
MAX_LABEL_LENGTH, MAX_PROGRAM_LENGTH = 24, 8
MAX_ARGUMENT_LENGTH, MAX_DESCRIPTION_LENGTH, MAX_TITLE_LENGTH = 100, 200, 48
PROGRAM_RE = re.compile(r"[A-Z0-9_$-]{1,8}\Z")
GUIDE_PAGE_SEPARATOR = "%%PAGE%%"
MAX_GUIDE_LINES = 20
MAX_GUIDE_WIDTH = 78


def crc16(data: bytes) -> int:
    """Return the CRC-16/CCITT-FALSE checksum used by Navigator."""
    crc = 0xFFFF
    for value in data:
        crc ^= value << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if crc & 0x8000 else (crc << 1) & 0xFFFF
    return crc


def compile_guide(source: Path, destination: Path) -> Path:
    """Compile readable source pages into a CP/M text file."""
    pages: list[list[str]] = [[]]
    for line_number, line in enumerate(source.read_text(encoding="utf-8").splitlines(), 1):
        if line == GUIDE_PAGE_SEPARATOR:
            if not pages[-1]:
                raise ValueError(f"empty guide page before line {line_number}")
            pages.append([])
            continue
        try:
            encoded = line.encode("ascii")
        except UnicodeEncodeError as exc:
            raise ValueError(f"guide line {line_number} must use printable ASCII") from exc
        if any(byte < 32 or byte > 126 for byte in encoded):
            raise ValueError(f"guide line {line_number} must use printable ASCII")
        if len(encoded) > MAX_GUIDE_WIDTH:
            raise ValueError(
                f"guide line {line_number} exceeds {MAX_GUIDE_WIDTH} characters"
            )
        pages[-1].append(line)
        if len(pages[-1]) > MAX_GUIDE_LINES:
            raise ValueError(
                f"guide page {len(pages)} exceeds {MAX_GUIDE_LINES} lines"
            )
    if not pages[-1]:
        raise ValueError("guide must not end with an empty page")
    payload = b"\x0c".join(
        b"\r\n".join(line.encode("ascii") for line in page) + b"\r\n"
        for page in pages
    ) + b"\x1a"
    destination.write_bytes(payload)
    return destination


def build_cpm_guide(destination: Path, assembler: str = "z80asm",
                    root: Path = ROOT) -> Path:
    """Build the small viewer and its disk-backed Dutch CP/M pages."""
    destination.mkdir(parents=True, exist_ok=True)
    program = destination / "CPMHELP.COM"
    assemble_program(root / "src/asm/cpmhelp.asm", program, assembler,
                     maximum_size=0x1000)
    compile_guide(root / "src/menu/cpm-guide.txt", destination / "CPMHELP.TXT")
    return program


def _table(value: object, context: str) -> dict:
    """Require a TOML table and return it."""
    if not isinstance(value, dict):
        raise ValueError(f"{context} must be a TOML table")
    return value


def _only_keys(table: Mapping[str, object], allowed: set[str], context: str) -> None:
    """Reject misspelled or unsupported keys."""
    unknown = sorted(set(table) - allowed)
    if unknown:
        raise ValueError(f"unknown key in {context}: {unknown[0]}")


def _expand_version(value: object) -> object:
    """Expand the canonical distro version in menu presentation strings."""
    return value.replace("{version}", DISPLAY_VERSION) if isinstance(value, str) else value


def _text(value: object, context: str, maximum: int, *, empty: bool = False,
          normalize: bool = False) -> str:
    """Validate a printable ASCII TOML string."""
    if not isinstance(value, str):
        raise ValueError(f"{context} must be a string")
    value = " ".join(value.split()) if normalize else value.strip()
    if (not empty and not value) or len(value) > maximum:
        qualifier = f"1-{maximum}" if not empty else f"at most {maximum}"
        raise ValueError(f"{context} must contain {qualifier} characters")
    try:
        encoded = value.encode("ascii")
    except UnicodeEncodeError as exc:
        raise ValueError(f"{context} must use printable ASCII") from exc
    if any(byte < 32 or byte > 126 for byte in encoded):
        raise ValueError(f"{context} must use printable ASCII")
    return value


def _available_set(payload: Mapping[str, Mapping[int, Sequence[Path]]] | None):
    """Convert distribution contents into drive, user and filename keys."""
    if payload is None:
        return None
    return {(drive.upper(), int(user), path.name.upper())
            for drive, users in payload.items() for user, paths in users.items()
            for path in paths}


def compile_menu_data(source: Path, destination: Path,
                      available_programs: Mapping[str, Mapping[int, Sequence[Path]]] | None = None) -> Path:
    """Validate TOML and compile it into Navigator's versioned binary format."""
    try:
        document = tomllib.loads(source.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        raise ValueError(f"invalid menu TOML: {exc}") from exc
    _only_keys(document, {"menu", "categories"}, "document")
    menu = _table(document.get("menu"), "menu")
    _only_keys(menu, {"title", "footer", "screensaver_seconds"}, "menu")
    title = _text(_expand_version(menu.get("title")), "menu.title", MAX_TITLE_LENGTH)
    footer = _text(_expand_version(menu.get("footer")), "menu.footer", MAX_TITLE_LENGTH)
    saver = menu.get("screensaver_seconds")
    if type(saver) is not int or saver < 0 or saver > 3600 or 0 < saver < 5:
        raise ValueError("menu.screensaver_seconds must be 0 or 5-3600")

    categories = document.get("categories")
    if not isinstance(categories, list) or not 1 <= len(categories) <= MAX_CATEGORIES:
        raise ValueError(f"categories must contain 1-{MAX_CATEGORIES} entries")
    available = _available_set(available_programs)
    payload = bytearray(title.encode("ascii") + footer.encode("ascii"))
    total = 0
    for category_index, raw_category in enumerate(categories, 1):
        context = f"categories[{category_index}]"
        category = _table(raw_category, context)
        _only_keys(category, {"label", "description", "programs"}, context)
        label = _text(category.get("label"), f"{context}.label", MAX_LABEL_LENGTH)
        description = _text(category.get("description", ""), f"{context}.description",
                            MAX_DESCRIPTION_LENGTH, empty=True, normalize=True)
        programs = category.get("programs")
        if not isinstance(programs, list) or not 1 <= len(programs) <= MAX_CATEGORY_ITEMS:
            raise ValueError(f"{context}.programs must contain 1-{MAX_CATEGORY_ITEMS} entries")
        total += len(programs)
        if total > MAX_ITEMS:
            raise ValueError(f"the menu may contain at most {MAX_ITEMS} programs")
        payload.extend((len(label), len(description), len(programs), 0))
        payload.extend(label.encode("ascii") + description.encode("ascii"))
        for program_index, raw_program in enumerate(programs, 1):
            pcontext = f"{context}.programs[{program_index}]"
            program = _table(raw_program, pcontext)
            _only_keys(program, {"label", "drive", "user", "command", "arguments", "description"}, pcontext)
            plabel = _text(program.get("label"), f"{pcontext}.label", MAX_LABEL_LENGTH)
            drive = _text(program.get("drive"), f"{pcontext}.drive", 1).upper()
            if drive < "A" or drive > "G":
                raise ValueError(f"{pcontext}.drive must be A-G")
            user = program.get("user")
            if type(user) is not int or not 0 <= user <= 15:
                raise ValueError(f"{pcontext}.user must be 0-15")
            command = _text(program.get("command"), f"{pcontext}.command", MAX_PROGRAM_LENGTH).upper()
            if not PROGRAM_RE.fullmatch(command):
                raise ValueError(f"{pcontext}.command is not a valid CP/M program name")
            arguments = _text(program.get("arguments", ""), f"{pcontext}.arguments",
                              MAX_ARGUMENT_LENGTH, empty=True)
            pdescription = _text(program.get("description", ""), f"{pcontext}.description",
                                 MAX_DESCRIPTION_LENGTH, empty=True, normalize=True)
            if available is not None and (drive, user, command + ".COM") not in available:
                raise ValueError(f"{pcontext} refers to missing {drive}: user {user} {command}.COM")
            payload.extend((len(plabel), len(command), len(arguments), len(pdescription),
                            ord(drive) - ord("A"), user))
            payload.extend(plabel.encode("ascii") + command.encode("ascii") +
                           arguments.encode("ascii") + pdescription.encode("ascii"))

    header = struct.pack("<4sBBBBHHHBB", MAGIC, FORMAT_VERSION, len(categories), total,
                         0, saver, len(payload), crc16(payload), len(title), len(footer))
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(header + payload)
    return destination


def _map_address(link_map: str, symbol: str) -> int:
    """Read one hexadecimal address from a Z88DK map."""
    match = re.search(
        rf"^{re.escape(symbol)}\s*=\s*\$([0-9A-Fa-f]+)\s*;",
        link_map,
        re.MULTILINE,
    )
    if match is None:
        raise ValueError(f"Z88DK map does not define {symbol}")
    return int(match.group(1), 16)


def _write_compact_application(binary: Path, link_map: Path,
                               destination: Path) -> None:
    """Omit trailing BSS bytes; the Z88DK startup clears that memory."""
    data = binary.read_bytes()
    symbols = link_map.read_text(encoding="ascii", errors="strict")
    bss_start = _map_address(symbols, "__BSS_head")
    bss_end = _map_address(symbols, "__BSS_END_tail")
    origin = 0x100
    if bss_end != origin + len(data) or not origin < bss_start <= bss_end:
        raise ValueError("Z88DK map and MENU.BIN layout disagree")
    file_end = bss_start - origin
    if any(data[file_end:]):
        raise ValueError("MENU.BIN BSS contains nonzero data and cannot be omitted")
    destination.write_bytes(data[:file_end])
    if not 0 < destination.stat().st_size <= 32768:
        raise ValueError("Z88DK did not produce a MENU.BIN between 1 and 32768 bytes")


def build_menu(destination: Path, zcc: str = "zcc", root: Path = ROOT,
               available_programs: Mapping[str, Mapping[int, Sequence[Path]]] | None = None,
               assembler: str = "z80asm") -> Path:
    """Build the MENU.COM launcher, MENU.BIN application and MENU.DAT."""
    executable = shutil.which(zcc)
    if executable is None and zcc == "zcc":
        for relative in ("z88dk/bin/zcc", "z88dk/z88dk/bin/zcc"):
            candidate = Path.home() / relative
            if candidate.is_file() and os.access(candidate, os.X_OK):
                executable = str(candidate)
                break
    if executable is None:
        raise ValueError(f"Z88DK compiler not found: {zcc}; set ZCC=/path/to/z88dk/bin/zcc")
    executable = str(Path(executable).resolve())
    environment = dict(os.environ)
    environment["PATH"] = str(Path(executable).parent) + os.pathsep + environment.get("PATH", "")
    config = Path(executable).parent.parent / "lib/config"
    if config.is_dir():
        environment.setdefault("ZCCCFG", str(config) + os.sep)
    build_date = environment.get("BUILD_DATE", date.today().isoformat())
    try:
        if date.fromisoformat(build_date).isoformat() != build_date:
            raise ValueError
    except ValueError as exc:
        raise ValueError("BUILD_DATE must use YYYY-MM-DD") from exc
    destination.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".menu-", dir=destination) as temporary:
        stage = Path(temporary).resolve()
        application = stage / "MENUAPP"
        subprocess.run([executable, "+cpm", "-O2", "-m", "-create-app",
                        "-pragma-define:CRT_ENABLE_COMMANDLINE=0",
                        f'-DNAVIGATOR_VERSION=\\"{DISPLAY_VERSION}\\"',
                        f'-DNAVIGATOR_BUILD_DATE=\\"{build_date}\\"',
                        str(root / "src/menu/menu.c"), str(root / "src/menu/platform.asm"),
                        "-o", str(application)], cwd=stage, env=environment,
                       check=True, capture_output=True, text=True)
        _write_compact_application(
            application.with_suffix(".COM"),
            application.with_suffix(".map"),
            stage / "MENU.BIN",
        )
        assemble_program(
            root / "src/menu/bootstrap.asm",
            stage / "MENU.COM",
            assembler,
            maximum_size=256,
        )
        compile_menu_data(root / "src/menu/menu.toml", stage / "MENU.DAT", available_programs)
        for name in ("MENU.COM", "MENU.BIN", "MENU.DAT"):
            os.replace(stage / name, destination / name)
        (destination / "VERSION.txt").write_text(
            f"P2000C SASI Distribution {DISPLAY_VERSION}\n", encoding="ascii"
        )
    stale = destination / "MENU.CFG"
    if stale.exists():
        stale.unlink()
    return destination / "MENU.COM"


def main() -> None:
    """Run the standalone menu builder."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "dist/tools")
    parser.add_argument("--zcc", default=os.environ.get("ZCC", "zcc"))
    parser.add_argument("--assembler", default="z80asm")
    args = parser.parse_args()
    try:
        menu = build_menu(args.output, args.zcc, assembler=args.assembler)
        guide = build_cpm_guide(args.output, args.assembler)
        print(f"Built {menu}, {guide} and {guide.with_suffix('.TXT')}")
    except subprocess.CalledProcessError as exc:
        parser.exit(1, exc.stderr or str(exc))
    except (OSError, ValueError) as exc:
        parser.exit(1, f"{exc}\n")


if __name__ == "__main__":
    main()
