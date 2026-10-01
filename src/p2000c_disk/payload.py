# SPDX-FileCopyrightText: 2026 P2000C SASI Distribution contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Read the shared drive configuration before starting a distribution build."""
from __future__ import annotations

import json
from pathlib import Path

from .filesystem import normalize_cpm_filename


def load_payload(path: Path, root: Path) -> tuple[dict, dict[str, dict[int, list[Path]]]]:
    config = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(config, dict) or set(config) != {"drives"}:
        raise ValueError("Configuration needs exactly 'drives'")
    drives = config["drives"]
    if not isinstance(drives, dict) or set(drives) != set("ADEF"):
        raise ValueError("Configure SASI drives A, D, E and F; B/C are floppies and G is RAM")
    library = (root / "assets/software").resolve()
    payload: dict[str, dict[int, list[Path]]] = {}
    for drive, configured in drives.items():
        areas = {"0": configured} if isinstance(configured, list) else configured
        if not isinstance(areas, dict) or not areas:
            raise ValueError(f"Drive {drive}: expected a list or user-area object")
        payload[drive] = {}
        for user_text, patterns in areas.items():
            if (not isinstance(user_text, str) or not user_text.isdecimal()
                    or not 0 <= int(user_text) <= 15 or str(int(user_text)) != user_text):
                raise ValueError(f"Drive {drive}: user areas must be strings from '0' through '15'")
            user = int(user_text)
            if not isinstance(patterns, list):
                raise ValueError(f"Drive {drive} user {user}: expected a list of file patterns")
            selected: dict[str, Path] = {}
            for pattern in patterns:
                if (not isinstance(pattern, str) or not pattern or "\\" in pattern
                        or Path(pattern).is_absolute() or ".." in Path(pattern).parts):
                    raise ValueError(f"Drive {drive} user {user}: use paths relative to assets/software")
                matches = sorted(library.glob(pattern))
                if not matches:
                    raise ValueError(f"Drive {drive} user {user}: no files match {pattern!r}")
                for source in matches:
                    if not source.is_file() or not source.resolve().is_relative_to(library):
                        raise ValueError(f"Not a software file inside assets/software: {source}")
                    name = normalize_cpm_filename(source.name)
                    reserved = ((drive == "A" and user == 0 and name == "TRKDUMP.COM")
                                or (drive == "D" and user == 0 and
                                    name in {"CPMHELP.COM", "CPMHELP.TXT"}))
                    if name in selected or reserved:
                        raise ValueError(f"Drive {drive} user {user}: duplicate or reserved filename {name}")
                    selected[name] = source
            payload[drive][user] = list(selected.values())
    return config, payload
