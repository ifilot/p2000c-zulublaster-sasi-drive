from __future__ import annotations

import json
from pathlib import Path

import pytest

from p2000c_disk import constants
from p2000c_disk.allocation import (
    CANDIDATE_BLOCK_SIZES,
    AllocationAnalysisReport,
    MappingCandidate,
    analyze_allocation,
)
from p2000c_disk.builder import build_image
from p2000c_disk.cli import main


def _directory_entry(allocation: bytes = b"\x04" + b"\x00" * 15) -> bytes:
    assert len(allocation) == 16
    return b"\x00HELLO   COM" + bytes([0, 0, 0, 1]) + allocation


def _image_with_file(tmp_path: Path, name: str = "after.hda") -> Path:
    path = build_image(tmp_path / name)
    with path.open("r+b") as stream:
        stream.seek(constants.DIRECTORY_START_LBA * constants.SECTOR_SIZE)
        stream.write(_directory_entry())
        stream.seek(7_904 * constants.SECTOR_SIZE)
        stream.write(b"synthetic file record".ljust(128, b"\x1a"))
    return path


def _candidate(
    report: AllocationAnalysisReport,
    *,
    interpretation: str,
    block_size: int,
    anchor: str,
) -> MappingCandidate:
    return next(
        candidate
        for candidate in report.images[0].candidates
        if candidate.interpretation == interpretation
        and candidate.block_size_sectors == block_size
        and candidate.anchor_name == anchor
    )


def test_analysis_preserves_raw_values_and_physical_observations(tmp_path: Path) -> None:
    image = _image_with_file(tmp_path)
    report = analyze_allocation(image)
    analysis = report.images[0]

    assert len(analysis.active_entries) == 1
    entry = analysis.active_entries[0]
    assert entry.raw_hex == "04000000000000000000000000000000"
    assert (entry.extent, entry.s1, entry.s2, entry.record_count) == (0, 0, 0, 1)
    assert entry.raw_bytes_decimal == (4,) + (0,) * 15
    assert entry.u8_values == (4,) + (0,) * 15
    assert entry.u16le_values == (4,) + (0,) * 7
    assert analysis.non_fill_sectors == (constants.DIRECTORY_START_LBA, 7_904)
    assert analysis.unclassified_non_fill_sectors == (7_904,)
    assert analysis.confirmed_mappings == ()


def test_every_requested_block_size_is_tested_for_both_encodings(tmp_path: Path) -> None:
    report = analyze_allocation(_image_with_file(tmp_path))
    candidates = report.images[0].candidates
    for interpretation in ("u8", "u16le"):
        assert {
            candidate.block_size_sectors
            for candidate in candidates
            if candidate.interpretation == interpretation
        } == set(CANDIDATE_BLOCK_SIZES)


def test_ambiguous_realistic_mappings_remain_candidates(tmp_path: Path) -> None:
    report = analyze_allocation(_image_with_file(tmp_path))

    directory_relative = _candidate(
        report, interpretation="u16le", block_size=16, anchor="directory-start"
    )
    assert directory_relative.classification == "candidate"
    assert directory_relative.matched_non_fill_sectors == (7_904,)
    assert directory_relative.predicted_ranges[0].start_lba == 7_904
    assert directory_relative.predicted_ranges[0].end_lba == 7_919

    after_directory = _candidate(
        report, interpretation="u16le", block_size=8, anchor="after-directory"
    )
    assert after_directory.classification == "candidate"
    assert after_directory.predicted_ranges[0].start_lba == 7_904

    contradictory = _candidate(
        report, interpretation="u16le", block_size=4, anchor="directory-start"
    )
    assert contradictory.classification == "inconsistent"
    assert contradictory.unexplained_non_fill_sectors == (7_904,)


def test_uncovered_data_is_reported_as_an_inconsistency(tmp_path: Path) -> None:
    image = _image_with_file(tmp_path)
    with image.open("r+b") as stream:
        stream.seek(8_000 * constants.SECTOR_SIZE)
        stream.write(b"unexplained")
    report = analyze_allocation(image)
    candidate = _candidate(
        report, interpretation="u16le", block_size=16, anchor="directory-start"
    )
    assert candidate.classification == "inconsistent"
    assert candidate.unexplained_non_fill_sectors == (8_000,)
    assert "does not cover" in candidate.reasons[0]


def test_compare_before_and_after_correlates_changed_entry_and_sector(tmp_path: Path) -> None:
    before = build_image(tmp_path / "before.hda")
    after = _image_with_file(tmp_path)
    report = analyze_allocation(before, after)
    comparison = report.comparison
    assert comparison is not None
    assert comparison.changed_sectors == (constants.DIRECTORY_START_LBA, 7_904)
    assert comparison.changed_non_fill_sectors == (7_904,)
    assert comparison.changed_to_fill_sectors == ()
    assert comparison.relevant_after_entry_indices == (0,)
    assert len(comparison.directory_changes) == 1
    assert comparison.directory_changes[0].change == "added"
    assert comparison.directory_changes[0].after_filename == "HELLO.COM"
    assert comparison.confirmed_mappings == ()
    assert any(candidate.classification == "candidate" for candidate in comparison.candidates)


def test_json_cli_report_is_machine_readable(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    image = _image_with_file(tmp_path)
    assert main(["analyze-allocation", str(image), "--json"]) == 0
    output = json.loads(capsys.readouterr().out)
    entry = output["images"][0]["active_entries"][0]
    assert entry["raw_hex"] == "04000000000000000000000000000000"
    assert entry["raw_bytes_decimal"][0] == 4
    assert output["images"][0]["confirmed_mappings"] == []
    assert {candidate["block_size_sectors"] for candidate in output["images"][0]["candidates"]} == set(
        CANDIDATE_BLOCK_SIZES
    )


def test_text_cli_displays_hex_decimal_and_candidate_status(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    image = _image_with_file(tmp_path)
    assert main(["analyze-allocation", str(image)]) == 0
    output = capsys.readouterr().out
    assert "[00]=0x04 (4)" in output
    assert "Physical non-0xE5 ranges: 7840, 7904" in output
    assert "[candidate] encoding=u16le block=16 sectors anchor=directory-start" in output
    assert "[inconsistent]" in output
    assert "Confirmed mappings: none" in output
    assert "this is not confirmation" in output


def test_comparison_json_uses_first_image_as_before(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    before = build_image(tmp_path / "before.hda")
    after = _image_with_file(tmp_path)
    assert main(["analyze-allocation", str(before), str(after), "--json"]) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["comparison"]["before_path"] == str(before)
    assert output["comparison"]["after_path"] == str(after)
    assert output["comparison"]["changed_non_fill_sectors"] == [7_904]
