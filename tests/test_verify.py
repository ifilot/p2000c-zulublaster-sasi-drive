# SPDX-FileCopyrightText: 2026 P2000C SASI Distribution contributors
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

from pathlib import Path

from p2000c_disk import constants
from p2000c_disk.verify import verify_image


def _entry(
    name: bytes,
    *,
    extent: int = 0,
    s1: int = 0,
    s2: int = 0,
    records: int = 1,
    blocks: tuple[int, ...] = (4,),
) -> bytes:
    allocation = b"".join(block.to_bytes(2, "little") for block in blocks)
    allocation = allocation.ljust(16, b"\x00")
    return (
        b"\x00"
        + name.ljust(8, b" ")
        + b"DAT"
        + bytes([extent, s1, s2, records])
        + allocation
    )


def _write_entries(path: Path, *entries: bytes) -> None:
    with path.open("r+b") as stream:
        stream.seek(constants.DIRECTORY_START_LBA * constants.SECTOR_SIZE)
        for entry in entries:
            stream.write(entry)


def test_verify_accepts_empty_and_simple_images(blank_image: Path) -> None:
    assert verify_image(blank_image).is_valid
    _write_entries(blank_image, _entry(b"ONE"))
    report = verify_image(blank_image)
    assert report.is_valid
    assert report.active_entry_count == 1
    assert report.file_count == 1


def test_verify_detects_invalid_size(tmp_path: Path) -> None:
    path = tmp_path / "short.hda"
    path.write_bytes(b"short")
    report = verify_image(path)
    assert not report.is_valid
    assert report.errors[0].code == "invalid-image-size"


def test_verify_rejects_nonblank_system_without_confirmed_dpb(blank_image: Path) -> None:
    with blank_image.open("r+b") as stream:
        stream.seek(0)
        stream.write(b"not a recognized boot system")
    report = verify_image(blank_image)
    assert not report.is_valid
    assert "unsupported-dpb" in {issue.code for issue in report.errors}


def test_verify_detects_shared_allocation(blank_image: Path) -> None:
    _write_entries(blank_image, _entry(b"FIRST", blocks=(4,)), _entry(b"SECOND", blocks=(4,)))
    report = verify_image(blank_image)
    assert "overlapping-allocation" in {issue.code for issue in report.errors}


def test_verify_detects_reserved_and_out_of_range_blocks(blank_image: Path) -> None:
    _write_entries(
        blank_image,
        _entry(b"RESERVED", blocks=(1,)),
        _entry(b"TOOHIGH", blocks=(constants.DPB_MAXIMUM_BLOCK + 1,)),
    )
    codes = {issue.code for issue in verify_image(blank_image).errors}
    assert "reserved-block-reference" in codes
    assert "out-of-range-block" in codes


def test_verify_detects_data_beyond_image(blank_image: Path) -> None:
    _write_entries(blank_image, _entry(b"BEYOND", blocks=(4_000,)))
    codes = {issue.code for issue in verify_image(blank_image).errors}
    assert "out-of-range-block" in codes
    assert "data-beyond-image" in codes


def test_verify_detects_impossible_record_count(blank_image: Path) -> None:
    _write_entries(blank_image, _entry(b"BADRC", records=129, blocks=(4, 5, 6, 7, 8)))
    codes = {issue.code for issue in verify_image(blank_image).errors}
    assert "impossible-record-count" in codes


def test_verify_detects_duplicate_and_missing_extents(blank_image: Path) -> None:
    duplicate = _entry(b"DUP", extent=0, records=128, blocks=(4, 5, 6, 7))
    duplicate_again = _entry(b"DUP", extent=1, records=128, blocks=(8, 9, 10, 11, 12, 13, 14, 15))
    missing = _entry(b"MISSING", extent=2, records=1, blocks=(16,))
    _write_entries(blank_image, duplicate, duplicate_again, missing)
    codes = {issue.code for issue in verify_image(blank_image).errors}
    assert "duplicate-extent-number" in codes
    assert "missing-extent-sequence" in codes


def test_verify_detects_short_nonfinal_extent(blank_image: Path) -> None:
    first = _entry(b"MULTI", extent=0, records=1, blocks=(4,))
    second = _entry(b"MULTI", extent=2, records=1, blocks=(5,))
    _write_entries(blank_image, first, second)
    codes = {issue.code for issue in verify_image(blank_image).errors}
    assert "short-nonfinal-extent" in codes


def test_verify_detects_allocation_gaps_and_count_mismatch(blank_image: Path) -> None:
    allocation = (4).to_bytes(2, "little") + b"\x00\x00" + (5).to_bytes(2, "little")
    raw = (
        b"\x00GAPPED  DAT"
        + bytes([0, 0, 0, 1])
        + allocation.ljust(16, b"\x00")
    )
    _write_entries(blank_image, raw)
    codes = {issue.code for issue in verify_image(blank_image).errors}
    assert "allocation-gap" in codes
    assert "allocation-count-mismatch" in codes
