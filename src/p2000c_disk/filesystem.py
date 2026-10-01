# SPDX-FileCopyrightText: 2026 P2000C SASI Distribution contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Safe, copy-on-write CP/M file operations for P2000C images."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
import os
from pathlib import Path
import shutil
import tempfile
from typing import Callable, Iterable

from . import constants
from .directory import DirectoryEntry, read_directory
from .image import DiskImage
from .layout import PartitionLayout, resolve_partition
from .verify import require_valid_image


class CPMFileSystemError(ValueError):
    """Base class for CP/M filesystem-operation errors."""


class FilenameError(CPMFileSystemError):
    """Raised for a filename that cannot be represented safely as CP/M 8.3."""


class AllocationError(CPMFileSystemError):
    """Raised when a safe allocation plan cannot be made."""


class CPMFileNotFoundError(CPMFileSystemError):
    """Raised when a requested CP/M file does not exist."""


class DuplicateFileError(CPMFileSystemError):
    """Raised when a CP/M file identity is duplicate or ambiguous."""


class MutationError(CPMFileSystemError):
    """Raised when copy-on-write safety validation fails."""


@dataclass(frozen=True, slots=True)
class CPMFile:
    user_number: int
    normalized_filename: str
    entries: tuple[DirectoryEntry, ...]
    record_count: int
    size: int
    allocation_blocks: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class PutPlan:
    user_number: int
    normalized_filename: str
    host_size: int
    record_count: int
    padded_record_size: int
    directory_indices: tuple[int, ...]
    allocation_blocks: tuple[int, ...]
    directory_entries: tuple[bytes, ...]
    block_payloads: tuple[bytes, ...]
    replaced_directory_indices: tuple[int, ...] = ()


_FORBIDDEN_FILENAME_CHARACTERS = frozenset('<>.,;:=?*[]/\\')
ByteRange = tuple[int, int]
Modifier = Callable[[Path], tuple[ByteRange, ...]]


def normalize_cpm_filename(value: str) -> str:
    """Normalize a host-supplied name without truncating or replacing bytes."""
    if not value or value in {".", ".."}:
        raise FilenameError("CP/M filename must not be empty")
    if value.count(".") > 1:
        raise FilenameError(f"invalid CP/M 8.3 filename {value!r}: too many periods")
    name, separator, extension = value.partition(".")
    if not name or len(name) > 8:
        raise FilenameError(
            f"invalid CP/M 8.3 filename {value!r}: name must contain 1-8 characters"
        )
    if separator and len(extension) > 3:
        raise FilenameError(
            f"invalid CP/M 8.3 filename {value!r}: extension must contain at most 3 characters"
        )
    if separator and not extension:
        raise FilenameError(f"invalid CP/M 8.3 filename {value!r}: empty extension")
    normalized = value.upper()
    try:
        normalized.encode("ascii")
    except UnicodeEncodeError as exc:
        raise FilenameError(f"invalid CP/M filename {value!r}: ASCII characters are required") from exc
    for character in normalized.replace(".", ""):
        if not 0x21 <= ord(character) <= 0x7E or character in _FORBIDDEN_FILENAME_CHARACTERS:
            raise FilenameError(
                f"invalid CP/M filename {value!r}: unsupported character {character!r}"
            )
    return normalized


def _group_files(entries: Iterable[DirectoryEntry]) -> tuple[CPMFile, ...]:
    grouped: dict[tuple[int, str], list[DirectoryEntry]] = defaultdict(list)
    for entry in entries:
        grouped[entry.identity].append(entry)
    files: list[CPMFile] = []
    for (user, filename), related in grouped.items():
        ordered = tuple(sorted(related, key=lambda item: item.directory_extent_number))
        records = sum(entry.extent_record_count for entry in ordered)
        blocks = tuple(
            block
            for entry in ordered
            for block in entry.allocation_values
            if block != 0
        )
        files.append(
            CPMFile(
                user_number=user,
                normalized_filename=filename,
                entries=ordered,
                record_count=records,
                size=records * constants.LOGICAL_RECORD_SIZE,
                allocation_blocks=blocks,
            )
        )
    return tuple(sorted(files, key=lambda item: (item.user_number, item.normalized_filename)))


def _selected_partition(
    image: DiskImage, partition: str | PartitionLayout | None
) -> PartitionLayout:
    return resolve_partition(image.system_area(), partition)[1]


def list_files(
    image: str | Path | DiskImage,
    partition: str | PartitionLayout | None = None,
) -> tuple[CPMFile, ...]:
    disk = image if isinstance(image, DiskImage) else DiskImage(image)
    selected = _selected_partition(disk, partition)
    require_valid_image(disk.path, selected)
    return _group_files(read_directory(disk, selected))


def _select_file(
    image: DiskImage,
    requested_name: str,
    partition: str | PartitionLayout | None = None,
    user_number: int | None = None,
) -> CPMFile:
    normalized = normalize_cpm_filename(requested_name)
    matches = [
        file
        for file in list_files(image, partition)
        if file.normalized_filename.casefold() == normalized.casefold()
        and (user_number is None or file.user_number == user_number)
    ]
    if not matches:
        raise CPMFileNotFoundError(f"CP/M file not found: {normalized}")
    identities = {(file.user_number, file.normalized_filename) for file in matches}
    if len(identities) > 1:
        users = ", ".join(str(file.user_number) for file in matches)
        raise DuplicateFileError(
            f"CP/M filename {normalized} is ambiguous across user numbers: {users}"
        )
    return matches[0]


def read_file(
    image: str | Path | DiskImage,
    cpm_filename: str,
    *,
    partition: str | PartitionLayout | None = None,
    user_number: int | None = None,
) -> bytes:
    """Reconstruct all extents, returning CP/M's record-rounded file bytes."""
    disk = image if isinstance(image, DiskImage) else DiskImage(image)
    selected_partition = _selected_partition(disk, partition)
    selected = _select_file(disk, cpm_filename, selected_partition, user_number)
    output = bytearray()
    for entry in selected.entries:
        extent_data = bytearray()
        for block in entry.allocation_values:
            if block:
                extent_data.extend(
                    disk.read_range(
                        selected_partition.block_offset(block),
                        constants.ALLOCATION_BLOCK_SIZE,
                    )
                )
        required = entry.extent_record_count * constants.LOGICAL_RECORD_SIZE
        if len(extent_data) < required:
            raise CPMFileSystemError(
                f"entry {entry.index} provides {len(extent_data)} data bytes but "
                f"its record count requires {required}"
            )
        output.extend(extent_data[:required])
    return bytes(output)


def _destination_exists(path: Path) -> bool:
    return os.path.lexists(path)


def _same_path(source: Path, destination: Path) -> bool:
    try:
        source_resolved = source.resolve(strict=True)
    except OSError as exc:
        raise CPMFileSystemError(f"cannot access source image {source}: {exc}") from exc
    destination_resolved = destination.resolve(strict=False)
    return source_resolved == destination_resolved


def _atomic_write_host(path: Path, data: bytes, overwrite: bool = True) -> None:
    if _destination_exists(path) and not overwrite:
        raise FileExistsError(f"output file already exists: {path}")
    if not path.parent.is_dir():
        raise CPMFileSystemError(f"output directory does not exist: {path.parent}")
    temporary: Path | None = None
    try:
        descriptor, name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
        temporary = Path(name)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        if _destination_exists(path) and not overwrite:
            raise FileExistsError(f"output file already exists: {path}")
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None:
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass


def extract_file(
    image: str | Path,
    cpm_filename: str,
    output: str | Path | None = None,
    *,
    overwrite: bool = True,
    partition: str | PartitionLayout | None = None,
) -> Path:
    normalized = normalize_cpm_filename(cpm_filename)
    destination = Path(output) if output is not None else Path(normalized)
    data = read_file(image, normalized, partition=partition)
    _atomic_write_host(destination, data, overwrite)
    return destination


def _encode_directory_entry(
    user_number: int,
    normalized_filename: str,
    directory_extent: int,
    records: int,
    blocks: tuple[int, ...],
) -> bytes:
    name, separator, extension = normalized_filename.partition(".")
    if len(blocks) > constants.ALLOCATION_VALUES_PER_ENTRY:
        raise AllocationError("internal allocation plan exceeds one directory entry")
    if not 0 <= records <= constants.DIRECTORY_EXTENT_RECORDS:
        raise AllocationError(f"internal extent record count is invalid: {records}")
    logical_extent = directory_extent * (constants.DPB_EXTENT_MASK + 1)
    if records > constants.LOGICAL_EXTENT_RECORDS:
        logical_extent += 1
        record_count = records - constants.LOGICAL_EXTENT_RECORDS
    else:
        record_count = records
    if logical_extent > 0x1FFF:
        raise AllocationError("file requires an extent number beyond the CP/M directory format")
    allocation = b"".join(block.to_bytes(2, "little") for block in blocks)
    allocation += bytes(16 - len(allocation))
    return (
        bytes([user_number])
        + name.encode("ascii").ljust(8, b" ")
        + (extension if separator else "").encode("ascii").ljust(3, b" ")
        + bytes([logical_extent & 0x1F, 0, logical_extent >> 5, record_count])
        + allocation
    )


def _plan_with_free_space(
    user_number: int,
    normalized_filename: str,
    data: bytes,
    free_entries: tuple[int, ...],
    free_blocks: tuple[int, ...],
    *,
    replaced_directory_indices: tuple[int, ...] = (),
) -> PutPlan:
    """Build one plan from an already validated free-space snapshot."""
    records = (len(data) + constants.LOGICAL_RECORD_SIZE - 1) // constants.LOGICAL_RECORD_SIZE
    padded_record_size = records * constants.LOGICAL_RECORD_SIZE
    blocks_needed = (
        padded_record_size + constants.ALLOCATION_BLOCK_SIZE - 1
    ) // constants.ALLOCATION_BLOCK_SIZE
    extents_needed = max(
        1,
        (records + constants.DIRECTORY_EXTENT_RECORDS - 1)
        // constants.DIRECTORY_EXTENT_RECORDS,
    )

    if len(free_entries) < extents_needed:
        raise AllocationError(
            f"directory is full: need {extents_needed} free entries, found {len(free_entries)}"
        )

    if len(free_blocks) < blocks_needed:
        raise AllocationError(
            f"insufficient free space: need {blocks_needed} block(s), found {len(free_blocks)}"
        )
    chosen_blocks = free_blocks[:blocks_needed]

    record_padded = data + bytes([constants.RECORD_PADDING_BYTE]) * (
        padded_record_size - len(data)
    )
    block_padded = record_padded + bytes([constants.ALLOCATION_SLACK_FILL_BYTE]) * (
        blocks_needed * constants.ALLOCATION_BLOCK_SIZE - len(record_padded)
    )
    directory_entries: list[bytes] = []
    remaining_records = records
    block_position = 0
    for extent_number in range(extents_needed):
        extent_records = min(remaining_records, constants.DIRECTORY_EXTENT_RECORDS)
        extent_blocks = (
            extent_records + constants.RECORDS_PER_ALLOCATION_BLOCK - 1
        ) // constants.RECORDS_PER_ALLOCATION_BLOCK
        block_slice = chosen_blocks[block_position : block_position + extent_blocks]
        directory_entries.append(
            _encode_directory_entry(
                user_number,
                normalized_filename,
                extent_number,
                extent_records,
                block_slice,
            )
        )
        remaining_records -= extent_records
        block_position += extent_blocks

    payloads = tuple(
        block_padded[offset : offset + constants.ALLOCATION_BLOCK_SIZE]
        for offset in range(0, len(block_padded), constants.ALLOCATION_BLOCK_SIZE)
    )
    return PutPlan(
        user_number=user_number,
        normalized_filename=normalized_filename,
        host_size=len(data),
        record_count=records,
        padded_record_size=padded_record_size,
        directory_indices=free_entries[:extents_needed],
        allocation_blocks=chosen_blocks,
        directory_entries=tuple(directory_entries),
        block_payloads=payloads,
        replaced_directory_indices=replaced_directory_indices,
    )


def _free_space(
    image: DiskImage,
    entries: tuple[DirectoryEntry, ...],
    partition: PartitionLayout,
    *,
    released_entries: tuple[DirectoryEntry, ...] = (),
) -> tuple[tuple[int, ...], tuple[int, ...]]:
    directory_offset = partition.directory_start_lba * constants.SECTOR_SIZE
    directory = image.read_range(directory_offset, constants.DIRECTORY_SIZE)
    released_indices = {entry.index for entry in released_entries}
    free_entries = tuple(
        index
        for index in range(constants.DIRECTORY_ENTRY_COUNT)
        if (
            directory[index * constants.DIRECTORY_ENTRY_SIZE]
            == constants.UNUSED_DIRECTORY_USER
            or index in released_indices
        )
    )
    used_blocks = {
        block
        for entry in entries
        for block in entry.allocation_values
        if block != 0
    }
    unavailable = used_blocks | set(partition.reserved_allocation_blocks)
    free_blocks = tuple(
        block
        for block in range(
            partition.first_usable_allocation_block,
            partition.maximum_block + 1,
        )
        if block not in unavailable
    )
    return free_entries, free_blocks


def plan_put(
    image: DiskImage,
    normalized_filename: str,
    data: bytes,
    *,
    replace: bool = True,
    partition: str | PartitionLayout | None = None,
    user_number: int = 0,
) -> PutPlan:
    """Plan directory and block changes without modifying an image."""
    selected = _selected_partition(image, partition)
    require_valid_image(image.path, selected)
    if not 0 <= user_number <= 15:
        raise CPMFileSystemError("CP/M user number must be between 0 and 15")
    normalized = normalize_cpm_filename(normalized_filename)
    entries = read_directory(image, selected)
    replaced = tuple(entry for entry in entries if entry.identity == (user_number, normalized))
    if replaced and not replace:
        raise DuplicateFileError(
            f"user {user_number} already contains CP/M file {normalized}; use replace=True to replace it"
        )
    retained = tuple(entry for entry in entries if entry not in replaced)
    free_entries, free_blocks = _free_space(
        image, retained, selected, released_entries=replaced
    )
    return _plan_with_free_space(
        user_number,
        normalized,
        data,
        free_entries,
        free_blocks,
        replaced_directory_indices=tuple(entry.index for entry in replaced),
    )


def plan_put_many(
    image: DiskImage,
    files: Iterable[tuple[str, bytes]],
    *,
    replace: bool = True,
    partition: str | PartitionLayout | None = None,
    user_number: int = 0,
) -> tuple[PutPlan, ...]:
    """Plan ordered additions against one immutable image snapshot."""
    requested = tuple((normalize_cpm_filename(name), data) for name, data in files)
    if not requested:
        raise CPMFileSystemError("at least one host file is required")

    selected = _selected_partition(image, partition)
    require_valid_image(image.path, selected)
    if not 0 <= user_number <= 15:
        raise CPMFileSystemError("CP/M user number must be between 0 and 15")
    entries = read_directory(image, selected)
    resources_by_identity: dict[
        tuple[int, str], tuple[tuple[int, ...], tuple[int, ...]]
    ] = {
        identity: (
            tuple(entry.index for entry in entries if entry.identity == identity),
            tuple(
                block
                for entry in entries
                if entry.identity == identity
                for block in entry.allocation_values
                if block
            ),
        )
        for identity in {entry.identity for entry in entries}
    }
    free_entries, free_blocks = _free_space(image, entries, selected)
    plans: list[PutPlan] = []
    for normalized, data in requested:
        identity = (user_number, normalized)
        replaced_indices, replaced_blocks = resources_by_identity.get(identity, ((), ()))
        if replaced_indices and not replace:
            raise DuplicateFileError(
                f"user {user_number} already contains CP/M file {normalized}; use replace=True to replace it"
            )
        if replaced_indices:
            free_entries = tuple(sorted((*free_entries, *replaced_indices)))
            free_blocks = tuple(sorted((*free_blocks, *replaced_blocks)))
        plan = _plan_with_free_space(
            user_number,
            normalized,
            data,
            free_entries,
            free_blocks,
            replaced_directory_indices=replaced_indices,
        )
        plans.append(plan)
        free_entries = free_entries[len(plan.directory_indices) :]
        free_blocks = free_blocks[len(plan.allocation_blocks) :]
        resources_by_identity[identity] = (
            plan.directory_indices,
            plan.allocation_blocks,
        )
    return tuple(plans)


def _offset_allowed(offset: int, allowed: tuple[ByteRange, ...]) -> bool:
    return any(start <= offset < end for start, end in allowed)


def _copy_on_write(
    source: Path,
    output: Path,
    modifier: Modifier,
    *,
    overwrite: bool,
) -> Path:
    require_valid_image(source)
    in_place = _same_path(source, output)
    destination = source.resolve(strict=True) if in_place else output
    if _destination_exists(destination) and not overwrite:
        raise FileExistsError(f"output file already exists: {destination}")
    if not destination.parent.is_dir():
        raise CPMFileSystemError(f"output directory does not exist: {destination.parent}")
    source_data = DiskImage(source).read_range(0, constants.IMAGE_SIZE)
    temporary: Path | None = None
    try:
        descriptor, name = tempfile.mkstemp(
            prefix=f".{destination.name}.", suffix=".tmp", dir=destination.parent
        )
        temporary = Path(name)
        with source.open("rb") as source_stream, os.fdopen(descriptor, "wb") as target_stream:
            shutil.copyfileobj(source_stream, target_stream, length=1024 * 1024)
            target_stream.flush()
            os.fsync(target_stream.fileno())
        allowed = modifier(temporary)
        require_valid_image(temporary)
        result_data = DiskImage(temporary).read_range(0, constants.IMAGE_SIZE)
        changed_outside = next(
            (
                offset
                for offset, (before, after) in enumerate(zip(source_data, result_data, strict=True))
                if before != after and not _offset_allowed(offset, allowed)
            ),
            None,
        )
        if changed_outside is not None:
            raise MutationError(
                f"copy-on-write changed unrelated byte offset {changed_outside}"
            )
        if result_data[: constants.SYSTEM_AREA_SIZE] != source_data[: constants.SYSTEM_AREA_SIZE]:
            raise MutationError("protected system area changed during mutation")
        if _destination_exists(destination) and not overwrite:
            raise FileExistsError(f"output file already exists: {destination}")
        os.replace(temporary, destination)
        temporary = None
        return output
    finally:
        if temporary is not None:
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass


def put_file(
    image: str | Path,
    host_file: str | Path,
    output: str | Path | None = None,
    *,
    cpm_filename: str | None = None,
    overwrite: bool = True,
    replace: bool = True,
    partition: str | PartitionLayout | None = None,
    user_number: int = 0,
) -> PutPlan:
    source = Path(image)
    host = Path(host_file)
    try:
        data = host.read_bytes()
    except OSError as exc:
        raise CPMFileSystemError(f"cannot read host file {host}: {exc}") from exc
    normalized = normalize_cpm_filename(cpm_filename if cpm_filename is not None else host.name)
    disk = DiskImage(source)
    selected_partition = _selected_partition(disk, partition)
    plan = plan_put(
        disk, normalized, data, replace=replace, partition=selected_partition,
        user_number=user_number,
    )

    def apply(temporary: Path) -> tuple[ByteRange, ...]:
        allowed: list[ByteRange] = []
        with temporary.open("r+b") as stream:
            for block, payload in zip(plan.allocation_blocks, plan.block_payloads, strict=True):
                offset = selected_partition.block_offset(block)
                stream.seek(offset)
                stream.write(payload)
                allowed.append((offset, offset + constants.ALLOCATION_BLOCK_SIZE))
            for index, entry_bytes in zip(
                plan.directory_indices, plan.directory_entries, strict=True
            ):
                offset = (
                    selected_partition.directory_start_lba * constants.SECTOR_SIZE
                    + index * constants.DIRECTORY_ENTRY_SIZE
                )
                stream.seek(offset)
                stream.write(entry_bytes)
                allowed.append((offset, offset + constants.DIRECTORY_ENTRY_SIZE))
            for index in sorted(
                set(plan.replaced_directory_indices) - set(plan.directory_indices)
            ):
                offset = (
                    selected_partition.directory_start_lba * constants.SECTOR_SIZE
                    + index * constants.DIRECTORY_ENTRY_SIZE
                )
                stream.seek(offset)
                stream.write(bytes([constants.UNUSED_DIRECTORY_USER]))
                allowed.append((offset, offset + 1))
            stream.flush()
            os.fsync(stream.fileno())
        return tuple(allowed)

    _copy_on_write(
        source, Path(output) if output is not None else source, apply, overwrite=overwrite
    )
    return plan


def put_files(
    image: str | Path,
    host_files: Iterable[str | Path],
    output: str | Path | None = None,
    *,
    overwrite: bool = True,
    replace: bool = True,
    partition: str | PartitionLayout | None = None,
    user_number: int = 0,
) -> tuple[PutPlan, ...]:
    """Add host files in order using one copy-on-write transaction."""
    source = Path(image)
    requested: list[tuple[str, bytes]] = []
    for host_file in host_files:
        host = Path(host_file)
        try:
            data = host.read_bytes()
        except OSError as exc:
            raise CPMFileSystemError(f"cannot read host file {host}: {exc}") from exc
        requested.append((host.name, data))
    disk = DiskImage(source)
    selected_partition = _selected_partition(disk, partition)
    plans = plan_put_many(
        disk, requested, replace=replace, partition=selected_partition,
        user_number=user_number,
    )

    def apply(temporary: Path) -> tuple[ByteRange, ...]:
        allowed: list[ByteRange] = []
        with temporary.open("r+b") as stream:
            for plan in plans:
                for block, payload in zip(
                    plan.allocation_blocks, plan.block_payloads, strict=True
                ):
                    offset = selected_partition.block_offset(block)
                    stream.seek(offset)
                    stream.write(payload)
                    allowed.append((offset, offset + constants.ALLOCATION_BLOCK_SIZE))
                for index, entry_bytes in zip(
                    plan.directory_indices, plan.directory_entries, strict=True
                ):
                    offset = (
                        selected_partition.directory_start_lba * constants.SECTOR_SIZE
                        + index * constants.DIRECTORY_ENTRY_SIZE
                    )
                    stream.seek(offset)
                    stream.write(entry_bytes)
                    allowed.append((offset, offset + constants.DIRECTORY_ENTRY_SIZE))
                for index in sorted(
                    set(plan.replaced_directory_indices) - set(plan.directory_indices)
                ):
                    offset = (
                        selected_partition.directory_start_lba * constants.SECTOR_SIZE
                        + index * constants.DIRECTORY_ENTRY_SIZE
                    )
                    stream.seek(offset)
                    stream.write(bytes([constants.UNUSED_DIRECTORY_USER]))
                    allowed.append((offset, offset + 1))
            stream.flush()
            os.fsync(stream.fileno())
        return tuple(allowed)

    _copy_on_write(
        source, Path(output) if output is not None else source, apply, overwrite=overwrite
    )
    return plans


def set_system_attribute(
    image: str | Path,
    cpm_filename: str,
    output: str | Path | None = None,
    *,
    enabled: bool = True,
    overwrite: bool = True,
    partition: str | PartitionLayout | None = None,
    user_number: int | None = None,
) -> CPMFile:
    """Set CP/M's System bit on every extent of one file."""
    source = Path(image)
    disk = DiskImage(source)
    selected_partition = _selected_partition(disk, partition)
    selected = _select_file(
        disk, cpm_filename, selected_partition, user_number=user_number
    )

    def apply(temporary: Path) -> tuple[ByteRange, ...]:
        changed: list[ByteRange] = []
        with temporary.open("r+b") as stream:
            for entry in selected.entries:
                offset = entry.image_offset + 10
                value = entry.raw_extension[1]
                value = value | 0x80 if enabled else value & 0x7F
                stream.seek(offset)
                stream.write(bytes([value]))
                changed.append((offset, offset + 1))
            stream.flush()
            os.fsync(stream.fileno())
        return tuple(changed)

    _copy_on_write(
        source, Path(output) if output is not None else source, apply,
        overwrite=overwrite,
    )
    return selected


def delete_file(
    image: str | Path,
    cpm_filename: str,
    output: str | Path | None = None,
    *,
    overwrite: bool = True,
    partition: str | PartitionLayout | None = None,
) -> CPMFile:
    source = Path(image)
    disk = DiskImage(source)
    selected_partition = _selected_partition(disk, partition)
    selected = _select_file(disk, cpm_filename, selected_partition)

    def apply(temporary: Path) -> tuple[ByteRange, ...]:
        allowed: list[ByteRange] = []
        with temporary.open("r+b") as stream:
            for entry in selected.entries:
                stream.seek(entry.image_offset)
                stream.write(bytes([constants.UNUSED_DIRECTORY_USER]))
                allowed.append((entry.image_offset, entry.image_offset + 1))
            stream.flush()
            os.fsync(stream.fileno())
        return tuple(allowed)

    _copy_on_write(
        source, Path(output) if output is not None else source, apply, overwrite=overwrite
    )
    return selected
