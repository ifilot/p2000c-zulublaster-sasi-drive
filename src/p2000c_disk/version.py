"""Canonical semantic-version metadata for the P2000C SASI distribution."""
from __future__ import annotations

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
SEMANTIC_VERSION_PATTERN = re.compile(
    r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\Z"
)


def validate_semantic_version(value: str) -> str:
    """Return a stable SemVer value or reject it."""
    if not SEMANTIC_VERSION_PATTERN.fullmatch(value):
        raise ValueError(
            f"invalid semantic version {value!r}; expected MAJOR.MINOR.PATCH"
        )
    return value


def _read_version() -> str:
    """Read and validate the single repository distribution version."""
    version = (ROOT / "VERSION").read_text(encoding="ascii").strip()
    try:
        return validate_semantic_version(version)
    except ValueError as exc:
        raise RuntimeError(f"invalid VERSION value: {version!r}") from exc


VERSION = _read_version()
"""Distribution version without its presentation prefix."""

DISPLAY_VERSION = f"v{VERSION}"
"""Distribution version as shown to users and used for its Git tag."""

DISTRIBUTION_NAME = "P2000C SASI Distribution"
"""User-facing name shared by every SASI distribution variant."""
