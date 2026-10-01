# SPDX-FileCopyrightText: 2026 P2000C SASI Distribution contributors
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import os
from pathlib import Path

import pytest

from p2000c_disk import constants
from p2000c_disk.builder import BuildError, build_image
from p2000c_disk.image import DiskImage


def test_build_blank_image(tmp_path: Path) -> None:
    output = build_image(tmp_path / "new.hda")
    assert output.stat().st_size == constants.IMAGE_SIZE
    assert DiskImage(output).non_fill_sectors() == ()


def test_build_with_exact_system_tracks(tmp_path: Path) -> None:
    system = bytes(range(256)) * 32
    system_path = tmp_path / "system.bin"
    system_path.write_bytes(system)
    output = build_image(tmp_path / "new.hda", system_path)
    image = DiskImage(output)
    assert image.system_area() == system
    assert image.read_sector(constants.SYSTEM_AREA_SECTOR_COUNT) == bytes([0xE5]) * 256


@pytest.mark.parametrize("size", [0, constants.SYSTEM_AREA_SIZE - 1, constants.SYSTEM_AREA_SIZE + 1])
def test_build_rejects_wrong_system_track_size(tmp_path: Path, size: int) -> None:
    system_path = tmp_path / "system.bin"
    system_path.write_bytes(b"S" * size)
    output = tmp_path / "new.hda"
    with pytest.raises(BuildError, match="exactly 8192 bytes"):
        build_image(output, system_path)
    assert not output.exists()
    assert not any(path.suffix == ".tmp" for path in tmp_path.iterdir())


def test_build_overwrites_existing_output_by_default(tmp_path: Path) -> None:
    output = tmp_path / "existing.hda"
    output.write_bytes(b"keep me")
    build_image(output)
    assert output.stat().st_size == constants.IMAGE_SIZE


def test_build_can_refuse_overwrite_when_requested(tmp_path: Path) -> None:
    output = tmp_path / "existing.hda"
    output.write_bytes(b"old")
    with pytest.raises(FileExistsError, match="already exists"):
        build_image(output, overwrite=False)
    assert output.read_bytes() == b"old"


def test_build_no_clobber_treats_dangling_symlink_as_existing_output(tmp_path: Path) -> None:
    output = tmp_path / "link.hda"
    output.symlink_to(tmp_path / "missing-target.hda")
    with pytest.raises(FileExistsError, match="already exists"):
        build_image(output, overwrite=False)
    assert output.is_symlink()


def test_build_removes_temporary_file_when_rename_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output = tmp_path / "new.hda"

    def fail_replace(source: str | bytes | os.PathLike[str] | os.PathLike[bytes],
                     destination: str | bytes | os.PathLike[str] | os.PathLike[bytes]) -> None:
        raise OSError("synthetic rename failure")

    monkeypatch.setattr(os, "replace", fail_replace)
    with pytest.raises(BuildError, match="synthetic rename failure"):
        build_image(output)
    assert not output.exists()
    assert list(tmp_path.iterdir()) == []


def test_build_requires_existing_parent(tmp_path: Path) -> None:
    with pytest.raises(BuildError, match="output directory does not exist"):
        build_image(tmp_path / "missing" / "new.hda")
