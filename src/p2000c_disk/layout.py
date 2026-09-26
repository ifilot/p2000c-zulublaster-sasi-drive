"""Detection and description of supported P2000C CP/M disk layouts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from . import constants


PartitionName = Literal["single", "low", "high"]
LayoutMode = Literal["single", "split"]


class LayoutDetectionError(ValueError):
    """Raised when system tracks do not describe one supported layout."""


@dataclass(frozen=True, slots=True)
class DiskParameterBlock:
    offset: int
    sectors_per_track: int
    block_shift: int
    block_mask: int
    extent_mask: int
    maximum_block: int
    maximum_directory_entry: int
    allocation_reserved_0: int
    allocation_reserved_1: int
    directory_check_size: int
    reserved_tracks: int

    @property
    def signature(self) -> tuple[int, int, int, int, int, int, int, int, int, int, int]:
        return (
            self.sectors_per_track,
            self.block_shift,
            self.block_mask,
            self.extent_mask,
            self.maximum_block,
            self.maximum_directory_entry,
            self.allocation_reserved_0,
            self.allocation_reserved_1,
            self.directory_check_size,
            self.reserved_tracks,
            self.directory_start_lba,
        )

    @property
    def directory_start_lba(self) -> int:
        return (
            self.reserved_tracks
            * self.sectors_per_track
            * constants.LOGICAL_RECORD_SIZE
            // constants.SECTOR_SIZE
        )

    @property
    def matches_p2000c_layout(self) -> bool:
        """Whether this is one of the three confirmed hard-disk DPBs."""
        return _profile_for_dpb(self) is not None


@dataclass(frozen=True, slots=True)
class PartitionLayout:
    """All geometry needed to address one CP/M filesystem in the image."""

    name: PartitionName
    display_name: str
    maximum_block: int
    allocation_reserved: tuple[int, int]
    reserved_tracks: int

    @property
    def directory_start_lba(self) -> int:
        return (
            self.reserved_tracks
            * constants.DPB_SECTORS_PER_TRACK
            * constants.LOGICAL_RECORD_SIZE
            // constants.SECTOR_SIZE
        )

    @property
    def directory_end_lba(self) -> int:
        return self.directory_start_lba + constants.DIRECTORY_SECTOR_COUNT - 1

    @property
    def allocation_block_count(self) -> int:
        return self.maximum_block + 1

    @property
    def reserved_allocation_blocks(self) -> frozenset[int]:
        bits = (self.allocation_reserved[0] << 8) | self.allocation_reserved[1]
        return frozenset(index for index in range(16) if bits & (0x8000 >> index))

    @property
    def first_usable_allocation_block(self) -> int:
        reserved = self.reserved_allocation_blocks
        first = 0
        while first in reserved:
            first += 1
        return first

    @property
    def filesystem_end_lba(self) -> int:
        return (
            self.directory_start_lba
            + self.allocation_block_count * constants.ALLOCATION_BLOCK_SECTORS
            - 1
        )

    @property
    def capacity_bytes(self) -> int:
        return (
            self.allocation_block_count - len(self.reserved_allocation_blocks)
        ) * constants.ALLOCATION_BLOCK_SIZE

    def block_offset(self, block: int) -> int:
        lba = self.directory_start_lba + block * constants.ALLOCATION_BLOCK_SECTORS
        return lba * constants.SECTOR_SIZE


@dataclass(frozen=True, slots=True)
class ImageLayout:
    mode: LayoutMode
    partitions: tuple[PartitionLayout, ...]
    dpbs: tuple[DiskParameterBlock, ...]
    assumed_from_blank_system: bool = False

    def partition(self, name: str | None = None) -> PartitionLayout:
        if self.mode == "single":
            if name not in (None, "single", "low"):
                raise LayoutDetectionError(
                    "this image has one filesystem; omit --partition"
                )
            return self.partitions[0]
        if name is None:
            raise LayoutDetectionError(
                "this is a split image; choose --partition low or --partition high"
            )
        for partition in self.partitions:
            if partition.name == name:
                return partition
        raise LayoutDetectionError(
            f"unknown split-image partition {name!r}; choose low or high"
        )


SINGLE_PARTITION = PartitionLayout(
    name="single",
    display_name="single 10 MiB",
    maximum_block=constants.DPB_MAXIMUM_BLOCK,
    allocation_reserved=constants.DPB_ALLOCATION_RESERVED,
    reserved_tracks=constants.DPB_RESERVED_TRACKS,
)
SPLIT_LOW_PARTITION = PartitionLayout(
    name="low",
    display_name="low 5 MiB (HRD1)",
    maximum_block=constants.SPLIT_LOW_DPB_MAXIMUM_BLOCK,
    allocation_reserved=constants.SPLIT_LOW_DPB_ALLOCATION_RESERVED,
    reserved_tracks=constants.SPLIT_LOW_DPB_RESERVED_TRACKS,
)
SPLIT_HIGH_PARTITION = PartitionLayout(
    name="high",
    display_name="high 5 MiB (HRD2)",
    maximum_block=constants.SPLIT_HIGH_DPB_MAXIMUM_BLOCK,
    allocation_reserved=constants.SPLIT_HIGH_DPB_ALLOCATION_RESERVED,
    reserved_tracks=constants.SPLIT_HIGH_DPB_RESERVED_TRACKS,
)


def _expected_signature(partition: PartitionLayout) -> tuple[int, ...]:
    return (
        constants.DPB_SECTORS_PER_TRACK,
        constants.DPB_BLOCK_SHIFT,
        constants.DPB_BLOCK_MASK,
        constants.DPB_EXTENT_MASK,
        partition.maximum_block,
        constants.DPB_MAXIMUM_DIRECTORY_ENTRY,
        partition.allocation_reserved[0],
        partition.allocation_reserved[1],
        constants.DPB_DIRECTORY_CHECK_SIZE,
        partition.reserved_tracks,
        partition.directory_start_lba,
    )


def _profile_for_dpb(dpb: DiskParameterBlock) -> PartitionLayout | None:
    for partition in (SINGLE_PARTITION, SPLIT_LOW_PARTITION, SPLIT_HIGH_PARTITION):
        if dpb.signature == _expected_signature(partition):
            return partition
    return None


def decode_dpb(data: bytes, offset: int) -> DiskParameterBlock:
    if offset < 0 or offset + 15 > len(data):
        raise ValueError("a CP/M 2.2 Disk Parameter Block requires 15 bytes")
    return DiskParameterBlock(
        offset=offset,
        sectors_per_track=int.from_bytes(data[offset : offset + 2], "little"),
        block_shift=data[offset + 2],
        block_mask=data[offset + 3],
        extent_mask=data[offset + 4],
        maximum_block=int.from_bytes(data[offset + 5 : offset + 7], "little"),
        maximum_directory_entry=int.from_bytes(data[offset + 7 : offset + 9], "little"),
        allocation_reserved_0=data[offset + 9],
        allocation_reserved_1=data[offset + 10],
        directory_check_size=int.from_bytes(data[offset + 11 : offset + 13], "little"),
        reserved_tracks=int.from_bytes(data[offset + 13 : offset + 15], "little"),
    )


def find_matching_dpbs(system_area: bytes) -> tuple[DiskParameterBlock, ...]:
    """Find all DPBs matching the confirmed single or split layouts."""
    matches: list[DiskParameterBlock] = []
    for offset in range(0, len(system_area) - 14):
        candidate = decode_dpb(system_area, offset)
        if candidate.matches_p2000c_layout:
            matches.append(candidate)
    return tuple(matches)


def detect_image_layout(system_area: bytes) -> ImageLayout:
    """Detect a single or split layout from its system-area DPBs."""
    if len(system_area) != constants.SYSTEM_AREA_SIZE:
        raise LayoutDetectionError(
            f"system area must contain exactly {constants.SYSTEM_AREA_SIZE} bytes"
        )
    blank = bytes([constants.DEFAULT_FILL_BYTE]) * constants.SYSTEM_AREA_SIZE
    if system_area == blank:
        return ImageLayout("single", (SINGLE_PARTITION,), (), True)

    dpbs = find_matching_dpbs(system_area)
    profiles = tuple(_profile_for_dpb(dpb) for dpb in dpbs)
    has_single = SINGLE_PARTITION in profiles
    has_low = SPLIT_LOW_PARTITION in profiles
    has_high = SPLIT_HIGH_PARTITION in profiles
    if has_single and not (has_low or has_high):
        return ImageLayout("single", (SINGLE_PARTITION,), dpbs)
    if has_low and has_high and not has_single:
        return ImageLayout(
            "split", (SPLIT_LOW_PARTITION, SPLIT_HIGH_PARTITION), dpbs
        )
    if has_low != has_high:
        missing = "high" if has_low else "low"
        raise LayoutDetectionError(
            f"incomplete split layout: the {missing}-partition DPB is missing"
        )
    raise LayoutDetectionError(
        "non-blank system area does not contain a confirmed P2000C single or split layout"
    )


def resolve_partition(
    system_area: bytes, selection: str | PartitionLayout | None = None
) -> tuple[ImageLayout, PartitionLayout]:
    layout = detect_image_layout(system_area)
    if isinstance(selection, PartitionLayout):
        if selection not in layout.partitions:
            raise LayoutDetectionError(
                f"partition {selection.name!r} is not present in this {layout.mode} image"
            )
        return layout, selection
    return layout, layout.partition(selection)


assert SINGLE_PARTITION.directory_start_lba == constants.DIRECTORY_START_LBA
assert SINGLE_PARTITION.filesystem_end_lba == constants.FILESYSTEM_END_LBA
assert SPLIT_LOW_PARTITION.directory_start_lba == constants.SPLIT_LOW_DIRECTORY_START_LBA
assert SPLIT_LOW_PARTITION.filesystem_end_lba == constants.SPLIT_LOW_FILESYSTEM_END_LBA
assert SPLIT_HIGH_PARTITION.directory_start_lba == constants.SPLIT_HIGH_DIRECTORY_START_LBA
assert SPLIT_HIGH_PARTITION.filesystem_end_lba == constants.SPLIT_HIGH_FILESYSTEM_END_LBA
