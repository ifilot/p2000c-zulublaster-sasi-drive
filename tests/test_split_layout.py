# SPDX-FileCopyrightText: 2026 P2000C SASI Distribution contributors
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

from hashlib import sha256
from pathlib import Path

import pytest

from p2000c_disk import constants
from p2000c_disk.builder import BuildError, build_image
from p2000c_disk.cli import main
from p2000c_disk.config import ConfigUpdates, inspect_config, plan_config_updates
from p2000c_disk.filesystem import list_files, put_file, read_file
from p2000c_disk.image import DiskImage
from p2000c_disk.layout import (
    LayoutDetectionError,
    SPLIT_HIGH_PARTITION,
    SPLIT_LOW_PARTITION,
    detect_image_layout,
)
from p2000c_disk.verify import verify_image


def _encode_dpb(maximum_block: int, allocation: tuple[int, int], off: int) -> bytes:
    return (
        constants.DPB_SECTORS_PER_TRACK.to_bytes(2, "little")
        + bytes(
            (
                constants.DPB_BLOCK_SHIFT,
                constants.DPB_BLOCK_MASK,
                constants.DPB_EXTENT_MASK,
            )
        )
        + maximum_block.to_bytes(2, "little")
        + constants.DPB_MAXIMUM_DIRECTORY_ENTRY.to_bytes(2, "little")
        + bytes(allocation)
        + constants.DPB_DIRECTORY_CHECK_SIZE.to_bytes(2, "little")
        + off.to_bytes(2, "little")
    )


def _split_system() -> bytes:
    system = bytearray([constants.DEFAULT_FILL_BYTE]) * constants.SYSTEM_AREA_SIZE
    system[64:79] = _encode_dpb(
        constants.SPLIT_LOW_DPB_MAXIMUM_BLOCK,
        constants.SPLIT_LOW_DPB_ALLOCATION_RESERVED,
        constants.SPLIT_LOW_DPB_RESERVED_TRACKS,
    )
    system[96:111] = _encode_dpb(
        constants.SPLIT_HIGH_DPB_MAXIMUM_BLOCK,
        constants.SPLIT_HIGH_DPB_ALLOCATION_RESERVED,
        constants.SPLIT_HIGH_DPB_RESERVED_TRACKS,
    )
    return bytes(system)


@pytest.fixture
def blank_split_image(tmp_path: Path) -> Path:
    system = tmp_path / "split.trk"
    system.write_bytes(_split_system())
    return build_image(tmp_path / "split.hda", system, layout="split")


def test_detects_split_geometry_from_both_dpbs() -> None:
    layout = detect_image_layout(_split_system())
    assert layout.mode == "split"
    assert layout.partitions == (SPLIT_LOW_PARTITION, SPLIT_HIGH_PARTITION)
    assert SPLIT_LOW_PARTITION.directory_start_lba == 32
    assert SPLIT_LOW_PARTITION.filesystem_end_lba == 19_583
    assert SPLIT_HIGH_PARTITION.directory_start_lba == 19_584
    assert SPLIT_HIGH_PARTITION.filesystem_end_lba == 39_167
    assert SPLIT_LOW_PARTITION.first_usable_allocation_block == 2
    assert SPLIT_HIGH_PARTITION.first_usable_allocation_block == 2


def test_split_file_operations_require_and_honor_partition(
    blank_split_image: Path, tmp_path: Path
) -> None:
    with pytest.raises(LayoutDetectionError, match="choose --partition"):
        list_files(blank_split_image)

    low_host = tmp_path / "LOW.TXT"
    low_host.write_bytes(b"low")
    with_low = tmp_path / "with-low.hda"
    low_plan = put_file(
        blank_split_image, low_host, with_low, partition="low"
    )
    assert low_plan.allocation_blocks == (2,)

    high_host = tmp_path / "HIGH.TXT"
    high_host.write_bytes(b"high")
    complete = tmp_path / "complete.hda"
    high_plan = put_file(with_low, high_host, complete, partition="high")
    assert high_plan.allocation_blocks == (2,)

    assert [item.normalized_filename for item in list_files(complete, "low")] == [
        "LOW.TXT"
    ]
    assert [item.normalized_filename for item in list_files(complete, "high")] == [
        "HIGH.TXT"
    ]
    assert read_file(complete, "LOW.TXT", partition="low")[:3] == b"low"
    assert read_file(complete, "HIGH.TXT", partition="high")[:4] == b"high"
    report = verify_image(complete)
    assert report.is_valid
    assert report.layout_mode == "split"
    assert report.partitions == ("low", "high")

    disk = DiskImage(complete)
    assert disk.read_range(
        SPLIT_LOW_PARTITION.block_offset(2), constants.ALLOCATION_BLOCK_SIZE
    ).startswith(b"low")
    assert disk.read_range(
        SPLIT_HIGH_PARTITION.block_offset(2), constants.ALLOCATION_BLOCK_SIZE
    ).startswith(b"high")


def test_split_build_rejects_missing_or_mismatched_system_tracks(
    tmp_path: Path,
) -> None:
    with pytest.raises(BuildError, match="requires --system"):
        build_image(tmp_path / "missing.hda", layout="split")
    single = tmp_path / "single.trk"
    single.write_bytes(
        bytes([constants.DEFAULT_FILL_BYTE]) * constants.SYSTEM_AREA_SIZE
    )
    with pytest.raises(BuildError, match="requested split layout"):
        build_image(tmp_path / "wrong.hda", single, layout="split")


def test_split_cli_lists_both_and_requires_choice_for_get(
    blank_split_image: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    host = tmp_path / "ONE.COM"
    host.write_bytes(b"one")
    populated = tmp_path / "populated.hda"
    put_file(blank_split_image, host, populated, partition="high")

    assert main(["list", str(populated)]) == 0
    rendered = capsys.readouterr().out
    assert "Partition: low" in rendered
    assert "Partition: high" in rendered
    assert "ONE.COM" in rendered

    output = tmp_path / "one.com"
    assert main(["get", str(populated), "ONE.COM", str(output)]) == 1
    assert "--partition low" in capsys.readouterr().err
    assert main(
        [
            "get",
            str(populated),
            "ONE.COM",
            str(output),
            "--partition",
            "high",
        ]
    ) == 0
    assert output.read_bytes().startswith(b"one")


@pytest.mark.integration
def test_reference_split_image_lists_zork_without_modification() -> None:
    path = Path("tests/fixtures/references/HD0_256_SPLIT.hda")
    if not path.is_file():
        pytest.skip("split reference image not available")
    before = sha256(path.read_bytes()).digest()
    assert [item.normalized_filename for item in list_files(path, "low")] == [
        "CPM61.COM",
        "CPM62.COM",
        "CPM63.COM",
    ]
    assert [item.normalized_filename for item in list_files(path, "high")] == [
        "ZORK1.COM",
        "ZORK1.DAT",
    ]
    assert verify_image(path).is_valid
    inspection = inspect_config(path)
    assert inspection.layout_status == "recognized"
    assert inspection.boot_drive_configuration == "A:5MB-HRD1"
    assert inspection.fields["welcome_message"].value == "Hello P2000C"
    _, plan = plan_config_updates(
        path, ConfigUpdates(welcome="Codex Split!")
    )
    assert plan.patches[0].offset == 6_909
    assert sha256(path.read_bytes()).digest() == before
