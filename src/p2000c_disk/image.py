# SPDX-FileCopyrightText: 2026 P2000C SASI Distribution contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Immutable, read-only disk-image inspection."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import os
from pathlib import Path
import tempfile
from typing import BinaryIO, Iterator

from . import constants


class ImageFormatError(ValueError):
    """Raised when an image does not match the required disk format."""


@dataclass(frozen=True, slots=True)
class SectorRange:
    """An inclusive contiguous range of LBAs."""

    start: int
    end: int

    def __str__(self) -> str:
        return str(self.start) if self.start == self.end else f"{self.start}-{self.end}"


@dataclass(frozen=True, slots=True)
class DiskImage:
    """A path-backed image reader that never opens its image for writing."""

    path: Path

    def __init__(self, path: str | Path) -> None:
        object.__setattr__(self, "path", Path(path))

    @property
    def size(self) -> int:
        try:
            return self.path.stat().st_size
        except OSError as exc:
            raise ImageFormatError(f"cannot access image {self.path}: {exc}") from exc

    @property
    def is_valid_size(self) -> bool:
        return self.size == constants.IMAGE_SIZE

    def validate_size(self) -> None:
        actual = self.size
        if actual != constants.IMAGE_SIZE:
            raise ImageFormatError(
                f"invalid image size: expected {constants.IMAGE_SIZE} bytes, got {actual}"
            )

    def _open(self) -> BinaryIO:
        try:
            return self.path.open("rb")
        except OSError as exc:
            raise ImageFormatError(f"cannot read image {self.path}: {exc}") from exc

    def read_range(self, offset: int, length: int) -> bytes:
        """Read a byte range after validating it against the known geometry."""
        self.validate_size()
        if offset < 0:
            raise ValueError("offset must be non-negative")
        if length < 0:
            raise ValueError("length must be non-negative")
        if offset + length > constants.IMAGE_SIZE:
            raise ValueError(
                f"byte range {offset}:{offset + length} exceeds image size "
                f"{constants.IMAGE_SIZE}"
            )
        with self._open() as stream:
            stream.seek(offset)
            data = stream.read(length)
        if len(data) != length:
            raise ImageFormatError(f"short read: requested {length} bytes, got {len(data)}")
        return data

    def read_sector(self, lba: int) -> bytes:
        if not 0 <= lba < constants.SECTOR_COUNT:
            raise ValueError(
                f"LBA must be between 0 and {constants.SECTOR_COUNT - 1}, got {lba}"
            )
        return self.read_range(lba * constants.SECTOR_SIZE, constants.SECTOR_SIZE)

    def system_area(self) -> bytes:
        return self.read_range(0, constants.SYSTEM_AREA_SIZE)

    def system_area_sha256(self) -> str:
        return sha256(self.system_area()).hexdigest()

    def extract_system(self, output: str | Path, *, overwrite: bool = True) -> None:
        """Write the system area, replacing an existing destination by default."""
        destination = Path(output)
        data = self.system_area()
        if os.path.lexists(destination) and not overwrite:
            raise FileExistsError(f"output file already exists: {destination}")
        if not destination.parent.is_dir():
            raise OSError(f"output directory does not exist: {destination.parent}")
        temporary: Path | None = None
        try:
            descriptor, name = tempfile.mkstemp(
                prefix=f".{destination.name}.", suffix=".tmp", dir=destination.parent
            )
            temporary = Path(name)
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            if os.path.lexists(destination) and not overwrite:
                raise FileExistsError(f"output file already exists: {destination}")
            os.replace(temporary, destination)
            temporary = None
        except FileExistsError as exc:
            raise FileExistsError(f"output file already exists: {destination}") from exc
        except OSError as exc:
            raise OSError(f"cannot write system-track file {destination}: {exc}") from exc
        finally:
            if temporary is not None:
                try:
                    temporary.unlink()
                except FileNotFoundError:
                    pass

    def non_fill_sectors(self, fill_byte: int = constants.DEFAULT_FILL_BYTE) -> tuple[int, ...]:
        """Return every LBA whose sector is not entirely the chosen byte."""
        if not 0 <= fill_byte <= 0xFF:
            raise ValueError("fill byte must be between 0 and 255")
        self.validate_size()
        expected = bytes([fill_byte]) * constants.SECTOR_SIZE
        sectors: list[int] = []
        with self._open() as stream:
            for lba in range(constants.SECTOR_COUNT):
                sector = stream.read(constants.SECTOR_SIZE)
                if len(sector) != constants.SECTOR_SIZE:
                    raise ImageFormatError(f"short read in sector {lba}")
                if sector != expected:
                    sectors.append(lba)
        return tuple(sectors)

    def non_fill_ranges(
        self, fill_byte: int = constants.DEFAULT_FILL_BYTE
    ) -> tuple[SectorRange, ...]:
        return sector_ranges(self.non_fill_sectors(fill_byte))

    def system_ascii_strings(self, minimum_length: int = 4) -> tuple[str, ...]:
        """Find runs of printable seven-bit ASCII in the system area."""
        if minimum_length < 1:
            raise ValueError("minimum length must be at least 1")
        strings: list[str] = []
        current = bytearray()
        for value in self.system_area():
            if 0x20 <= value <= 0x7E:
                current.append(value)
            else:
                if len(current) >= minimum_length:
                    strings.append(current.decode("ascii"))
                current.clear()
        if len(current) >= minimum_length:
            strings.append(current.decode("ascii"))
        return tuple(strings)


def sector_ranges(sectors: tuple[int, ...]) -> tuple[SectorRange, ...]:
    """Group an ordered tuple of LBAs into inclusive contiguous ranges."""
    return tuple(_group_consecutive(sectors))


def _group_consecutive(sectors: tuple[int, ...]) -> Iterator[SectorRange]:
    if not sectors:
        return
    start = previous = sectors[0]
    for lba in sectors[1:]:
        if lba != previous + 1:
            yield SectorRange(start, previous)
            start = lba
        previous = lba
    yield SectorRange(start, previous)
