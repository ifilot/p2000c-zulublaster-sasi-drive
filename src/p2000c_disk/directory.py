"""Read-only parsing of CP/M directory entries."""

from __future__ import annotations

from dataclasses import dataclass

from . import constants
from .image import DiskImage
from .layout import PartitionLayout, resolve_partition


class DirectoryFormatError(ValueError):
    """Raised for a malformed active directory entry."""


@dataclass(frozen=True, slots=True)
class DirectoryEntry:
    index: int
    image_offset: int
    user_number: int
    raw_filename: bytes
    raw_extension: bytes
    filename: str
    extension: str
    extent: int
    s1: int
    s2: int
    record_count: int
    allocation: bytes
    raw: bytes

    @property
    def normalized_filename(self) -> str:
        return f"{self.filename}.{self.extension}" if self.extension else self.filename

    @property
    def is_system(self) -> bool:
        """Whether CP/M's System attribute hides this extent from normal DIR."""
        return bool(self.raw_extension[1] & 0x80)

    @property
    def allocation_values(self) -> tuple[int, ...]:
        """Decode the eight DPB-confirmed little-endian 16-bit block values."""
        return tuple(
            int.from_bytes(self.allocation[offset : offset + 2], "little")
            for offset in range(0, len(self.allocation), 2)
        )

    @property
    def logical_extent_number(self) -> int:
        return (self.s2 << 5) | (self.extent & 0x1F)

    @property
    def directory_extent_number(self) -> int:
        return self.logical_extent_number // (constants.DPB_EXTENT_MASK + 1)

    @property
    def extent_record_count(self) -> int:
        return (
            (self.extent & constants.DPB_EXTENT_MASK)
            * constants.LOGICAL_EXTENT_RECORDS
            + self.record_count
        )

    @property
    def identity(self) -> tuple[int, str]:
        return self.user_number, self.normalized_filename


def _decode_name(raw: bytes, field: str, index: int) -> str:
    masked = bytes(value & 0x7F for value in raw)
    if any(value < 0x20 or value > 0x7E for value in masked):
        raise DirectoryFormatError(
            f"directory entry {index} has non-printable {field} bytes"
        )
    return masked.decode("ascii").rstrip(" ").upper()


def parse_directory_entry(
    raw: bytes,
    index: int = 0,
    *,
    directory_start_lba: int = constants.DIRECTORY_START_LBA,
) -> DirectoryEntry | None:
    if len(raw) != constants.DIRECTORY_ENTRY_SIZE:
        raise DirectoryFormatError(
            f"directory entry must be {constants.DIRECTORY_ENTRY_SIZE} bytes; got {len(raw)}"
        )
    if raw[0] == constants.UNUSED_DIRECTORY_USER:
        return None
    if raw[0] > 31:
        raise DirectoryFormatError(
            f"directory entry {index} has invalid user number 0x{raw[0]:02X}"
        )
    filename = _decode_name(raw[1:9], "filename", index)
    extension = _decode_name(raw[9:12], "extension", index)
    if not filename:
        raise DirectoryFormatError(f"directory entry {index} has an empty filename")
    return DirectoryEntry(
        index=index,
        image_offset=(
            directory_start_lba * constants.SECTOR_SIZE
            + index * constants.DIRECTORY_ENTRY_SIZE
        ),
        user_number=raw[0],
        raw_filename=raw[1:9],
        raw_extension=raw[9:12],
        filename=filename,
        extension=extension,
        extent=raw[12],
        s1=raw[13],
        s2=raw[14],
        record_count=raw[15],
        allocation=raw[16:32],
        raw=raw,
    )


def read_directory(
    image: DiskImage, partition: str | PartitionLayout | None = None
) -> tuple[DirectoryEntry, ...]:
    """Read one directory, requiring a choice when the image is split."""
    _, selected = resolve_partition(image.system_area(), partition)
    offset = selected.directory_start_lba * constants.SECTOR_SIZE
    data = image.read_range(offset, constants.DIRECTORY_SIZE)
    entries: list[DirectoryEntry] = []
    for index in range(constants.DIRECTORY_ENTRY_COUNT):
        start = index * constants.DIRECTORY_ENTRY_SIZE
        entry = parse_directory_entry(
            data[start : start + constants.DIRECTORY_ENTRY_SIZE],
            index,
            directory_start_lba=selected.directory_start_lba,
        )
        if entry is not None:
            entries.append(entry)
    return tuple(entries)
