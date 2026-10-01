# SPDX-FileCopyrightText: 2026 P2000C SASI Distribution contributors
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

from pathlib import Path

import pytest

from p2000c_disk import constants
from p2000c_disk.image import DiskImage, ImageFormatError, SectorRange


def test_validate_size_accepts_exact_image(blank_image: Path) -> None:
    image = DiskImage(blank_image)
    image.validate_size()
    assert image.is_valid_size
    assert image.size == constants.IMAGE_SIZE


def test_validate_size_rejects_malformed_image(tmp_path: Path) -> None:
    path = tmp_path / "short.hda"
    path.write_bytes(b"short")
    image = DiskImage(path)
    assert not image.is_valid_size
    with pytest.raises(ImageFormatError, match="expected 10485760 bytes, got 5"):
        image.validate_size()
    with pytest.raises(ImageFormatError):
        image.read_sector(0)


def test_missing_image_has_useful_error(tmp_path: Path) -> None:
    with pytest.raises(ImageFormatError, match="cannot access image"):
        DiskImage(tmp_path / "missing.hda").validate_size()


def test_read_sector_and_arbitrary_range(blank_image: Path) -> None:
    with blank_image.open("r+b") as stream:
        stream.seek(3 * constants.SECTOR_SIZE)
        stream.write(bytes(range(256)))
    image = DiskImage(blank_image)
    assert image.read_sector(3) == bytes(range(256))
    assert image.read_range(3 * constants.SECTOR_SIZE + 10, 4) == bytes([10, 11, 12, 13])
    assert image.read_range(constants.IMAGE_SIZE, 0) == b""


@pytest.mark.parametrize("lba", [-1, constants.SECTOR_COUNT])
def test_read_sector_rejects_invalid_lba(blank_image: Path, lba: int) -> None:
    with pytest.raises(ValueError, match="LBA"):
        DiskImage(blank_image).read_sector(lba)


@pytest.mark.parametrize(
    ("offset", "length"), [(-1, 1), (0, -1), (constants.IMAGE_SIZE, 1)]
)
def test_read_range_rejects_invalid_bounds(
    blank_image: Path, offset: int, length: int
) -> None:
    with pytest.raises(ValueError):
        DiskImage(blank_image).read_range(offset, length)


def test_extract_system_overwrites_by_default_and_can_refuse(
    blank_image: Path, tmp_path: Path
) -> None:
    system = bytes(range(256)) * 32
    with blank_image.open("r+b") as stream:
        stream.write(system)
    output = tmp_path / "system.bin"
    image = DiskImage(blank_image)
    image.extract_system(output)
    assert output.read_bytes() == system
    output.write_bytes(b"old")
    image.extract_system(output)
    assert output.read_bytes() == system
    with pytest.raises(FileExistsError, match="already exists"):
        image.extract_system(output, overwrite=False)


def test_extract_from_malformed_image_does_not_create_output(tmp_path: Path) -> None:
    malformed = tmp_path / "malformed.hda"
    malformed.write_bytes(b"short")
    output = tmp_path / "system.bin"
    with pytest.raises(ImageFormatError):
        DiskImage(malformed).extract_system(output)
    assert not output.exists()


def test_non_fill_sectors_and_ranges(blank_image: Path) -> None:
    with blank_image.open("r+b") as stream:
        for lba in (0, 1, 4, 8, 9, 10):
            stream.seek(lba * constants.SECTOR_SIZE)
            stream.write(b"X")
    image = DiskImage(blank_image)
    assert image.non_fill_sectors() == (0, 1, 4, 8, 9, 10)
    assert image.non_fill_ranges() == (
        SectorRange(0, 1),
        SectorRange(4, 4),
        SectorRange(8, 10),
    )


def test_non_fill_rejects_invalid_fill_byte(blank_image: Path) -> None:
    with pytest.raises(ValueError, match="fill byte"):
        DiskImage(blank_image).non_fill_sectors(256)


def test_ascii_strings_only_come_from_system_area(blank_image: Path) -> None:
    with blank_image.open("r+b") as stream:
        stream.write(b"\x00PHILIPS P2000C\r\nA:8MB-HRD1\x00abc\x00")
        stream.seek(constants.SYSTEM_AREA_SIZE)
        stream.write(b"SHOULD NOT APPEAR")
    strings = DiskImage(blank_image).system_ascii_strings(minimum_length=4)
    assert strings == ("PHILIPS P2000C", "A:8MB-HRD1")


def test_ascii_string_minimum_length_is_validated(blank_image: Path) -> None:
    with pytest.raises(ValueError, match="at least 1"):
        DiskImage(blank_image).system_ascii_strings(0)
