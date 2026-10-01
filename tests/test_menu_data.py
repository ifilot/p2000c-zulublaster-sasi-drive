# SPDX-FileCopyrightText: 2026 P2000C SASI Distribution contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Host-side tests for the TOML to MENU.DAT compiler."""
from pathlib import Path
import struct

import pytest

from p2000c_disk.menu import (
    _write_compact_application, compile_guide, compile_menu_data, crc16,
)

VALID = '''[menu]
title = "Test menu"
footer = "Museum"
screensaver_seconds = 60
[[categories]]
label = "Tools"
description = "A useful category"
[[categories.programs]]
label = "Guide"
drive = "D"
user = 0
command = "CPMHELP"
description = "Read the guide"
'''


def compile_text(tmp_path: Path, text: str, available=None) -> bytes:
    source = tmp_path / "menu.toml"
    source.write_text(text)
    output = tmp_path / "MENU.DAT"
    compile_menu_data(source, output, available)
    return output.read_bytes()


def test_binary_header_and_checksum(tmp_path):
    data = compile_text(tmp_path, VALID)
    values = struct.unpack("<4sBBBBHHHBB", data[:16])
    magic, version, categories, programs, flags, saver, length, checksum, title, footer = values
    assert (magic, version, categories, programs, flags, saver) == (b"P2MN", 1, 1, 1, 0, 60)
    assert length == len(data) - 16
    assert checksum == crc16(data[16:])
    assert data[16:16 + title] == b"Test menu"
    assert footer == len("Museum")


def test_multiline_description_is_normalized(tmp_path):
    data = compile_text(tmp_path, VALID.replace("A useful category", "A useful\\ncategory"))
    assert b"A useful category" in data
    assert b"\\n" not in data


def test_guide_pages_are_compiled_for_cpm(tmp_path):
    source = tmp_path / "guide.txt"
    destination = tmp_path / "GUIDE.TXT"
    source.write_text("PAGE ONE\n%%PAGE%%\nPAGE TWO\n")

    compile_guide(source, destination)

    assert destination.read_bytes() == b"PAGE ONE\r\n\x0cPAGE TWO\r\n\x1a"


@pytest.mark.parametrize("old, replacement, message", [
    ("screensaver_seconds = 60", "screensaver_seconds = 2", "screensaver_seconds"),
    ("user = 0", "user = 16", ".user"),
    ('command = "CPMHELP"', 'command = "BAD.COM"', ".command"),
    ('description = "Read the guide"', 'description = "é"', "printable ASCII"),
    ('footer = "Museum"', 'footer = "Museum"\nmystery = "value"', "unknown key"),
])
def test_invalid_menu_is_rejected(tmp_path, old, replacement, message):
    with pytest.raises(ValueError, match=message):
        compile_text(tmp_path, VALID.replace(old, replacement))


def test_distribution_reference_must_exist(tmp_path):
    available = {"D": {0: [tmp_path / "OTHER.COM"]}}

    with pytest.raises(ValueError, match="missing D: user 0 CPMHELP.COM"):
        compile_text(tmp_path, VALID, available)
    available["D"][0].append(tmp_path / "CPMHELP.COM")
    compile_text(tmp_path, VALID, available)


def test_compact_application_omits_zero_filled_bss(tmp_path):
    binary = tmp_path / "MENUAPP.COM"
    link_map = tmp_path / "MENUAPP.map"
    output = tmp_path / "MENU.BIN"
    binary.write_bytes(b"application" + bytes(12))
    link_map.write_text(
        "__BSS_head = $010B ;\n"
        "__BSS_END_tail = $0117 ;\n",
        encoding="ascii",
    )

    _write_compact_application(binary, link_map, output)

    assert output.read_bytes() == b"application"


def test_compact_application_rejects_initialized_bss(tmp_path):
    binary = tmp_path / "MENUAPP.COM"
    link_map = tmp_path / "MENUAPP.map"
    output = tmp_path / "MENU.BIN"
    binary.write_bytes(b"application" + bytes(11) + b"x")
    link_map.write_text(
        "__BSS_head = $010B ;\n"
        "__BSS_END_tail = $0117 ;\n",
        encoding="ascii",
    )

    with pytest.raises(ValueError, match="nonzero"):
        _write_compact_application(binary, link_map, output)
