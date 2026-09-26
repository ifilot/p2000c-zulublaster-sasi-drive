from __future__ import annotations

from pathlib import Path

import pytest

from p2000c_disk import constants
from p2000c_disk.directory import (
    DirectoryFormatError,
    parse_directory_entry,
    read_directory,
)
from p2000c_disk.image import DiskImage


def make_entry(
    *,
    user: int = 2,
    name: bytes = b"README  ",
    extension: bytes = b"TXT",
) -> bytes:
    return bytes([user]) + name + extension + bytes([3, 4, 5, 0x7F]) + bytes(range(16))


def test_parse_active_directory_entry_preserves_all_fields() -> None:
    raw = make_entry(extension=bytes([ord("T") | 0x80, ord("X"), ord("T")]))
    entry = parse_directory_entry(raw, index=12)
    assert entry is not None
    assert entry.index == 12
    assert entry.user_number == 2
    assert entry.filename == "README"
    assert entry.extension == "TXT"
    assert entry.normalized_filename == "README.TXT"
    assert (entry.extent, entry.s1, entry.s2, entry.record_count) == (3, 4, 5, 0x7F)
    assert entry.allocation == bytes(range(16))
    assert entry.raw == raw
    assert entry.raw_filename == b"README  "
    assert entry.raw_extension == bytes([ord("T") | 0x80, ord("X"), ord("T")])
    assert not entry.is_system
    assert entry.image_offset == (
        constants.DIRECTORY_START_LBA * constants.SECTOR_SIZE
        + 12 * constants.DIRECTORY_ENTRY_SIZE
    )
    assert entry.allocation_values[:3] == (0x0100, 0x0302, 0x0504)
    assert entry.identity == (2, "README.TXT")


def test_normalized_filename_without_extension() -> None:
    entry = parse_directory_entry(make_entry(extension=b"   "))
    assert entry is not None
    assert entry.normalized_filename == "README"


def test_system_attribute_uses_second_extension_high_bit() -> None:
    entry = parse_directory_entry(
        make_entry(extension=bytes([ord("T"), ord("X") | 0x80, ord("T")]))
    )
    assert entry is not None
    assert entry.normalized_filename == "README.TXT"
    assert entry.is_system


def test_unused_directory_entry_is_ignored() -> None:
    assert parse_directory_entry(bytes([0xE5]) * 32) is None


def test_parse_rejects_malformed_entries() -> None:
    with pytest.raises(DirectoryFormatError, match="must be 32 bytes"):
        parse_directory_entry(b"short")
    with pytest.raises(DirectoryFormatError, match="invalid user number"):
        parse_directory_entry(make_entry(user=0x40))
    with pytest.raises(DirectoryFormatError, match="non-printable filename"):
        parse_directory_entry(make_entry(name=b"BAD\x01    "))
    with pytest.raises(DirectoryFormatError, match="empty filename"):
        parse_directory_entry(make_entry(name=b"        "))


def test_read_directory_uses_known_offset_and_skips_unused(blank_image: Path) -> None:
    first = make_entry(user=0, name=b"FIRST   ", extension=b"COM")
    third = make_entry(user=1, name=b"SECOND  ", extension=b"DAT")
    offset = constants.DIRECTORY_START_LBA * constants.SECTOR_SIZE
    with blank_image.open("r+b") as stream:
        stream.seek(offset)
        stream.write(first)
        stream.write(bytes([0xE5]) * 32)
        stream.write(third)
    entries = read_directory(DiskImage(blank_image))
    assert [entry.index for entry in entries] == [0, 2]
    assert [entry.normalized_filename for entry in entries] == ["FIRST.COM", "SECOND.DAT"]
