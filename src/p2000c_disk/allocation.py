"""Evidence-based analysis of possible CP/M allocation mappings.

This module intentionally models several hypotheses.  It does not establish any
of them as the P2000C allocation formula.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any, Iterable, Literal

from . import constants
from .directory import DirectoryEntry, read_directory
from .image import DiskImage, SectorRange, sector_ranges
from .layout import PartitionLayout, find_matching_dpbs, resolve_partition


CANDIDATE_BLOCK_SIZES: tuple[int, ...] = (1, 2, 4, 8, 16, 32, 64)
AllocationInterpretation = Literal["u8", "u16le"]
CandidateClassification = Literal[
    "confirmed", "candidate", "inconsistent", "insufficient-evidence"
]


@dataclass(frozen=True, slots=True)
class AllocationRange:
    value: int
    start_lba: int
    end_lba: int


@dataclass(frozen=True, slots=True)
class EntryAllocationObservation:
    index: int
    filename: str
    extent: int
    s1: int
    s2: int
    record_count: int
    raw_hex: str
    raw_bytes_decimal: tuple[int, ...]
    u8_values: tuple[int, ...]
    u16le_values: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class MappingCandidate:
    interpretation: AllocationInterpretation
    block_size_sectors: int
    anchor_name: str
    anchor_lba: int
    formula: str
    allocation_values: tuple[int, ...]
    predicted_ranges: tuple[AllocationRange, ...]
    matched_non_fill_sectors: tuple[int, ...]
    unexplained_non_fill_sectors: tuple[int, ...]
    predicted_fill_sectors: tuple[int, ...]
    known_structure_overlaps: tuple[int, ...]
    out_of_bounds_values: tuple[int, ...]
    classification: CandidateClassification
    reasons: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ImageAllocationAnalysis:
    path: str
    partition: str
    image_size: int
    active_entries: tuple[EntryAllocationObservation, ...]
    non_fill_sectors: tuple[int, ...]
    non_fill_ranges: tuple[SectorRange, ...]
    unclassified_non_fill_sectors: tuple[int, ...]
    unclassified_non_fill_ranges: tuple[SectorRange, ...]
    matching_dpb_offsets: tuple[int, ...]
    candidates: tuple[MappingCandidate, ...]
    confirmed_mappings: tuple[MappingCandidate, ...] = ()


@dataclass(frozen=True, slots=True)
class DirectoryChange:
    index: int
    change: Literal["added", "removed", "modified"]
    before_filename: str | None
    after_filename: str | None


@dataclass(frozen=True, slots=True)
class ComparisonAnalysis:
    before_path: str
    after_path: str
    changed_sectors: tuple[int, ...]
    changed_sector_ranges: tuple[SectorRange, ...]
    changed_non_fill_sectors: tuple[int, ...]
    changed_non_fill_ranges: tuple[SectorRange, ...]
    changed_to_fill_sectors: tuple[int, ...]
    directory_changes: tuple[DirectoryChange, ...]
    relevant_after_entry_indices: tuple[int, ...]
    candidates: tuple[MappingCandidate, ...]
    confirmed_mappings: tuple[MappingCandidate, ...] = ()


@dataclass(frozen=True, slots=True)
class AllocationAnalysisReport:
    images: tuple[ImageAllocationAnalysis, ...]
    comparison: ComparisonAnalysis | None
    caveats: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation."""
        return asdict(self)


def _entry_observation(entry: DirectoryEntry) -> EntryAllocationObservation:
    return EntryAllocationObservation(
        index=entry.index,
        filename=entry.normalized_filename,
        extent=entry.extent,
        s1=entry.s1,
        s2=entry.s2,
        record_count=entry.record_count,
        raw_hex=entry.allocation.hex().upper(),
        raw_bytes_decimal=tuple(entry.allocation),
        u8_values=tuple(entry.allocation),
        u16le_values=tuple(
            int.from_bytes(entry.allocation[offset : offset + 2], "little")
            for offset in range(0, len(entry.allocation), 2)
        ),
    )


def _non_fill_sectors(data: bytes, fill_byte: int = constants.DEFAULT_FILL_BYTE) -> tuple[int, ...]:
    expected = bytes([fill_byte]) * constants.SECTOR_SIZE
    return tuple(
        lba
        for lba in range(constants.SECTOR_COUNT)
        if data[lba * constants.SECTOR_SIZE : (lba + 1) * constants.SECTOR_SIZE]
        != expected
    )


def _is_known_structure(lba: int, partition: PartitionLayout) -> bool:
    return (
        constants.SYSTEM_AREA_START_LBA <= lba <= constants.SYSTEM_AREA_END_LBA
        or partition.directory_start_lba <= lba <= partition.directory_end_lba
    )


def _allocation_values(
    entries: Iterable[DirectoryEntry], interpretation: AllocationInterpretation
) -> tuple[int, ...]:
    values: set[int] = set()
    for entry in entries:
        if interpretation == "u8":
            decoded = entry.allocation
        else:
            decoded = tuple(
                int.from_bytes(entry.allocation[offset : offset + 2], "little")
                for offset in range(0, len(entry.allocation), 2)
            )
        # Zero is tested as the conventional unused allocation-slot value.  The
        # report caveats explicitly identify this as an assumption.
        values.update(value for value in decoded if value != 0)
    return tuple(sorted(values))


def _classify_candidate(
    values: tuple[int, ...],
    observed: tuple[int, ...],
    matched: tuple[int, ...],
    unexplained: tuple[int, ...],
    overlaps: tuple[int, ...],
    out_of_bounds: tuple[int, ...],
) -> tuple[CandidateClassification, tuple[str, ...]]:
    reasons: list[str] = []
    if unexplained:
        reasons.append("does not cover every unclassified non-fill sector")
    if overlaps:
        reasons.append("predicts allocated sectors inside a known structural region")
    if out_of_bounds:
        reasons.append("one or more allocation values map outside the image")
    if reasons:
        return "inconsistent", tuple(reasons)
    if not values and not observed:
        return "insufficient-evidence", ("no non-zero allocations or data-sector evidence",)
    if not values:
        return "inconsistent", ("data-sector evidence exists without a non-zero allocation",)
    if not observed or not matched:
        return "insufficient-evidence", ("allocations exist but no matching non-fill data was observed",)
    return "candidate", (
        "covers the observed sectors without a hard contradiction; this is not confirmation",
    )


def _mapping_candidates(
    entries: Iterable[DirectoryEntry],
    observed_sectors: tuple[int, ...],
    partition: PartitionLayout,
) -> tuple[MappingCandidate, ...]:
    entry_tuple = tuple(entries)
    anchors = (
        ("image-start", 0),
        ("directory-start", partition.directory_start_lba),
        ("after-directory", partition.directory_end_lba + 1),
    )
    observed = set(observed_sectors)
    candidates: list[MappingCandidate] = []
    for interpretation in ("u8", "u16le"):
        values = _allocation_values(entry_tuple, interpretation)
        for block_size in CANDIDATE_BLOCK_SIZES:
            for anchor_name, anchor_lba in anchors:
                ranges: list[AllocationRange] = []
                predicted: set[int] = set()
                out_of_bounds: list[int] = []
                for value in values:
                    start = anchor_lba + value * block_size
                    end = start + block_size - 1
                    ranges.append(AllocationRange(value, start, end))
                    if start < 0 or end >= constants.SECTOR_COUNT:
                        out_of_bounds.append(value)
                        continue
                    predicted.update(range(start, end + 1))
                matched = tuple(sorted(observed & predicted))
                unexplained = tuple(sorted(observed - predicted))
                predicted_fill = tuple(sorted(predicted - observed))
                overlaps = tuple(
                    sorted(lba for lba in predicted if _is_known_structure(lba, partition))
                )
                classification, reasons = _classify_candidate(
                    values,
                    observed_sectors,
                    matched,
                    unexplained,
                    overlaps,
                    tuple(out_of_bounds),
                )
                candidates.append(
                    MappingCandidate(
                        interpretation=interpretation,
                        block_size_sectors=block_size,
                        anchor_name=anchor_name,
                        anchor_lba=anchor_lba,
                        formula=f"LBA = {anchor_lba} + allocation_value * {block_size}",
                        allocation_values=values,
                        predicted_ranges=tuple(ranges),
                        matched_non_fill_sectors=matched,
                        unexplained_non_fill_sectors=unexplained,
                        predicted_fill_sectors=predicted_fill,
                        known_structure_overlaps=overlaps,
                        out_of_bounds_values=tuple(out_of_bounds),
                        classification=classification,
                        reasons=reasons,
                    )
                )
    return tuple(candidates)


def _apply_dpb_evidence(
    candidates: tuple[MappingCandidate, ...], has_matching_dpb: bool
) -> tuple[tuple[MappingCandidate, ...], tuple[MappingCandidate, ...]]:
    if not has_matching_dpb:
        return candidates, ()
    updated: list[MappingCandidate] = []
    confirmed: list[MappingCandidate] = []
    for candidate in candidates:
        is_dpb_mapping = (
            candidate.interpretation == "u16le"
            and candidate.block_size_sectors == constants.ALLOCATION_BLOCK_SECTORS
            and candidate.anchor_name == "directory-start"
        )
        if is_dpb_mapping and candidate.classification == "candidate":
            changed = replace(
                candidate,
                classification="confirmed",
                reasons=(
                    "correlation fits and the embedded CP/M Disk Parameter Block independently confirms this mapping",
                ),
            )
            confirmed.append(changed)
        elif candidate.classification == "candidate":
            changed = replace(
                candidate,
                classification="inconsistent",
                reasons=candidate.reasons
                + ("correlation fits, but this hypothesis conflicts with the embedded DPB",),
            )
        else:
            changed = candidate
        updated.append(changed)
    return tuple(updated), tuple(confirmed)


def _analyze_one(
    path: str | Path, partition: str | PartitionLayout | None
) -> tuple[
    ImageAllocationAnalysis,
    bytes,
    tuple[DirectoryEntry, ...],
    PartitionLayout,
]:
    image = DiskImage(path)
    image.validate_size()
    data = image.read_range(0, constants.IMAGE_SIZE)
    _, selected = resolve_partition(data[: constants.SYSTEM_AREA_SIZE], partition)
    entries = read_directory(image, selected)
    matching_dpbs = find_matching_dpbs(data[: constants.SYSTEM_AREA_SIZE])
    non_fill = _non_fill_sectors(data)
    unclassified = tuple(
        lba
        for lba in non_fill
        if selected.directory_start_lba <= lba <= selected.filesystem_end_lba
        and not _is_known_structure(lba, selected)
    )
    candidates, confirmed = _apply_dpb_evidence(
        _mapping_candidates(entries, unclassified, selected), bool(matching_dpbs)
    )
    analysis = ImageAllocationAnalysis(
        path=str(image.path),
        partition=selected.name,
        image_size=image.size,
        active_entries=tuple(_entry_observation(entry) for entry in entries),
        non_fill_sectors=non_fill,
        non_fill_ranges=sector_ranges(non_fill),
        unclassified_non_fill_sectors=unclassified,
        unclassified_non_fill_ranges=sector_ranges(unclassified),
        matching_dpb_offsets=tuple(dpb.offset for dpb in matching_dpbs),
        candidates=candidates,
        confirmed_mappings=confirmed,
    )
    return analysis, data, entries, selected


def _entry_map(entries: Iterable[DirectoryEntry]) -> dict[int, DirectoryEntry]:
    return {entry.index: entry for entry in entries}


def _compare(
    before_path: str,
    before_data: bytes,
    before_entries: tuple[DirectoryEntry, ...],
    after_path: str,
    after_data: bytes,
    after_entries: tuple[DirectoryEntry, ...],
    after_has_matching_dpb: bool,
    partition: PartitionLayout,
) -> ComparisonAnalysis:
    changed = tuple(
        lba
        for lba in range(constants.SECTOR_COUNT)
        if before_data[lba * constants.SECTOR_SIZE : (lba + 1) * constants.SECTOR_SIZE]
        != after_data[lba * constants.SECTOR_SIZE : (lba + 1) * constants.SECTOR_SIZE]
    )
    fill_sector = bytes([constants.DEFAULT_FILL_BYTE]) * constants.SECTOR_SIZE
    changed_non_fill = tuple(
        lba
        for lba in changed
        if partition.directory_start_lba <= lba <= partition.filesystem_end_lba
        and not _is_known_structure(lba, partition)
        and after_data[lba * constants.SECTOR_SIZE : (lba + 1) * constants.SECTOR_SIZE]
        != fill_sector
    )
    changed_to_fill = tuple(
        lba
        for lba in changed
        if partition.directory_start_lba <= lba <= partition.filesystem_end_lba
        and not _is_known_structure(lba, partition)
        and after_data[lba * constants.SECTOR_SIZE : (lba + 1) * constants.SECTOR_SIZE]
        == fill_sector
    )

    before_by_index = _entry_map(before_entries)
    after_by_index = _entry_map(after_entries)
    changes: list[DirectoryChange] = []
    relevant_entries: list[DirectoryEntry] = []
    for index in sorted(before_by_index.keys() | after_by_index.keys()):
        before = before_by_index.get(index)
        after = after_by_index.get(index)
        if before is not None and after is not None and before.raw == after.raw:
            continue
        if before is None:
            change: Literal["added", "removed", "modified"] = "added"
        elif after is None:
            change = "removed"
        else:
            change = "modified"
        changes.append(
            DirectoryChange(
                index=index,
                change=change,
                before_filename=before.normalized_filename if before else None,
                after_filename=after.normalized_filename if after else None,
            )
        )
        if after is not None:
            relevant_entries.append(after)

    candidates, confirmed = _apply_dpb_evidence(
        _mapping_candidates(relevant_entries, changed_non_fill, partition),
        after_has_matching_dpb,
    )
    return ComparisonAnalysis(
        before_path=before_path,
        after_path=after_path,
        changed_sectors=changed,
        changed_sector_ranges=sector_ranges(changed),
        changed_non_fill_sectors=changed_non_fill,
        changed_non_fill_ranges=sector_ranges(changed_non_fill),
        changed_to_fill_sectors=changed_to_fill,
        directory_changes=tuple(changes),
        relevant_after_entry_indices=tuple(entry.index for entry in relevant_entries),
        candidates=candidates,
        confirmed_mappings=confirmed,
    )


def analyze_allocation(
    image: str | Path,
    comparison_image: str | Path | None = None,
    *,
    partition: str | PartitionLayout | None = None,
) -> AllocationAnalysisReport:
    """Analyze one image, or compare a before image with an after image."""
    first, first_data, first_entries, selected = _analyze_one(image, partition)
    images = [first]
    comparison: ComparisonAnalysis | None = None
    if comparison_image is not None:
        second, second_data, second_entries, second_partition = _analyze_one(
            comparison_image, selected.name
        )
        if second_partition.name != selected.name:
            raise ValueError("comparison images do not use the same partition layout")
        images.append(second)
        comparison = _compare(
            first.path,
            first_data,
            first_entries,
            second.path,
            second_data,
            second_entries,
            bool(second.matching_dpb_offsets),
            selected,
        )
    return AllocationAnalysisReport(
        images=tuple(images),
        comparison=comparison,
        caveats=(
            "Non-fill sectors outside the known system and directory areas are unclassified; they are not proven file data.",
            "Zero allocation values are treated as unused slots for candidate testing only.",
            "Both 8-bit and little-endian 16-bit entries are tested; an embedded matching DPB confirms the latter.",
            "Candidate anchors are hypotheses and are not an exhaustive list of possible mappings.",
            "A correlation candidate is not confirmation; confirmed status requires independent embedded DPB evidence.",
        ),
    )
