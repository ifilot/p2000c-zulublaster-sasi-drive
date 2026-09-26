"""Developer-oriented comparison of P2000C system areas."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

from . import constants
from .image import DiskImage


@dataclass(frozen=True, slots=True)
class ByteRange:
    start: int
    end: int

    def __str__(self) -> str:
        return f"0x{self.start:04X}" if self.start == self.end else f"0x{self.start:04X}-0x{self.end:04X}"


@dataclass(frozen=True, slots=True)
class IntegerCandidates:
    offset: int
    old_u8: int
    new_u8: int
    old_u16le: int | None
    new_u16le: int | None
    old_u16be: int | None
    new_u16be: int | None


@dataclass(frozen=True, slots=True)
class RangeChange:
    start: int
    end: int
    old_hex: str
    new_hex: str
    old_ascii: str
    new_ascii: str
    ascii_context_before: str
    ascii_context_after: str
    integer_candidates: IntegerCandidates


@dataclass(frozen=True, slots=True)
class StringLocation:
    offset: int
    value: str


@dataclass(frozen=True, slots=True)
class MovedString:
    value: str
    old_offsets: tuple[int, ...]
    new_offsets: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class LengthByteCandidate:
    offset: int
    value: int
    following_text: str


@dataclass(frozen=True, slots=True)
class PairwiseSystemComparison:
    image: str
    changed_offsets: tuple[int, ...]
    changed_ranges: tuple[ByteRange, ...]
    changes: tuple[RangeChange, ...]
    strings_added: tuple[StringLocation, ...]
    strings_removed: tuple[StringLocation, ...]
    strings_moved: tuple[MovedString, ...]
    candidate_length_bytes: tuple[LengthByteCandidate, ...]


@dataclass(frozen=True, slots=True)
class SystemComparisonReport:
    baseline: str
    images: tuple[str, ...]
    pairwise: tuple[PairwiseSystemComparison, ...]
    unchanged_across_all: tuple[ByteRange, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class RangeSample:
    path: str
    raw_hex: str
    ascii_context: str


@dataclass(frozen=True, slots=True)
class AggregateChangedRange:
    start: int
    end: int
    samples: tuple[RangeSample, ...]


@dataclass(frozen=True, slots=True)
class AggregateLengthCandidate:
    path: str
    offset: int
    length: int
    following_ascii: str


@dataclass(frozen=True, slots=True)
class AggregateIntegerCandidate:
    path: str
    offset: int
    u8: int
    u16le: int | None
    u16be: int | None


@dataclass(frozen=True, slots=True)
class StringDifference:
    status: str
    value: str
    locations: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class AggregateSystemComparisonReport:
    paths: tuple[str, ...]
    changed_offsets: tuple[int, ...]
    changed_ranges: tuple[AggregateChangedRange, ...]
    unchanged_ranges: tuple[ByteRange, ...]
    length_byte_candidates: tuple[AggregateLengthCandidate, ...]
    integer_candidates: tuple[AggregateIntegerCandidate, ...]
    string_differences: tuple[StringDifference, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _ranges(offsets: Iterable[int]) -> tuple[ByteRange, ...]:
    values = tuple(offsets)
    if not values:
        return ()
    ranges: list[ByteRange] = []
    start = previous = values[0]
    for offset in values[1:]:
        if offset != previous + 1:
            ranges.append(ByteRange(start, previous))
            start = offset
        previous = offset
    ranges.append(ByteRange(start, previous))
    return tuple(ranges)


def _ascii(raw: bytes) -> str:
    return "".join(chr(byte) if 0x20 <= byte <= 0x7E else "." for byte in raw)


def _strings(data: bytes, minimum: int = 4) -> tuple[StringLocation, ...]:
    found: list[StringLocation] = []
    start: int | None = None
    for offset, byte in enumerate(data + b"\x00"):
        if 0x20 <= byte <= 0x7E:
            if start is None:
                start = offset
        elif start is not None:
            if offset - start >= minimum:
                found.append(StringLocation(start, data[start:offset].decode("ascii")))
            start = None
    return tuple(found)


def _length_candidates(data: bytes, changed: tuple[int, ...]) -> tuple[LengthByteCandidate, ...]:
    candidates: list[LengthByteCandidate] = []
    for offset in changed:
        length = data[offset]
        if not 1 <= length <= 127 or offset + 1 + length > len(data):
            continue
        following = data[offset + 1 : offset + 1 + length]
        if all(0x20 <= byte <= 0x7E for byte in following):
            candidates.append(
                LengthByteCandidate(offset, length, following.decode("ascii"))
            )
    return tuple(candidates)


def _integer_candidates(old: bytes, new: bytes, offset: int) -> IntegerCandidates:
    has_word = offset + 2 <= len(old)
    return IntegerCandidates(
        offset=offset,
        old_u8=old[offset],
        new_u8=new[offset],
        old_u16le=int.from_bytes(old[offset : offset + 2], "little") if has_word else None,
        new_u16le=int.from_bytes(new[offset : offset + 2], "little") if has_word else None,
        old_u16be=int.from_bytes(old[offset : offset + 2], "big") if has_word else None,
        new_u16be=int.from_bytes(new[offset : offset + 2], "big") if has_word else None,
    )


def _pairwise(
    baseline_path: str,
    baseline: bytes,
    image_path: str,
    current: bytes,
) -> PairwiseSystemComparison:
    changed = tuple(
        offset
        for offset, (old, new) in enumerate(zip(baseline, current, strict=True))
        if old != new
    )
    ranges = _ranges(changed)
    changes: list[RangeChange] = []
    for item in ranges:
        end = item.end + 1
        context_start = max(0, item.start - 16)
        context_end = min(len(baseline), end + 16)
        changes.append(
            RangeChange(
                start=item.start,
                end=item.end,
                old_hex=baseline[item.start:end].hex().upper(),
                new_hex=current[item.start:end].hex().upper(),
                old_ascii=_ascii(baseline[item.start:end]),
                new_ascii=_ascii(current[item.start:end]),
                ascii_context_before=_ascii(baseline[context_start:context_end]),
                ascii_context_after=_ascii(current[context_start:context_end]),
                integer_candidates=_integer_candidates(baseline, current, item.start),
            )
        )

    old_strings = _strings(baseline)
    new_strings = _strings(current)
    old_by_value: dict[str, list[int]] = {}
    new_by_value: dict[str, list[int]] = {}
    for string in old_strings:
        old_by_value.setdefault(string.value, []).append(string.offset)
    for string in new_strings:
        new_by_value.setdefault(string.value, []).append(string.offset)
    added = tuple(item for item in new_strings if item.value not in old_by_value)
    removed = tuple(item for item in old_strings if item.value not in new_by_value)
    moved = tuple(
        MovedString(value, tuple(old_by_value[value]), tuple(new_by_value[value]))
        for value in sorted(old_by_value.keys() & new_by_value.keys())
        if old_by_value[value] != new_by_value[value]
    )
    length_candidates = {
        (item.offset, item.value, item.following_text): item
        for item in _length_candidates(baseline, changed)
        + _length_candidates(current, changed)
    }
    return PairwiseSystemComparison(
        image=image_path,
        changed_offsets=changed,
        changed_ranges=ranges,
        changes=tuple(changes),
        strings_added=added,
        strings_removed=removed,
        strings_moved=moved,
        candidate_length_bytes=tuple(length_candidates.values()),
    )


def compare_system_images(images: Iterable[str | Path]) -> SystemComparisonReport:
    paths = tuple(Path(path) for path in images)
    if len(paths) < 2:
        raise ValueError("compare-system requires at least two images")
    areas: list[bytes] = []
    for path in paths:
        disk = DiskImage(path)
        disk.validate_size()
        areas.append(disk.system_area())
    baseline = areas[0]
    pairwise = tuple(
        _pairwise(str(paths[0]), baseline, str(path), data)
        for path, data in zip(paths[1:], areas[1:], strict=True)
    )
    unchanged = tuple(
        offset
        for offset in range(constants.SYSTEM_AREA_SIZE)
        if all(data[offset] == baseline[offset] for data in areas[1:])
    )
    return SystemComparisonReport(
        baseline=str(paths[0]),
        images=tuple(str(path) for path in paths),
        pairwise=pairwise,
        unchanged_across_all=_ranges(unchanged),
    )


def compare_system_areas(images: Iterable[str | Path]) -> AggregateSystemComparisonReport:
    """Compare all samples symmetrically for configuration capture analysis."""
    paths = tuple(Path(path) for path in images)
    if len(paths) < 2:
        raise ValueError("compare-system requires at least two images")
    areas: list[bytes] = []
    for path in paths:
        disk = DiskImage(path)
        disk.validate_size()
        areas.append(disk.system_area())
    changed = tuple(
        offset
        for offset in range(constants.SYSTEM_AREA_SIZE)
        if len({area[offset] for area in areas}) > 1
    )
    changed_ranges: list[AggregateChangedRange] = []
    for item in _ranges(changed):
        end = item.end + 1
        context_start = max(0, item.start - 16)
        context_end = min(constants.SYSTEM_AREA_SIZE, end + 16)
        changed_ranges.append(
            AggregateChangedRange(
                start=item.start,
                end=item.end,
                samples=tuple(
                    RangeSample(
                        path=str(path),
                        raw_hex=area[item.start:end].hex().upper(),
                        ascii_context=_ascii(area[context_start:context_end]),
                    )
                    for path, area in zip(paths, areas, strict=True)
                ),
            )
        )
    unchanged = tuple(
        offset
        for offset in range(constants.SYSTEM_AREA_SIZE)
        if all(area[offset] == areas[0][offset] for area in areas[1:])
    )
    length_candidates = tuple(
        AggregateLengthCandidate(
            path=str(path),
            offset=candidate.offset,
            length=candidate.value,
            following_ascii=candidate.following_text,
        )
        for path, area in zip(paths, areas, strict=True)
        for candidate in _length_candidates(area, changed)
    )
    integers = tuple(
        AggregateIntegerCandidate(
            path=str(path),
            offset=offset,
            u8=area[offset],
            u16le=(
                int.from_bytes(area[offset : offset + 2], "little")
                if offset + 2 <= len(area)
                else None
            ),
            u16be=(
                int.from_bytes(area[offset : offset + 2], "big")
                if offset + 2 <= len(area)
                else None
            ),
        )
        for offset in changed
        for path, area in zip(paths, areas, strict=True)
    )
    strings_by_path = [_strings(area) for area in areas]
    all_values = sorted({item.value for strings in strings_by_path for item in strings})
    differences: list[StringDifference] = []
    for value in all_values:
        locations = tuple(
            f"{path}@0x{item.offset:04X}"
            for path, strings in zip(paths, strings_by_path, strict=True)
            for item in strings
            if item.value == value
        )
        presence = [any(item.value == value for item in strings) for strings in strings_by_path]
        offsets = [
            tuple(item.offset for item in strings if item.value == value)
            for strings in strings_by_path
        ]
        if all(presence) and len(set(offsets)) == 1:
            continue
        if presence[0] and not all(presence[1:]):
            status = "removed"
        elif not presence[0] and any(presence[1:]):
            status = "added"
        else:
            status = "moved-or-changed"
        differences.append(StringDifference(status, value, locations))
    return AggregateSystemComparisonReport(
        paths=tuple(str(path) for path in paths),
        changed_offsets=changed,
        changed_ranges=tuple(changed_ranges),
        unchanged_ranges=_ranges(unchanged),
        length_byte_candidates=length_candidates,
        integer_candidates=integers,
        string_differences=tuple(differences),
    )
