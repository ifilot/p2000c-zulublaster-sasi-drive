# SPDX-FileCopyrightText: 2026 P2000C SASI Distribution contributors
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import os
from hashlib import md5, sha256
from pathlib import Path
import shutil

import pytest

from p2000c_disk import constants
from p2000c_disk.allocation import analyze_allocation
from p2000c_disk.config import ConfigUpdates, apply_config_updates, inspect_config
from p2000c_disk.directory import read_directory
from p2000c_disk.filesystem import delete_file, put_file, read_file
from p2000c_disk.image import DiskImage
from p2000c_disk.verify import verify_image


@pytest.fixture(scope="module")
def reference_image() -> DiskImage:
    configured = os.environ.get("P2000C_REFERENCE_IMAGE")
    path = Path(configured) if configured else Path("tests/fixtures/references/HD0_256_BOOT.hda")
    if not path.is_file():
        pytest.skip(f"reference image is not available: {path}")
    return DiskImage(path)


@pytest.fixture(scope="module")
def files_image() -> DiskImage:
    configured = os.environ.get("P2000C_FILES_IMAGE")
    path = Path(configured) if configured else Path("tests/fixtures/references/HD0_256_FILES.hda")
    if not path.is_file():
        pytest.skip(f"files image is not available: {path}")
    return DiskImage(path)


FILES_IMAGE_MD5: dict[str, str] = {
    "ASM.COM": "44b451bcfa33e7602c1e514160327427",
    "CBIOS61.COM": "a76bf20f15f38e6e1ab2586450f11a73",
    "CBIOS62.COM": "2c76c0b867b7f0c55ebd23e8355a8982",
    "CBIOS63.COM": "8344910019151e78a3fbcb1fe310e2f0",
    "CONFIG.COM": "0baebae5ebf2f6f3ce96e330125cbcd1",
    "CONFIG.DAT": "014d251fc9c11cfd2ab4b2cda4e32701",
    "CONFIG.MSG": "d03da5b5a549685abe17d46c048219a0",
    "CPM61.COM": "59a1d0ec7b5fe401768fea504ebbac18",
    "CPM62.COM": "346e5ba1845749339e4bfb8f3b351679",
    "CPM63.COM": "0f635cfd34a9dbd3eceffbf82ae471dc",
    "DDT.COM": "d79add381da89be3e2737327599d0f82",
    "ED.COM": "bb11fc71dac73204a7cf61d104f4f7ae",
    "LOAD.COM": "21c2b98e55a1fbe8354523ac18b14039",
    "PIP.COM": "ed658f4379ab0a0e555fa091a44da061",
    "STAT.COM": "dc396b8617c04c623383d63ba36c4337",
    "SYSGEN.COM": "1b2f666500ddd6b178838f4b0dff6475",
}


@pytest.mark.integration
def test_files_image_contents_and_configuration_are_readable(
    files_image: DiskImage,
) -> None:
    before = sha256(files_image.path.read_bytes()).digest()
    assert verify_image(files_image.path).is_valid
    entries = read_directory(files_image)
    assert {entry.normalized_filename for entry in entries} == set(FILES_IMAGE_MD5)
    for filename, expected in FILES_IMAGE_MD5.items():
        assert md5(read_file(files_image.path, filename)).hexdigest() == expected

    inspection = inspect_config(files_image)
    assert inspection.layout_status == "recognized"
    assert inspection.fields["autostart"].value == ""
    assert inspection.fields["welcome_message"].value == "Hello P2000C"
    assert sha256(files_image.path.read_bytes()).digest() == before


@pytest.mark.integration
def test_files_image_empty_autostart_can_be_set_copy_on_write(
    files_image: DiskImage, tmp_path: Path
) -> None:
    source_digest = sha256(files_image.path.read_bytes()).digest()
    output = tmp_path / "files-autostart.hda"
    _, plan, written = apply_config_updates(
        files_image.path,
        ConfigUpdates(autostart="DIR"),
        output,
    )
    assert written == output
    assert [(patch.offset, len(patch.new_bytes)) for patch in plan.patches] == [
        (135, 1),
        (136, 128),
    ]
    assert inspect_config(output).fields["autostart"].value == "DIR"
    assert verify_image(output).is_valid
    source_after_system = files_image.path.read_bytes()[constants.SYSTEM_AREA_SIZE :]
    assert output.read_bytes()[constants.SYSTEM_AREA_SIZE :] == source_after_system
    assert sha256(files_image.path.read_bytes()).digest() == source_digest


@pytest.mark.integration
def test_reference_geometry_without_modifying_image(reference_image: DiskImage) -> None:
    reference_image.validate_size()
    assert len(reference_image.read_sector(0)) == constants.SECTOR_SIZE
    assert len(reference_image.system_area()) == constants.SYSTEM_AREA_SIZE
    assert any(
        constants.SYSTEM_CONFIGURATION_TEXT.casefold() in value.casefold()
        for value in reference_image.system_ascii_strings()
    )


@pytest.mark.integration
def test_reference_directory_is_readable(reference_image: DiskImage) -> None:
    entries = read_directory(reference_image)
    assert all(entry.raw != bytes([0xE5]) * 32 for entry in entries)


@pytest.mark.integration
def test_reference_allocation_analysis_uses_independent_dpb_confirmation(
    reference_image: DiskImage,
) -> None:
    report = analyze_allocation(reference_image.path)
    assert len(report.images[0].confirmed_mappings) == 1
    confirmed = report.images[0].confirmed_mappings[0]
    assert confirmed.interpretation == "u16le"
    assert confirmed.block_size_sectors == 16
    assert confirmed.anchor_name == "directory-start"
    assert {candidate.block_size_sectors for candidate in report.images[0].candidates} == {
        1,
        2,
        4,
        8,
        16,
        32,
        64,
    }


@pytest.mark.integration
def test_reference_dpb_supports_confirmed_layout(reference_image: DiskImage) -> None:
    system = reference_image.system_area()
    offset = constants.DPB_REFERENCE_OFFSET
    assert int.from_bytes(system[offset : offset + 2], "little") == constants.DPB_SECTORS_PER_TRACK
    assert system[offset + 2] == constants.DPB_BLOCK_SHIFT
    assert system[offset + 3] == constants.DPB_BLOCK_MASK
    assert system[offset + 4] == constants.DPB_EXTENT_MASK
    assert int.from_bytes(system[offset + 5 : offset + 7], "little") == constants.DPB_MAXIMUM_BLOCK
    assert int.from_bytes(system[offset + 7 : offset + 9], "little") == constants.DPB_MAXIMUM_DIRECTORY_ENTRY
    assert tuple(system[offset + 9 : offset + 11]) == constants.DPB_ALLOCATION_RESERVED
    assert int.from_bytes(system[offset + 13 : offset + 15], "little") == constants.DPB_RESERVED_TRACKS


@pytest.mark.integration
def test_reference_allocation_slack_uses_e5(reference_image: DiskImage) -> None:
    hello = read_directory(reference_image)[0]
    assert hello.normalized_filename == "HELLO.COM"
    assert hello.extent_record_count == 1
    block = hello.allocation_values[0]
    data = reference_image.read_range(
        (constants.DIRECTORY_START_LBA + block * constants.ALLOCATION_BLOCK_SECTORS)
        * constants.SECTOR_SIZE,
        constants.ALLOCATION_BLOCK_SIZE,
    )
    assert data[constants.LOGICAL_RECORD_SIZE :] == bytes(
        [constants.ALLOCATION_SLACK_FILL_BYTE]
    ) * (constants.ALLOCATION_BLOCK_SIZE - constants.LOGICAL_RECORD_SIZE)


@pytest.mark.integration
def test_reference_copy_on_write_lifecycle(
    reference_image: DiskImage, tmp_path: Path
) -> None:
    source_digest = sha256(reference_image.path.read_bytes()).digest()
    system = reference_image.system_area()
    working_source = tmp_path / "working-source.hda"
    shutil.copy2(reference_image.path, working_source)
    working_digest = sha256(working_source.read_bytes()).digest()
    data = bytes(index % 256 for index in range(constants.DIRECTORY_EXTENT_SIZE + 128))
    host = tmp_path / "integration.bin"
    host.write_bytes(data)
    added = tmp_path / "added.hda"
    plan = put_file(
        working_source,
        host,
        added,
        cpm_filename="CXUNIQ.BIN",
    )
    assert len(plan.directory_entries) == 2
    assert verify_image(added).is_valid
    assert read_file(added, "cxuniq.bin") == data
    assert DiskImage(added).system_area() == system

    deleted = tmp_path / "deleted.hda"
    delete_file(added, "CXUNIQ.BIN", deleted)
    assert verify_image(deleted).is_valid
    assert DiskImage(deleted).system_area() == system
    assert sha256(working_source.read_bytes()).digest() == working_digest
    assert sha256(reference_image.path.read_bytes()).digest() == source_digest


@pytest.mark.integration
def test_reference_welcome_copy_on_write(
    reference_image: DiskImage, tmp_path: Path
) -> None:
    reference_digest = sha256(reference_image.path.read_bytes()).digest()
    working = tmp_path / "config-source.hda"
    shutil.copy2(reference_image.path, working)
    before = working.read_bytes()
    assert inspect_config(working).fields["welcome_message"].value == "Hello Ivo"
    output = tmp_path / "welcome.hda"
    _, plan, written = apply_config_updates(
        working,
        ConfigUpdates(welcome="Welcome!!"),
        output,
    )
    assert written == output
    assert [(patch.offset, len(patch.new_bytes)) for patch in plan.patches] == [(6_838, 9)]
    after = output.read_bytes()
    allowed = set(range(6_838, 6_847))
    changed = {
        offset
        for offset, (old, new) in enumerate(zip(before, after, strict=True))
        if old != new
    }
    assert changed <= allowed
    assert after[constants.SYSTEM_AREA_SIZE :] == before[constants.SYSTEM_AREA_SIZE :]
    assert inspect_config(output).fields["welcome_message"].value == "Welcome!!"
    assert verify_image(output).is_valid
    assert sha256(reference_image.path.read_bytes()).digest() == reference_digest


@pytest.mark.integration
def test_reference_autostart_config_copy_on_write(
    reference_image: DiskImage, tmp_path: Path
) -> None:
    source_digest = sha256(reference_image.path.read_bytes()).digest()
    working = tmp_path / "config-source.hda"
    shutil.copy2(reference_image.path, working)
    before = working.read_bytes()
    output = tmp_path / "config-output.hda"
    _, plan, written = apply_config_updates(
        working,
        ConfigUpdates(autostart="Codex IPL"),
        output,
    )
    assert written == output
    assert [(patch.offset, len(patch.new_bytes)) for patch in plan.patches] == [
        (135, 1),
        (136, 128),
    ]
    after = output.read_bytes()
    expected_offsets = set(range(135, 264))
    changed = {
        offset
        for offset, (old, new) in enumerate(zip(before, after, strict=True))
        if old != new
    }
    assert changed <= expected_offsets
    assert after[constants.SYSTEM_AREA_SIZE :] == before[constants.SYSTEM_AREA_SIZE :]
    inspection = inspect_config(output)
    assert inspection.fields["autostart"].value == "Codex IPL"
    assert inspection.fields["welcome_message"].value == "Hello Ivo"
    assert verify_image(output).is_valid
    assert sha256(reference_image.path.read_bytes()).digest() == source_digest
