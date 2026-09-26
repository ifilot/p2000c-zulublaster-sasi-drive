"""Read-only consistency checking for the confirmed P2000C CP/M layout."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from . import constants
from .directory import DirectoryEntry, DirectoryFormatError, parse_directory_entry
from .image import DiskImage, ImageFormatError
from .layout import (
    LayoutDetectionError,
    PartitionLayout,
    detect_image_layout,
)


@dataclass(frozen=True, slots=True)
class VerificationIssue:
    code: str
    message: str
    entry_indices: tuple[int, ...] = ()


@dataclass(frozen=True, slots=True)
class VerificationReport:
    path: str
    image_size: int | None
    active_entry_count: int
    file_count: int
    errors: tuple[VerificationIssue, ...]
    warnings: tuple[VerificationIssue, ...]
    layout_mode: str | None = None
    partitions: tuple[str, ...] = ()

    @property
    def is_valid(self) -> bool:
        return not self.errors


class ConsistencyError(ValueError):
    """Raised when an image fails filesystem consistency verification."""

    def __init__(self, report: VerificationReport) -> None:
        self.report = report
        details = "; ".join(issue.message for issue in report.errors[:3])
        if len(report.errors) > 3:
            details += f"; and {len(report.errors) - 3} more error(s)"
        super().__init__(f"filesystem verification failed: {details}")


def _issue(
    errors: list[VerificationIssue],
    code: str,
    message: str,
    *entry_indices: int,
) -> None:
    errors.append(VerificationIssue(code, message, tuple(entry_indices)))


def _verify_entry(
    entry: DirectoryEntry,
    errors: list[VerificationIssue],
    partition: PartitionLayout,
) -> None:
    if entry.user_number > 15:
        _issue(
            errors,
            "invalid-user-number",
            f"entry {entry.index} has CP/M user number {entry.user_number}; expected 0-15",
            entry.index,
        )
    if entry.extent > 31:
        _issue(
            errors,
            "invalid-extent-field",
            f"entry {entry.index} has extent byte {entry.extent}; high bits must be clear",
            entry.index,
        )
    if entry.s1 != 0:
        _issue(
            errors,
            "invalid-s1-field",
            f"entry {entry.index} has reserved S1 value {entry.s1}",
            entry.index,
        )
    if entry.record_count > constants.LOGICAL_EXTENT_RECORDS:
        _issue(
            errors,
            "impossible-record-count",
            f"entry {entry.index} has record count {entry.record_count}; maximum is 128",
            entry.index,
        )

    allocations = entry.allocation_values
    saw_zero = False
    nonzero: list[int] = []
    for slot, block in enumerate(allocations):
        if block == 0:
            saw_zero = True
            continue
        nonzero.append(block)
        if saw_zero:
            _issue(
                errors,
                "allocation-gap",
                f"entry {entry.index} has non-zero block {block} after an empty allocation slot",
                entry.index,
            )
        if block in partition.reserved_allocation_blocks:
            _issue(
                errors,
                "reserved-block-reference",
                f"entry {entry.index} allocation slot {slot} references reserved block {block}",
                entry.index,
            )
        if block > partition.maximum_block:
            _issue(
                errors,
                "out-of-range-block",
                f"entry {entry.index} allocation slot {slot} references block {block}, "
                f"above DSM {partition.maximum_block}",
                entry.index,
            )
        end_lba = (
            partition.directory_start_lba
            + (block + 1) * constants.ALLOCATION_BLOCK_SECTORS
            - 1
        )
        if end_lba >= constants.SECTOR_COUNT:
            _issue(
                errors,
                "data-beyond-image",
                f"entry {entry.index} block {block} ends at LBA {end_lba}, beyond the image",
                entry.index,
            )

    if entry.record_count <= constants.LOGICAL_EXTENT_RECORDS:
        records = entry.extent_record_count
        if records > constants.DIRECTORY_EXTENT_RECORDS:
            _issue(
                errors,
                "impossible-extent-size",
                f"entry {entry.index} implies {records} records; maximum is "
                f"{constants.DIRECTORY_EXTENT_RECORDS}",
                entry.index,
            )
        expected_blocks = (
            records + constants.RECORDS_PER_ALLOCATION_BLOCK - 1
        ) // constants.RECORDS_PER_ALLOCATION_BLOCK
        if len(nonzero) != expected_blocks:
            _issue(
                errors,
                "allocation-count-mismatch",
                f"entry {entry.index} implies {records} records and {expected_blocks} block(s), "
                f"but references {len(nonzero)}",
                entry.index,
            )


def _prefix_issues(
    issues: list[VerificationIssue], partition: PartitionLayout
) -> list[VerificationIssue]:
    if partition.name == "single":
        return issues
    return [
        VerificationIssue(
            issue.code,
            f"{partition.name} partition: {issue.message}",
            issue.entry_indices,
        )
        for issue in issues
    ]


def _verify_partition(
    image: DiskImage, partition: PartitionLayout
) -> tuple[list[DirectoryEntry], list[VerificationIssue]]:
    entries: list[DirectoryEntry] = []
    errors: list[VerificationIssue] = []
    directory_offset = partition.directory_start_lba * constants.SECTOR_SIZE
    directory = image.read_range(directory_offset, constants.DIRECTORY_SIZE)
    for index in range(constants.DIRECTORY_ENTRY_COUNT):
        start = index * constants.DIRECTORY_ENTRY_SIZE
        raw = directory[start : start + constants.DIRECTORY_ENTRY_SIZE]
        try:
            entry = parse_directory_entry(
                raw, index, directory_start_lba=partition.directory_start_lba
            )
        except DirectoryFormatError as exc:
            _issue(errors, "malformed-directory-entry", str(exc), index)
            continue
        if entry is not None:
            entries.append(entry)
            _verify_entry(entry, errors, partition)

    by_file: dict[tuple[int, str], list[DirectoryEntry]] = defaultdict(list)
    block_owners: dict[int, DirectoryEntry] = {}
    for entry in entries:
        by_file[entry.identity].append(entry)
        for block in entry.allocation_values:
            if block == 0 or block > partition.maximum_block:
                continue
            previous = block_owners.get(block)
            if previous is not None:
                if previous.identity == entry.identity:
                    message = (
                        f"block {block} is referenced by multiple extents of "
                        f"user {entry.user_number} {entry.normalized_filename}"
                    )
                else:
                    message = (
                        f"block {block} is shared by user {previous.user_number} "
                        f"{previous.normalized_filename} and user {entry.user_number} "
                        f"{entry.normalized_filename}"
                    )
                _issue(
                    errors,
                    "overlapping-allocation",
                    message,
                    previous.index,
                    entry.index,
                )
            else:
                block_owners[block] = entry

    for (user, filename), file_entries in by_file.items():
        ordered = sorted(file_entries, key=lambda item: item.directory_extent_number)
        groups = [entry.directory_extent_number for entry in ordered]
        if len(groups) != len(set(groups)):
            duplicates = sorted(group for group in set(groups) if groups.count(group) > 1)
            _issue(
                errors,
                "duplicate-extent-number",
                f"user {user} {filename} has duplicate directory extent(s): "
                f"{', '.join(map(str, duplicates))}",
                *(entry.index for entry in ordered),
            )
        expected = list(range(len(groups)))
        if groups != expected:
            _issue(
                errors,
                "missing-extent-sequence",
                f"user {user} {filename} has extent sequence {groups}; expected {expected}",
                *(entry.index for entry in ordered),
            )
        for entry in ordered[:-1]:
            if entry.extent_record_count != constants.DIRECTORY_EXTENT_RECORDS:
                _issue(
                    errors,
                    "short-nonfinal-extent",
                    f"entry {entry.index} is followed by another extent but contains only "
                    f"{entry.extent_record_count} of {constants.DIRECTORY_EXTENT_RECORDS} records",
                    entry.index,
                )
        if len(ordered) > 1 and ordered[-1].extent_record_count == 0:
            _issue(
                errors,
                "empty-final-extent",
                f"user {user} {filename} has an unnecessary empty final extent",
                ordered[-1].index,
            )
    return entries, _prefix_issues(errors, partition)


def verify_image(
    path: str | Path, partition: str | PartitionLayout | None = None
) -> VerificationReport:
    """Verify image and filesystem structure without opening it for writing."""
    image = DiskImage(path)
    try:
        size = image.size
    except ImageFormatError as exc:
        return VerificationReport(
            path=str(image.path),
            image_size=None,
            active_entry_count=0,
            file_count=0,
            errors=(VerificationIssue("image-access", str(exc)),),
            warnings=(),
        )
    if size != constants.IMAGE_SIZE:
        return VerificationReport(
            path=str(image.path),
            image_size=size,
            active_entry_count=0,
            file_count=0,
            errors=(
                VerificationIssue(
                    "invalid-image-size",
                    f"expected {constants.IMAGE_SIZE} bytes, got {size}",
                ),
            ),
            warnings=(),
        )

    all_entries: list[DirectoryEntry] = []
    errors: list[VerificationIssue] = []
    warnings: list[VerificationIssue] = []
    system_area = image.system_area()
    try:
        layout = detect_image_layout(system_area)
        if isinstance(partition, PartitionLayout):
            selected = layout.partition(partition.name)
            partitions = (selected,)
        elif partition is not None:
            partitions = (layout.partition(partition),)
        else:
            partitions = layout.partitions
    except LayoutDetectionError as exc:
        return VerificationReport(
            path=str(image.path),
            image_size=size,
            active_entry_count=0,
            file_count=0,
            errors=(VerificationIssue("unsupported-dpb", str(exc)),),
            warnings=(),
        )
    if layout.assumed_from_blank_system:
        warnings.append(
            VerificationIssue(
                "dpb-not-present",
                "blank system area contains no DPB; the confirmed single layout is assumed",
            )
        )
    file_identities: set[tuple[str, int, str]] = set()
    for selected in partitions:
        entries, partition_errors = _verify_partition(image, selected)
        all_entries.extend(entries)
        errors.extend(partition_errors)
        file_identities.update(
            (selected.name, entry.user_number, entry.normalized_filename)
            for entry in entries
        )

    return VerificationReport(
        path=str(image.path),
        image_size=size,
        active_entry_count=len(all_entries),
        file_count=len(file_identities),
        errors=tuple(errors),
        warnings=tuple(warnings),
        layout_mode=layout.mode,
        partitions=tuple(item.name for item in partitions),
    )


def require_valid_image(
    path: str | Path, partition: str | PartitionLayout | None = None
) -> VerificationReport:
    report = verify_image(path, partition)
    if not report.is_valid:
        raise ConsistencyError(report)
    return report
