# SPDX-FileCopyrightText: 2026 P2000C SASI Distribution contributors
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import json
from pathlib import Path

import pytest

from p2000c_disk import constants
from p2000c_disk.cli import main
from p2000c_disk.system_compare import compare_system_images


def _changed_image(blank_image: Path, tmp_path: Path) -> tuple[Path, Path]:
    first = tmp_path / "first.hda"
    second = tmp_path / "second.hda"
    content = blank_image.read_bytes()
    first.write_bytes(content)
    second.write_bytes(content)
    with first.open("r+b") as stream:
        stream.seek(100)
        stream.write(b"\x03OLD")
        stream.seek(200)
        stream.write(b"SAME")
    with second.open("r+b") as stream:
        stream.seek(100)
        stream.write(b"\x04NEWW")
        stream.seek(200)
        stream.write(b"SAME")
    return first, second


def test_compare_system_reports_ranges_context_candidates_and_unchanged(
    blank_image: Path, tmp_path: Path
) -> None:
    first, second = _changed_image(blank_image, tmp_path)
    report = compare_system_images((first, second))
    comparison = report.pairwise[0]
    assert comparison.changed_offsets
    assert any(item.start <= 100 <= item.end for item in comparison.changed_ranges)
    assert report.unchanged_across_all
    assert any(
        candidate.offset == 100 and candidate.value == 4
        for candidate in comparison.candidate_length_bytes
    )
    assert any(change.integer_candidates.offset == 100 for change in comparison.changes)
    assert comparison.strings_added or comparison.strings_removed or comparison.strings_moved
    assert all(item.end < constants.SYSTEM_AREA_SIZE for item in comparison.changed_ranges)


def test_compare_system_json_cli(blank_image: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    first, second = _changed_image(blank_image, tmp_path)
    assert main(["compare-system", str(first), str(second), "--json"]) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["paths"] == [str(first), str(second)]
    assert output["changed_ranges"]
    assert "integer_candidates" in output
    assert "string_differences" in output


def test_compare_system_requires_two_images(blank_image: Path) -> None:
    with pytest.raises(ValueError, match="at least two"):
        compare_system_images((blank_image,))
