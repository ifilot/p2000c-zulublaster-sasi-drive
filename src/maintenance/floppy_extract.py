# SPDX-FileCopyrightText: 2026 P2000C SASI Distribution contributors
# SPDX-License-Identifier: GPL-3.0-or-later

#!/usr/bin/env python3
"""Decode sector data from IMD and HFE floppy images.

The decoder is intentionally read-only.  It supports the IBM MFM sector
encoding used by the Philips P2000C museum images, including 256-byte and
512-byte sectors.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
import struct


@dataclass(frozen=True)
class Sector:
    cylinder: int
    head: int
    number: int
    data: bytes | None
    status: str = "ok"


def read_imd(path: Path) -> list[Sector]:
    image = path.read_bytes()
    position = image.index(0x1A) + 1
    sectors: list[Sector] = []
    while position < len(image):
        _mode, cylinder, head_flags, count, size_code = image[position : position + 5]
        position += 5
        numbers = image[position : position + count]
        position += count
        cylinders = bytes([cylinder]) * count
        heads = bytes([head_flags & 1]) * count
        if head_flags & 0x80:
            cylinders = image[position : position + count]
            position += count
        if head_flags & 0x40:
            heads = image[position : position + count]
            position += count
        if size_code == 0xFF:
            sizes = struct.unpack_from(f"<{count}H", image, position)
            position += count * 2
        else:
            sizes = (128 << size_code,) * count
        for sector_cylinder, sector_head, number, size in zip(
            cylinders, heads, numbers, sizes, strict=True
        ):
            record_type = image[position]
            position += 1
            if record_type == 0:
                data = None
            elif record_type & 1:
                data = image[position : position + size]
                position += size
            elif 2 <= record_type <= 8:
                data = bytes([image[position]]) * size
                position += 1
            else:
                raise ValueError(f"unsupported IMD sector record type {record_type}")
            status = "ok" if record_type in (1, 2, 3, 4) else "read-error"
            sectors.append(Sector(sector_cylinder, sector_head, number, data, status))
    return sectors


def _reverse_byte(value: int) -> int:
    value = ((value & 0x55) << 1) | ((value >> 1) & 0x55)
    value = ((value & 0x33) << 2) | ((value >> 2) & 0x33)
    return ((value & 0x0F) << 4) | ((value >> 4) & 0x0F)


def _mfm_byte(bits: str, position: int) -> int:
    return int(bits[position + 1 : position + 16 : 2], 2)


def _decode_mfm_track(data: bytes) -> list[Sector]:
    # HFE v1 stores each byte least-significant bit first.
    bits = "".join(f"{_reverse_byte(value):08b}" for value in data)
    sync = f"{0x4489:016b}" * 3
    headers: list[tuple[int, int, int, int, int]] = []
    position = 0
    while True:
        marker = bits.find(sync, position)
        if marker < 0 or marker + 16 * 8 > len(bits):
            break
        tag_position = marker + 48
        tag = _mfm_byte(bits, tag_position)
        if tag == 0xFE:
            fields = [_mfm_byte(bits, tag_position + 16 * offset) for offset in range(1, 5)]
            cylinder, head, number, size_code = fields
            if size_code <= 7:
                headers.append((marker, cylinder, head, number, 128 << size_code))
        position = marker + 1

    sectors: list[Sector] = []
    for index, (header_position, cylinder, head, number, size) in enumerate(headers):
        search_start = header_position + 48 + 16 * 7
        search_end = headers[index + 1][0] if index + 1 < len(headers) else len(bits)
        marker = bits.find(sync, search_start, search_end)
        if marker < 0:
            continue
        tag_position = marker + 48
        tag = _mfm_byte(bits, tag_position)
        if tag not in (0xF8, 0xFB):
            continue
        data_position = tag_position + 16
        if data_position + size * 16 > len(bits):
            continue
        payload = bytes(
            _mfm_byte(bits, data_position + 16 * offset) for offset in range(size)
        )
        sectors.append(Sector(cylinder, head, number, payload))
    return sectors


def read_hfe(path: Path) -> list[Sector]:
    image = path.read_bytes()
    if image[:8] != b"HXCPICFE" or image[8] != 0:
        raise ValueError("only HFE v1 images are supported")
    track_count = image[9]
    side_count = image[10]
    table_offset = int.from_bytes(image[18:20], "little") * 512
    sectors: list[Sector] = []
    for track in range(track_count):
        offset, length = struct.unpack_from("<HH", image, table_offset + track * 4)
        rounded_length = (length + 511) & ~511
        track_data = image[offset * 512 : offset * 512 + rounded_length]
        sides = [bytearray() for _ in range(side_count)]
        for block_start in range(0, len(track_data), 512):
            block = track_data[block_start : block_start + 512]
            sides[0].extend(block[:256])
            if side_count > 1:
                sides[1].extend(block[256:512])
        for side_data in sides:
            sectors.extend(_decode_mfm_track(side_data))
    return sectors


def read_sectors(path: Path) -> list[Sector]:
    if path.suffix.lower() == ".imd":
        return read_imd(path)
    if path.suffix.lower() == ".hfe":
        return read_hfe(path)
    raise ValueError(f"unsupported image extension: {path.suffix}")


def raw_bytes(sectors: list[Sector], fill: int) -> bytes:
    if not sectors:
        raise ValueError("image contains no decoded sectors")
    grouped: dict[tuple[int, int], list[Sector]] = {}
    for sector in sectors:
        grouped.setdefault((sector.cylinder, sector.head), []).append(sector)
    output = bytearray()
    max_cylinder = max(cylinder for cylinder, _head in grouped)
    max_head = max(head for _cylinder, head in grouped)
    typical_count = max(len(items) for items in grouped.values())
    typical_size = max(
        len(sector.data) for sector in sectors if sector.data is not None
    )
    for cylinder in range(max_cylinder + 1):
        for head in range(max_head + 1):
            track = (cylinder, head)
            by_number = {sector.number: sector for sector in grouped.get(track, [])}
            for number in range(1, typical_count + 1):
                sector = by_number.get(number)
                if sector is None or sector.data is None:
                    output.extend(bytes([fill]) * typical_size)
                else:
                    output.extend(sector.data)
    return bytes(output)


def write_raw(path: Path, sectors: list[Sector], fill: int) -> None:
    path.write_bytes(raw_bytes(sectors, fill))


CPM_PROFILES = {
    "p2000c-640": (8192, 4096, 128, 3, 1),
    "p2000c-800": (8192, 2048, 256, 0, 2),
}


def _safe_name(name: str) -> str:
    return name.replace("/", "_").replace("\\", "_").replace("\x00", "_")


def extract_cpm(data: bytes, destination: Path, profile: str) -> list[tuple[str, int]]:
    base, block_size, max_directory, extent_mask, allocation_width = CPM_PROFILES[profile]
    grouped: dict[tuple[int, str], list[tuple[int, int, list[int]]]] = defaultdict(list)
    directory = data[base : base + max_directory * 32]
    for offset in range(0, len(directory), 32):
        entry = directory[offset : offset + 32]
        if len(entry) < 32 or entry[0] == 0xE5:
            continue
        if entry[0] > 31:
            continue
        stem = bytes(value & 0x7F for value in entry[1:9]).decode("ascii", "replace").rstrip()
        suffix = bytes(value & 0x7F for value in entry[9:12]).decode("ascii", "replace").rstrip()
        if not stem:
            stem = "_UNNAMED"
        name = f"{stem}.{suffix}" if suffix else stem
        logical_extent = (entry[14] << 5) | (entry[12] & 0x1F)
        directory_extent = logical_extent // (extent_mask + 1)
        records = (entry[12] & extent_mask) * 128 + entry[15]
        if allocation_width == 1:
            blocks = list(entry[16:32])
        else:
            blocks = [
                int.from_bytes(entry[position : position + 2], "little")
                for position in range(16, 32, 2)
            ]
        grouped[(entry[0], name)].append((directory_extent, records, blocks))

    extracted: list[tuple[str, int]] = []
    destination.mkdir(parents=True, exist_ok=True)
    for (user, name), entries in sorted(grouped.items()):
        payload = bytearray()
        for _extent, records, blocks in sorted(entries):
            extent_data = bytearray()
            for block in blocks:
                if block:
                    start = base + block * block_size
                    extent_data.extend(data[start : start + block_size])
            payload.extend(extent_data[: records * 128])
        parent = destination if user == 0 else destination / f"user-{user:02d}"
        parent.mkdir(parents=True, exist_ok=True)
        output = parent / _safe_name(name.upper())
        output.write_bytes(payload)
        extracted.append((str(output.relative_to(destination)), len(payload)))
    return extracted


def _ucsd_candidate(data: bytes) -> tuple[int, str, int, str] | None:
    header = data[1024:1050]
    if len(header) < 26 or header[:2] != b"\0\0" or not 0 < header[6] < 8:
        return None
    for byte_order in ("little", "big"):
        last_directory = int.from_bytes(header[2:4], byte_order)
        if last_directory not in (6, 10):
            continue
        block_count = int.from_bytes(header[14:16], byte_order)
        file_count = int.from_bytes(header[16:18], byte_order)
        if not 0 < file_count <= 77:
            continue
        valid = 0
        for index in range(file_count):
            entry = data[1050 + index * 26 : 1076 + index * 26]
            if len(entry) < 26:
                break
            first = int.from_bytes(entry[:2], byte_order)
            after = int.from_bytes(entry[2:4], byte_order)
            name = entry[7 : 7 + min(entry[6], 15)]
            if (
                0 < entry[6] <= 15
                and all(0x20 <= value <= 0x7E for value in name)
                and first < after <= block_count + 2
            ):
                valid += 1
        if valid:
            volume_name = header[7 : 7 + header[6]].decode("ascii", "replace")
            return valid, byte_order, file_count, volume_name
    return None


def _ucsd_volume(data: bytes) -> tuple[bytes, str, int, str]:
    best: tuple[int, bytes, str, int, str] | None = None
    even_odd = tuple(range(0, 16, 2)) + tuple(range(1, 16, 2))
    for offset in range(0, min(len(data), 128 * 256), 256):
        physical = data[offset:]
        variants = [physical]
        logical = bytearray()
        for track_start in range(0, len(physical), 4096):
            track = physical[track_start : track_start + 4096]
            if len(track) < 4096:
                logical.extend(track)
                continue
            for sector in even_odd:
                logical.extend(track[sector * 256 : (sector + 1) * 256])
        variants.append(bytes(logical))
        for variant in variants:
            candidate = _ucsd_candidate(variant)
            if candidate is None:
                continue
            valid, byte_order, file_count, volume_name = candidate
            if best is None or valid > best[0]:
                best = valid, variant, byte_order, file_count, volume_name
    if best is None:
        raise ValueError("UCSD p-System volume directory not found")
    _valid, logical_data, byte_order, file_count, volume_name = best
    return logical_data, byte_order, file_count, volume_name


def extract_ucsd(data: bytes, destination: Path) -> tuple[str, list[tuple[str, int]]]:
    data, byte_order, file_count, volume_name = _ucsd_volume(data)
    directory = 1024
    destination.mkdir(parents=True, exist_ok=True)
    extracted: list[tuple[str, int]] = []
    for index in range(file_count):
        entry = data[directory + 26 + index * 26 : directory + 52 + index * 26]
        if len(entry) < 26:
            break
        first = int.from_bytes(entry[0:2], byte_order)
        after = int.from_bytes(entry[2:4], byte_order)
        name_length = min(entry[6], 15)
        name = entry[7 : 7 + name_length].decode("ascii", "replace")
        bytes_last = int.from_bytes(entry[22:24], byte_order)
        if not name or after <= first:
            continue
        extent_size = (after - first) * 512
        size = extent_size if not 0 < bytes_last <= 512 else extent_size - 512 + bytes_last
        payload = data[first * 512 : first * 512 + size]
        output = destination / _safe_name(name.upper())
        output.write_bytes(payload)
        extracted.append((output.name, len(payload)))
    return volume_name, extracted


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--filesystem", choices=("raw", "cpm", "ucsd"), default="raw")
    parser.add_argument("--profile", choices=tuple(CPM_PROFILES), default="p2000c-640")
    parser.add_argument("image", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--fill", type=lambda value: int(value, 0), default=0)
    arguments = parser.parse_args()
    sectors = read_sectors(arguments.image)
    data = raw_bytes(sectors, arguments.fill)
    if arguments.filesystem == "raw":
        arguments.output.write_bytes(data)
        detail = ""
    elif arguments.filesystem == "cpm":
        files = extract_cpm(data, arguments.output, arguments.profile)
        detail = f"; extracted={len(files)}"
    else:
        volume, files = extract_ucsd(data, arguments.output)
        detail = f"; volume={volume}; extracted={len(files)}"
    sizes = sorted({len(sector.data) for sector in sectors if sector.data is not None})
    errors = sum(sector.status != "ok" for sector in sectors)
    print(f"{len(sectors)} sectors; sizes={sizes}; read_errors={errors}{detail}")


if __name__ == "__main__":
    main()
