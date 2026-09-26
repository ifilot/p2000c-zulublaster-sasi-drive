from __future__ import annotations

from hashlib import sha256
import os
from pathlib import Path

import pytest

from p2000c_disk import constants
from p2000c_disk.directory import read_directory
from p2000c_disk.filesystem import (
    AllocationError,
    CPMFileNotFoundError,
    DuplicateFileError,
    FilenameError,
    MutationError,
    delete_file,
    extract_file,
    normalize_cpm_filename,
    plan_put,
    put_file,
    put_files,
    read_file,
)
from p2000c_disk.image import DiskImage
from p2000c_disk.verify import verify_image


def _data(size: int) -> bytes:
    return bytes(index % 256 for index in range(size))


def _host_file(tmp_path: Path, size: int, name: str = "source.bin") -> Path:
    path = tmp_path / name
    path.write_bytes(_data(size))
    return path


@pytest.mark.parametrize("size", [0, 1, 127, 128, 129, 4_095, 4_096, 4_097, 5_000])
def test_put_get_record_and_block_boundaries(blank_image: Path, tmp_path: Path, size: int) -> None:
    host = _host_file(tmp_path, size)
    output = tmp_path / f"output-{size}.hda"
    plan = put_file(blank_image, host, output, cpm_filename="ROUND.BIN")
    expected = _data(size) + bytes([0x1A]) * (plan.padded_record_size - size)
    assert read_file(output, "round.bin") == expected
    assert verify_image(output).is_valid
    assert blank_image.read_bytes() == bytes([0xE5]) * constants.IMAGE_SIZE


def test_extract_one_record_overwrites_by_default_and_supports_no_clobber(
    blank_image: Path, tmp_path: Path
) -> None:
    host = _host_file(tmp_path, 128)
    image = tmp_path / "with-file.hda"
    put_file(blank_image, host, image, cpm_filename="HELLO.COM")
    extracted = tmp_path / "hello.com"
    extract_file(image, "hello.com", extracted)
    assert extracted.read_bytes() == host.read_bytes()
    extracted.write_bytes(b"old")
    extract_file(image, "HELLO.COM", extracted)
    assert extracted.read_bytes() == host.read_bytes()
    with pytest.raises(FileExistsError):
        extract_file(image, "HELLO.COM", extracted, overwrite=False)


def test_put_uses_reference_padding_conventions(blank_image: Path, tmp_path: Path) -> None:
    host = _host_file(tmp_path, 129)
    image = tmp_path / "padding.hda"
    plan = put_file(blank_image, host, image, cpm_filename="PAD.DAT")
    block = DiskImage(image).read_range(
        (constants.DIRECTORY_START_LBA
         + plan.allocation_blocks[0] * constants.ALLOCATION_BLOCK_SECTORS)
        * constants.SECTOR_SIZE,
        constants.ALLOCATION_BLOCK_SIZE,
    )
    assert block[:129] == host.read_bytes()
    assert block[129:256] == bytes([constants.RECORD_PADDING_BYTE]) * 127
    assert block[256:] == bytes([constants.ALLOCATION_SLACK_FILL_BYTE]) * (
        constants.ALLOCATION_BLOCK_SIZE - 256
    )


def test_put_and_get_multi_extent_file(blank_image: Path, tmp_path: Path) -> None:
    host = _host_file(tmp_path, constants.DIRECTORY_EXTENT_SIZE + 777)
    output = tmp_path / "multi.hda"
    plan = put_file(blank_image, host, output, cpm_filename="MULTI.DAT")
    entries = read_directory(DiskImage(output))
    assert len(entries) == 2
    assert [entry.directory_extent_number for entry in entries] == [0, 1]
    assert entries[0].extent_record_count == constants.DIRECTORY_EXTENT_RECORDS
    expected = host.read_bytes() + bytes([0x1A]) * (plan.padded_record_size - host.stat().st_size)
    assert read_file(output, "MULTI.DAT") == expected


def test_put_empty_file_creates_one_extent_without_blocks(blank_image: Path, tmp_path: Path) -> None:
    host = _host_file(tmp_path, 0)
    output = tmp_path / "empty.hda"
    plan = put_file(blank_image, host, output, cpm_filename="EMPTY")
    assert plan.record_count == 0
    assert plan.allocation_blocks == ()
    entries = read_directory(DiskImage(output))
    assert len(entries) == 1
    assert entries[0].record_count == 0
    assert read_file(output, "EMPTY") == b""


def test_duplicate_filename_is_replaced_by_default_and_can_be_refused(
    blank_image: Path, tmp_path: Path
) -> None:
    host = _host_file(tmp_path, 10)
    first = tmp_path / "first.hda"
    put_file(blank_image, host, first, cpm_filename="SAME.DAT")
    second = tmp_path / "second.hda"
    plan = put_file(first, host, second, cpm_filename="same.dat")
    assert plan.replaced_directory_indices
    with pytest.raises(DuplicateFileError, match="replace=True"):
        put_file(first, host, tmp_path / "third.hda", cpm_filename="same.dat", replace=False)


@pytest.mark.parametrize(
    ("original_size", "replacement_size"),
    [
        (constants.DIRECTORY_EXTENT_SIZE + 1, 129),
        (129, constants.DIRECTORY_EXTENT_SIZE + 1),
        (128, 0),
    ],
)
def test_put_can_replace_existing_file_and_reclaim_its_space(
    blank_image: Path,
    tmp_path: Path,
    original_size: int,
    replacement_size: int,
) -> None:
    original_host = _host_file(tmp_path, original_size, "original.bin")
    original_image = tmp_path / "original.hda"
    original_plan = put_file(
        blank_image, original_host, original_image, cpm_filename="SAME.DAT"
    )
    replacement_host = tmp_path / "replacement.bin"
    replacement_data = bytes((255 - index) % 256 for index in range(replacement_size))
    replacement_host.write_bytes(replacement_data)
    replaced_image = tmp_path / "replaced.hda"

    replacement_plan = put_file(
        original_image,
        replacement_host,
        replaced_image,
        cpm_filename="same.dat",
        replace=True,
    )

    assert replacement_plan.replaced_directory_indices == original_plan.directory_indices
    assert replacement_plan.directory_indices[0] == original_plan.directory_indices[0]
    if replacement_plan.allocation_blocks:
        assert replacement_plan.allocation_blocks[0] == original_plan.allocation_blocks[0]
    expected = replacement_data + bytes([constants.RECORD_PADDING_BYTE]) * (
        replacement_plan.padded_record_size - replacement_size
    )
    assert read_file(replaced_image, "SAME.DAT") == expected
    assert len(read_directory(DiskImage(replaced_image))) == len(
        replacement_plan.directory_indices
    )
    assert verify_image(replaced_image).is_valid
    assert read_file(original_image, "SAME.DAT")[:original_size] == original_host.read_bytes()


def test_put_files_preserves_requested_directory_order(
    blank_image: Path, tmp_path: Path
) -> None:
    first = _host_file(tmp_path, 129, "CPM62.COM")
    second = _host_file(tmp_path, constants.DIRECTORY_EXTENT_SIZE + 1, "CBIOS61.COM")
    third = _host_file(tmp_path, 0, "CONFIG")
    output = tmp_path / "ordered.hda"
    before = sha256(blank_image.read_bytes()).digest()

    plans = put_files(blank_image, (first, second, third), output)

    assert [plan.normalized_filename for plan in plans] == [
        "CPM62.COM",
        "CBIOS61.COM",
        "CONFIG",
    ]
    assert [entry.normalized_filename for entry in read_directory(DiskImage(output))] == [
        "CPM62.COM",
        "CBIOS61.COM",
        "CBIOS61.COM",
        "CONFIG",
    ]
    assert read_file(output, "CPM62.COM")[:129] == first.read_bytes()
    assert read_file(output, "CBIOS61.COM")[: second.stat().st_size] == second.read_bytes()
    assert read_file(output, "CONFIG") == b""
    assert verify_image(output).is_valid
    assert sha256(blank_image.read_bytes()).digest() == before


def test_put_files_duplicate_batch_uses_last_file(
    blank_image: Path, tmp_path: Path
) -> None:
    first = _host_file(tmp_path, 1, "same.com")
    second_dir = tmp_path / "other"
    second_dir.mkdir()
    second = _host_file(second_dir, 2, "SAME.COM")
    output = tmp_path / "duplicate.hda"

    plans = put_files(blank_image, (first, second), output)
    assert len(plans) == 2
    assert not plans[0].replaced_directory_indices
    assert plans[1].replaced_directory_indices == plans[0].directory_indices
    assert read_file(output, "SAME.COM")[:2] == second.read_bytes()


def test_same_filename_can_be_stored_and_selected_in_different_user_areas(
    blank_image: Path, tmp_path: Path
) -> None:
    user_zero = _host_file(tmp_path, 1, "SAME.COM")
    first = tmp_path / "user-zero.hda"
    put_file(blank_image, user_zero, first, user_number=0)
    other_dir = tmp_path / "other-user"
    other_dir.mkdir()
    user_four = _host_file(other_dir, 2, "SAME.COM")
    output = tmp_path / "users.hda"

    plan = put_file(first, user_four, output, user_number=4)

    assert plan.user_number == 4
    assert read_file(output, "SAME.COM", user_number=0)[:1] == user_zero.read_bytes()
    assert read_file(output, "SAME.COM", user_number=4)[:2] == user_four.read_bytes()
    with pytest.raises(DuplicateFileError, match="ambiguous across user numbers"):
        read_file(output, "SAME.COM")


@pytest.mark.parametrize("user_number", [-1, 16])
def test_put_rejects_invalid_user_area(
    blank_image: Path, tmp_path: Path, user_number: int
) -> None:
    host = _host_file(tmp_path, 1)
    with pytest.raises(ValueError, match="between 0 and 15"):
        put_file(blank_image, host, tmp_path / "invalid-user.hda", user_number=user_number)


def test_put_files_replaces_existing_files_and_adds_new_files_atomically(
    blank_image: Path, tmp_path: Path
) -> None:
    old_first = _host_file(tmp_path, 5000, "FIRST.COM")
    old_second = _host_file(tmp_path, 5000, "SECOND.COM")
    populated = tmp_path / "populated.hda"
    old_plans = put_files(blank_image, (old_first, old_second), populated)
    replacements = tmp_path / "replacements"
    replacements.mkdir()
    new_first = _host_file(replacements, 1, "FIRST.COM")
    new_third = _host_file(replacements, 129, "THIRD.COM")
    output = tmp_path / "updated.hda"

    plans = put_files(populated, (new_first, new_third), output, replace=True)

    assert plans[0].replaced_directory_indices == old_plans[0].directory_indices
    assert plans[1].replaced_directory_indices == ()
    assert read_file(output, "FIRST.COM")[:1] == new_first.read_bytes()
    assert read_file(output, "SECOND.COM")[:5000] == old_second.read_bytes()
    assert read_file(output, "THIRD.COM")[:129] == new_third.read_bytes()
    assert verify_image(output).is_valid


@pytest.mark.parametrize(
    "name",
    ["", ".", "TOOLONGER.COM", "OK.TOOLONG", "TWO.DOT.S", "BAD NAME.COM", "BAD?.COM", "é.COM"],
)
def test_invalid_cpm_names_are_rejected(name: str) -> None:
    with pytest.raises(FilenameError):
        normalize_cpm_filename(name)


def test_filename_normalization_is_case_insensitive() -> None:
    assert normalize_cpm_filename("hello.com") == "HELLO.COM"
    assert normalize_cpm_filename("readme") == "README"


def _directory_entry(name: str, records: int, blocks: tuple[int, ...]) -> bytes:
    if records > 128:
        extent = 1
        rc = records - 128
    else:
        extent = 0
        rc = records
    allocation = b"".join(block.to_bytes(2, "little") for block in blocks).ljust(16, b"\x00")
    return (
        b"\x00"
        + name.encode("ascii").ljust(8, b" ")
        + b"DAT"
        + bytes([extent, 0, 0, rc])
        + allocation
    )


def test_insufficient_free_blocks_is_rejected(blank_image: Path, tmp_path: Path) -> None:
    blocks = list(range(constants.FIRST_USABLE_ALLOCATION_BLOCK, constants.DPB_MAXIMUM_BLOCK + 1))
    entries: list[bytes] = []
    for position in range(0, len(blocks), constants.ALLOCATION_VALUES_PER_ENTRY):
        group = tuple(blocks[position : position + constants.ALLOCATION_VALUES_PER_ENTRY])
        records = len(group) * constants.RECORDS_PER_ALLOCATION_BLOCK
        entries.append(_directory_entry(f"F{len(entries):07d}", records, group))
    with blank_image.open("r+b") as stream:
        stream.seek(constants.DIRECTORY_START_LBA * constants.SECTOR_SIZE)
        stream.write(b"".join(entries))
    assert verify_image(blank_image).is_valid
    host = _host_file(tmp_path, 1)
    with pytest.raises(AllocationError, match="insufficient free space"):
        put_file(blank_image, host, tmp_path / "full.hda", cpm_filename="NEW.DAT")


def test_full_directory_is_rejected(blank_image: Path, tmp_path: Path) -> None:
    entries = [
        b"\x00" + f"F{index:07d}".encode("ascii") + b"   " + bytes(20)
        for index in range(constants.DIRECTORY_ENTRY_COUNT)
    ]
    with blank_image.open("r+b") as stream:
        stream.seek(constants.DIRECTORY_START_LBA * constants.SECTOR_SIZE)
        stream.write(b"".join(entries))
    assert verify_image(blank_image).is_valid
    host = _host_file(tmp_path, 0)
    with pytest.raises(AllocationError, match="directory is full"):
        put_file(blank_image, host, tmp_path / "full.hda", cpm_filename="NEW")


def test_delete_multi_extent_and_reuse_blocks(blank_image: Path, tmp_path: Path) -> None:
    host = _host_file(tmp_path, constants.DIRECTORY_EXTENT_SIZE + 1)
    first = tmp_path / "first.hda"
    original_plan = put_file(blank_image, host, first, cpm_filename="REMOVE.DAT")
    data_before_delete = [
        DiskImage(first).read_range(
            (constants.DIRECTORY_START_LBA + block * constants.ALLOCATION_BLOCK_SECTORS)
            * constants.SECTOR_SIZE,
            constants.ALLOCATION_BLOCK_SIZE,
        )
        for block in original_plan.allocation_blocks
    ]
    deleted = tmp_path / "deleted.hda"
    delete_file(first, "remove.dat", deleted)
    assert verify_image(deleted).is_valid
    with pytest.raises(CPMFileNotFoundError):
        read_file(deleted, "REMOVE.DAT")
    for block, expected in zip(original_plan.allocation_blocks, data_before_delete, strict=True):
        assert DiskImage(deleted).read_range(
            (constants.DIRECTORY_START_LBA + block * constants.ALLOCATION_BLOCK_SECTORS)
            * constants.SECTOR_SIZE,
            constants.ALLOCATION_BLOCK_SIZE,
        ) == expected

    replacement_host = _host_file(tmp_path, 128, "replacement.bin")
    reused = tmp_path / "reused.hda"
    replacement_plan = put_file(deleted, replacement_host, reused, cpm_filename="NEW.COM")
    assert replacement_plan.allocation_blocks[0] == original_plan.allocation_blocks[0]


def test_delete_missing_file_fails_without_output(blank_image: Path, tmp_path: Path) -> None:
    output = tmp_path / "deleted.hda"
    with pytest.raises(CPMFileNotFoundError):
        delete_file(blank_image, "MISSING.COM", output)
    assert not output.exists()


def test_put_preserves_system_and_every_unrelated_byte(blank_image: Path, tmp_path: Path) -> None:
    with blank_image.open("r+b") as stream:
        stream.seek(0)
        system = bytearray(bytes(range(256)) * constants.SYSTEM_AREA_SECTOR_COUNT)
        dpb_offset = constants.DPB_REFERENCE_OFFSET
        system[dpb_offset : dpb_offset + 15] = (
            constants.DPB_SECTORS_PER_TRACK.to_bytes(2, "little")
            + bytes(
                [
                    constants.DPB_BLOCK_SHIFT,
                    constants.DPB_BLOCK_MASK,
                    constants.DPB_EXTENT_MASK,
                ]
            )
            + constants.DPB_MAXIMUM_BLOCK.to_bytes(2, "little")
            + constants.DPB_MAXIMUM_DIRECTORY_ENTRY.to_bytes(2, "little")
            + bytes(constants.DPB_ALLOCATION_RESERVED)
            + constants.DPB_DIRECTORY_CHECK_SIZE.to_bytes(2, "little")
            + constants.DPB_RESERVED_TRACKS.to_bytes(2, "little")
        )
        stream.write(system)
        stream.seek(500 * constants.SECTOR_SIZE)
        stream.write(b"unrelated evidence")
    before = blank_image.read_bytes()
    host = _host_file(tmp_path, 129)
    output = tmp_path / "preserved.hda"
    plan = put_file(blank_image, host, output, cpm_filename="SAFE.DAT")
    after = output.read_bytes()
    assert after[: constants.SYSTEM_AREA_SIZE] == before[: constants.SYSTEM_AREA_SIZE]
    directory_offset = constants.DIRECTORY_START_LBA * constants.SECTOR_SIZE
    block_offset = (
        constants.DIRECTORY_START_LBA
        + plan.allocation_blocks[0] * constants.ALLOCATION_BLOCK_SECTORS
    ) * constants.SECTOR_SIZE
    assert after[:directory_offset] == before[:directory_offset]
    assert after[directory_offset + 32 : block_offset] == before[directory_offset + 32 : block_offset]
    assert after[block_offset + constants.ALLOCATION_BLOCK_SIZE :] == before[
        block_offset + constants.ALLOCATION_BLOCK_SIZE :
    ]


def test_source_immutability_and_output_overwrite_rules(blank_image: Path, tmp_path: Path) -> None:
    host = _host_file(tmp_path, 128)
    before_hash = sha256(blank_image.read_bytes()).digest()
    output = tmp_path / "output.hda"
    output.write_bytes(b"keep")
    put_file(blank_image, host, output, cpm_filename="FILE.DAT")
    assert output.stat().st_size == constants.IMAGE_SIZE
    output.write_bytes(b"keep")
    with pytest.raises(FileExistsError):
        put_file(blank_image, host, output, cpm_filename="FILE.DAT", overwrite=False)
    assert output.read_bytes() == b"keep"
    assert sha256(blank_image.read_bytes()).digest() == before_hash


def test_put_can_atomically_modify_source_image_in_place(
    blank_image: Path, tmp_path: Path
) -> None:
    host = _host_file(tmp_path, 1)
    put_file(blank_image, host, cpm_filename="FILE.DAT")
    assert read_file(blank_image, "FILE.DAT")[:1] == host.read_bytes()
    replacement = _host_file(tmp_path, 2, "replacement.bin")
    plan = put_file(blank_image, replacement, cpm_filename="FILE.DAT")
    assert plan.replaced_directory_indices
    assert read_file(blank_image, "FILE.DAT")[:2] == replacement.read_bytes()
    assert verify_image(blank_image).is_valid


def test_atomic_cleanup_after_commit_failure(
    blank_image: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    host = _host_file(tmp_path, 128)
    output = tmp_path / "output.hda"
    before_hash = sha256(blank_image.read_bytes()).digest()

    def fail_replace(source: os.PathLike[str] | str, destination: os.PathLike[str] | str) -> None:
        raise OSError("simulated commit failure")

    monkeypatch.setattr("p2000c_disk.filesystem.os.replace", fail_replace)
    with pytest.raises(OSError, match="simulated commit failure"):
        put_file(blank_image, host, output, cpm_filename="FILE.DAT")
    assert not output.exists()
    assert not any(path.suffix == ".tmp" for path in tmp_path.iterdir())
    assert sha256(blank_image.read_bytes()).digest() == before_hash


def test_plan_does_not_modify_image(blank_image: Path) -> None:
    before = sha256(blank_image.read_bytes()).digest()
    plan = plan_put(DiskImage(blank_image), "PLAN.DAT", _data(129))
    assert plan.allocation_blocks == (4,)
    assert sha256(blank_image.read_bytes()).digest() == before
