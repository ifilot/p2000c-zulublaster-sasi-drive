"""Validate CHANGELOG.md and extract the current release notes."""
from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path
import re

from .version import DISPLAY_VERSION, ROOT, VERSION, validate_semantic_version

ENTRY_PATTERN = re.compile(
    r"^## \[(?P<version>[^]]+)\] - (?P<date>[0-9]{4}-[0-9]{2}-[0-9]{2})[ \t]*$",
    re.MULTILINE,
)


def release_notes(path: Path = ROOT / "CHANGELOG.md", version: str = VERSION) -> str:
    """Return the newest changelog entry after validating its SemVer metadata."""
    validate_semantic_version(version)
    text = path.read_text(encoding="utf-8")
    entries = list(ENTRY_PATTERN.finditer(text))
    if not entries:
        raise ValueError("CHANGELOG.md contains no versioned release entries")

    seen: set[str] = set()
    for entry in entries:
        entry_version = validate_semantic_version(entry.group("version"))
        if entry_version in seen:
            raise ValueError(f"duplicate CHANGELOG.md entry: {entry_version}")
        seen.add(entry_version)
        try:
            date.fromisoformat(entry.group("date"))
        except ValueError as exc:
            raise ValueError(
                f"invalid CHANGELOG.md date for {entry_version}: {entry.group('date')}"
            ) from exc

    newest = entries[0]
    if newest.group("version") != version:
        raise ValueError(
            f"latest CHANGELOG.md entry is {newest.group('version')}, expected {version}"
        )
    end = entries[1].start() if len(entries) > 1 else len(text)
    body = text[newest.end():end].strip()
    if not body:
        raise ValueError(f"CHANGELOG.md entry {version} has no release notes")
    return f"{newest.group(0)}\n\n{body}\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", help="require this Git tag to match VERSION")
    parser.add_argument("--output", type=Path, help="write the current entry here")
    parser.add_argument("--check", action="store_true", help="validate without printing")
    args = parser.parse_args(argv)
    try:
        if args.tag is not None and args.tag != DISPLAY_VERSION:
            raise ValueError(f"tag {args.tag!r} does not match VERSION ({DISPLAY_VERSION})")
        notes = release_notes()
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(notes, encoding="utf-8")
        elif not args.check:
            print(notes, end="")
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
