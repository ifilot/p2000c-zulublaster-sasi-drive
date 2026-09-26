"""Safe construction of blank P2000C disk images."""

from __future__ import annotations

import os
from pathlib import Path
import tempfile

from . import constants
from .layout import LayoutDetectionError, detect_image_layout


class BuildError(ValueError):
    """Raised when an image cannot be built from the supplied inputs."""


def _read_system_tracks(path: Path) -> bytes:
    try:
        size = path.stat().st_size
    except OSError as exc:
        raise BuildError(f"cannot access system-track file {path}: {exc}") from exc
    if size != constants.SYSTEM_AREA_SIZE:
        raise BuildError(
            f"system-track file must be exactly {constants.SYSTEM_AREA_SIZE} bytes; got {size}"
        )
    try:
        data = path.read_bytes()
    except OSError as exc:
        raise BuildError(f"cannot read system-track file {path}: {exc}") from exc
    if len(data) != constants.SYSTEM_AREA_SIZE:
        raise BuildError(
            "system-track file changed while being read; "
            f"expected {constants.SYSTEM_AREA_SIZE} bytes, got {len(data)}"
        )
    return data


def build_image(
    output: str | Path,
    system_tracks: str | Path | None = None,
    *,
    overwrite: bool = True,
    layout: str = "auto",
) -> Path:
    """Atomically build a fill-byte image, optionally installing system tracks."""
    if layout not in {"auto", "single", "split"}:
        raise BuildError("layout must be auto, single, or split")
    destination = Path(output)
    system_data = _read_system_tracks(Path(system_tracks)) if system_tracks else None
    if layout == "split" and system_data is None:
        raise BuildError(
            "a split image requires --system tracks containing the low and high DPBs"
        )
    if system_data is not None:
        try:
            detected = detect_image_layout(system_data)
        except LayoutDetectionError as exc:
            if layout == "split":
                raise BuildError(
                    f"system-track file does not contain a supported split layout: {exc}"
                ) from exc
        else:
            if layout != "auto" and detected.mode != layout:
                raise BuildError(
                    f"requested {layout} layout but system-track file describes "
                    f"a {detected.mode} layout"
                )
    if os.path.lexists(destination) and not overwrite:
        raise FileExistsError(f"output file already exists: {destination}")
    if not destination.parent.exists():
        raise BuildError(f"output directory does not exist: {destination.parent}")

    temporary_path: Path | None = None
    try:
        fd, temporary_name = tempfile.mkstemp(
            prefix=f".{destination.name}.", suffix=".tmp", dir=destination.parent
        )
        temporary_path = Path(temporary_name)
        with os.fdopen(fd, "wb") as stream:
            chunk = bytes([constants.DEFAULT_FILL_BYTE]) * (1024 * 1024)
            remaining = constants.IMAGE_SIZE
            while remaining:
                part = chunk[: min(remaining, len(chunk))]
                stream.write(part)
                remaining -= len(part)
            if system_data is not None:
                stream.seek(0)
                stream.write(system_data)
            stream.flush()
            os.fsync(stream.fileno())

        if os.path.lexists(destination) and not overwrite:
            raise FileExistsError(f"output file already exists: {destination}")
        os.replace(temporary_path, destination)
        temporary_path = None
        return destination
    except OSError as exc:
        if isinstance(exc, FileExistsError):
            raise
        raise BuildError(f"cannot build image {destination}: {exc}") from exc
    finally:
        if temporary_path is not None:
            try:
                temporary_path.unlink()
            except FileNotFoundError:
                pass
