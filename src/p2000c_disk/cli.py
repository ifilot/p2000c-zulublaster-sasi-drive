# SPDX-FileCopyrightText: 2026 P2000C SASI Distribution contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Command-line interface for p2000c-disk-tools."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
from typing import Sequence

from . import constants
from .allocation import (
    AllocationAnalysisReport,
    ImageAllocationAnalysis,
    MappingCandidate,
    analyze_allocation,
)
from .builder import BuildError, build_image
from .config import (
    ConfigError,
    ConfigInspection,
    ConfigPatchPlan,
    ConfigUpdates,
    apply_config_updates,
    effective_printer_timeout,
    inspect_config,
)
from .directory import DirectoryFormatError
from .filesystem import (
    CPMFileSystemError,
    delete_file,
    extract_file,
    list_files,
    normalize_cpm_filename,
    put_file,
    put_files,
)
from .image import DiskImage, ImageFormatError, sector_ranges
from .layout import (
    ImageLayout,
    LayoutDetectionError,
    PartitionLayout,
    detect_image_layout,
    find_matching_dpbs,
)
from .verify import ConsistencyError, verify_image
from .system_compare import (
    SystemComparisonReport,
    compare_system_areas,
    compare_system_images,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="p2000c-disk")
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect_parser = subparsers.add_parser("inspect", help="inspect image geometry and contents")
    inspect_parser.add_argument("image", type=Path)

    list_parser = subparsers.add_parser("list", help="list active CP/M directory entries")
    list_parser.add_argument("image", type=Path)
    list_parser.add_argument("--partition", choices=("low", "high"))

    get_parser = subparsers.add_parser("get", help="extract a CP/M file")
    get_parser.add_argument("image", type=Path)
    get_parser.add_argument("cpm_file")
    get_parser.add_argument("output", nargs="?", type=Path)
    _add_clobber_options(get_parser)
    get_parser.add_argument("--partition", choices=("low", "high"))

    put_parser = subparsers.add_parser("put", help="add or replace a host file")
    put_parser.add_argument("image", type=Path)
    put_parser.add_argument("host_file", type=Path)
    put_parser.add_argument("--name", dest="cpm_file")
    put_parser.add_argument("--output", type=Path, help="output image (default: input image)")
    _add_clobber_options(put_parser, legacy_replace=True)
    put_parser.add_argument("--partition", choices=("low", "high"))

    put_many_parser = subparsers.add_parser(
        "put-many", help="add ordered host files using one copy-on-write transaction"
    )
    put_many_parser.add_argument("image", type=Path)
    put_many_parser.add_argument("host_files", nargs="+", type=Path)
    put_many_parser.add_argument(
        "--output", type=Path, help="output image (default: input image)"
    )
    _add_clobber_options(put_many_parser, legacy_replace=True)
    put_many_parser.add_argument("--partition", choices=("low", "high"))

    delete_parser = subparsers.add_parser("delete", help="delete a file in a new image")
    delete_parser.add_argument("image", type=Path)
    delete_parser.add_argument("cpm_file")
    delete_parser.add_argument("--output", type=Path, help="output image (default: input image)")
    _add_clobber_options(delete_parser)
    delete_parser.add_argument("--partition", choices=("low", "high"))

    verify_parser = subparsers.add_parser("verify", help="check filesystem consistency")
    verify_parser.add_argument("image", type=Path)
    verify_parser.add_argument("--partition", choices=("low", "high"))

    show_config_parser = subparsers.add_parser(
        "show-config", help="inspect supported boot configuration fields"
    )
    show_config_parser.add_argument("image", type=Path)
    show_config_parser.add_argument("--json", action="store_true")

    set_config_parser = subparsers.add_parser(
        "set-config", help="safely edit supported boot configuration fields"
    )
    set_config_parser.add_argument("image", type=Path)
    set_config_parser.add_argument("--capslock", choices=("on", "off"))
    set_config_parser.add_argument("--printer-timeout", type=int)
    autostart_group = set_config_parser.add_mutually_exclusive_group()
    autostart_group.add_argument("--autostart")
    autostart_group.add_argument("--clear-autostart", action="store_true")
    welcome_group = set_config_parser.add_mutually_exclusive_group()
    welcome_group.add_argument("--welcome")
    welcome_group.add_argument("--clear-welcome", action="store_true")
    set_config_parser.add_argument(
        "--output", type=Path, help="output image (default: input image)"
    )
    _add_clobber_options(set_config_parser)
    set_config_parser.add_argument("--dry-run", action="store_true")

    compare_system_parser = subparsers.add_parser(
        "compare-system", help="compare only the system areas of two or more images"
    )
    compare_system_parser.add_argument("images", nargs="+", type=Path)
    compare_system_parser.add_argument("--json", action="store_true")

    allocation_parser = subparsers.add_parser(
        "analyze-allocation", help="test candidate allocation mappings"
    )
    allocation_parser.add_argument("image", type=Path, help="image, or before image")
    allocation_parser.add_argument(
        "comparison_image", nargs="?", type=Path, help="optional after image"
    )
    allocation_parser.add_argument(
        "--json", action="store_true", help="write the report as JSON to standard output"
    )
    allocation_parser.add_argument("--partition", choices=("low", "high"))

    extract_parser = subparsers.add_parser(
        "extract-system", help="extract the 8 KiB system area"
    )
    extract_parser.add_argument("image", type=Path)
    extract_parser.add_argument("output", type=Path)
    _add_clobber_options(extract_parser)

    build_parser = subparsers.add_parser("build", help="build a new blank image")
    build_parser.add_argument("output", type=Path)
    build_parser.add_argument("--system", type=Path, help="exactly 8192 bytes of system tracks")
    build_parser.add_argument(
        "--layout",
        choices=("auto", "single", "split"),
        default="auto",
        help="layout to require (default: detect from --system, otherwise single)",
    )
    _add_clobber_options(build_parser)
    return parser


def _add_clobber_options(
    parser: argparse.ArgumentParser, *, legacy_replace: bool = False
) -> None:
    behavior = parser.add_mutually_exclusive_group()
    behavior.add_argument(
        "-n", "--no-clobber", action="store_true", help="do not replace existing files"
    )
    behavior.add_argument(
        "-i", "--interactive", action="store_true", help="prompt before replacing a host file"
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="deprecated compatibility option; replacement is already the default",
    )
    if legacy_replace:
        parser.add_argument(
            "--replace",
            action="store_true",
            help="deprecated compatibility option; CP/M replacement is already the default",
        )


def _confirm_destination(path: Path, interactive: bool) -> bool:
    if not interactive or not os.path.lexists(path):
        return True
    try:
        answer = input(f"overwrite {path}? [y/N] ").strip().casefold()
    except EOFError:
        return False
    return answer in {"y", "yes"}


def _image_layout(path: Path) -> ImageLayout:
    return detect_image_layout(DiskImage(path).system_area())


def _choose_partition(path: Path, requested: str | None) -> PartitionLayout:
    """Select a mutation/extraction target, prompting on an interactive split image."""
    layout = _image_layout(path)
    if layout.mode == "single":
        return layout.partition(requested)
    if requested is not None:
        return layout.partition(requested)
    if not sys.stdin.isatty():
        raise LayoutDetectionError(
            "this split image needs a partition choice; add --partition low or "
            "--partition high"
        )
    while True:
        try:
            answer = input("Choose partition [low/high]: ").strip().casefold()
        except EOFError as exc:
            raise LayoutDetectionError(
                "no partition was selected; use --partition low or --partition high"
            ) from exc
        if answer in {"low", "l"}:
            return layout.partition("low")
        if answer in {"high", "h"}:
            return layout.partition("high")
        print("Please enter 'low' or 'high'.", file=sys.stderr)


def _inspect(path: Path) -> int:
    image = DiskImage(path)
    size = image.size
    valid = size == constants.IMAGE_SIZE
    print(f"Image size: {size} bytes")
    print(f"Valid size: {'yes' if valid else 'no'}")
    print(f"Sector size: {constants.SECTOR_SIZE} bytes")
    print(f"Sector count: {constants.SECTOR_COUNT}")
    if not valid:
        raise ImageFormatError(
            f"invalid image size: expected {constants.IMAGE_SIZE} bytes, got {size}"
        )

    strings = image.system_ascii_strings()
    dpbs = find_matching_dpbs(image.system_area())
    try:
        layout = detect_image_layout(image.system_area())
    except LayoutDetectionError:
        layout = None
    non_fill = image.non_fill_sectors()
    ranges = sector_ranges(non_fill)
    configuration_text = (
        constants.SPLIT_SYSTEM_CONFIGURATION_TEXT
        if layout is not None and layout.mode == "split"
        else constants.SYSTEM_CONFIGURATION_TEXT
    )
    marker = configuration_text.casefold()
    resembles_marker = any(marker in value.casefold() for value in strings)
    print(f"System area SHA-256: {image.system_area_sha256()}")
    print(f"Filesystem layout: {layout.mode if layout else 'unrecognized'}")
    if layout:
        for partition in layout.partitions:
            print(
                f"  {partition.display_name}: directory LBA "
                f"{partition.directory_start_lba}-{partition.directory_end_lba}, "
                f"DSM={partition.maximum_block}, data capacity "
                f"{partition.capacity_bytes:,} bytes"
            )
    print(
        "Confirmed-layout DPB offsets: "
        f"{', '.join(str(dpb.offset) for dpb in dpbs) or '(none)'}"
    )
    print(f"Sectors not filled with 0xE5: {len(non_fill)}")
    print(f"Non-fill ranges: {', '.join(map(str, ranges)) or '(none)'}")
    print("System-area ASCII strings:")
    if strings:
        for value in strings:
            print(f"  {value}")
    else:
        print("  (none)")
    print(
        f"Contains text resembling {configuration_text}: "
        f"{'yes' if resembles_marker else 'no'}"
    )
    return 0


def _list(path: Path, requested: str | None = None) -> int:
    layout = _image_layout(path)
    partitions = (layout.partition(requested),) if requested else layout.partitions
    for position, partition in enumerate(partitions):
        if len(partitions) > 1:
            if position:
                print()
            print(f"Partition: {partition.name} ({partition.display_name})")
        files = list_files(path, partition)
        if not files:
            print("No active CP/M files.")
            continue
        print("USER NAME         RECORDS   BYTES EXTENTS BLOCKS")
        for file in files:
            print(
                f"{file.user_number:4d} {file.normalized_filename:<12} "
                f"{file.record_count:7d} {file.size:7d} {len(file.entries):7d} "
                f"{','.join(map(str, file.allocation_blocks)) or '-'}"
            )
    return 0


def _verify(path: Path, partition: str | None = None) -> int:
    report = verify_image(path, partition)
    print(f"Image: {report.path}")
    print(f"Size: {report.image_size if report.image_size is not None else 'unavailable'}")
    if report.layout_mode:
        print(f"Filesystem layout: {report.layout_mode}")
    if report.partitions:
        print(f"Checked partitions: {', '.join(report.partitions)}")
    print(f"Active directory entries: {report.active_entry_count}")
    print(f"Files: {report.file_count}")
    for issue in report.errors:
        print(f"ERROR [{issue.code}]: {issue.message}")
    for issue in report.warnings:
        print(f"WARNING [{issue.code}]: {issue.message}")
    if report.is_valid:
        print("Filesystem verification: OK")
        return 0
    print(f"Filesystem verification: FAILED ({len(report.errors)} error(s))")
    return 1


def _config_display_value(inspection: ConfigInspection, name: str) -> str:
    field = inspection.fields.get(name)
    if field is None or field.value is None or not field.consistent:
        return "unknown"
    if isinstance(field.value, bool):
        return "enabled" if field.value else "disabled"
    if isinstance(field.value, str) and not field.value:
        return "empty"
    return str(field.value)


def _print_config(inspection: ConfigInspection) -> None:
    print(f"CAPSLOCK at startup: {_config_display_value(inspection, 'capslock')}")
    timeout = _config_display_value(inspection, "printer_timeout")
    print(f"Printer timeout: {timeout if timeout == 'unknown' else timeout + ' seconds'}")
    print(f"Autostart string: {_config_display_value(inspection, 'autostart')}")
    print(f"Welcome message: {_config_display_value(inspection, 'welcome_message')}")
    boot = inspection.boot_drive_configuration
    print(f"Boot drive configuration: {boot or 'unknown'}")
    print(f"System-area SHA-256: {inspection.system_area_sha256}")
    print(f"Configuration layout: {inspection.layout_status}")
    if inspection.profile_name:
        print(f"Layout profile: {inspection.profile_name}")
    for warning in inspection.warnings:
        print(f"WARNING: {warning}")


def _print_patch_plan(plan: ConfigPatchPlan) -> None:
    if plan.requested_printer_timeout is not None:
        print(f"Requested printer timeout: {plan.requested_printer_timeout} seconds")
        print(f"Effective printer timeout: {plan.effective_printer_timeout} seconds")
    if not plan.patches:
        print("Planned byte changes: none (requested values already match)")
    for patch in plan.patches:
        print(f"Field: {patch.field_name}")
        print(f"Offset: 0x{patch.offset:04X}-0x{patch.end_offset:04X}")
        print(f"Current decoded value: {patch.current_value!r}")
        print(f"New decoded value: {patch.new_value!r}")
        print(f"Old bytes: {patch.old_bytes.hex().upper()}")
        print(f"New bytes: {patch.new_bytes.hex().upper()}")
        print(f"Reason: {patch.reason}")
    for warning in plan.warnings:
        print(f"WARNING: {warning}")


def _print_system_comparison(report: SystemComparisonReport) -> None:
    print(f"Baseline: {report.baseline}")
    for comparison in report.pairwise:
        print(f"Compared image: {comparison.image}")
        print(
            "Changed offsets: "
            + (", ".join(f"0x{offset:04X}" for offset in comparison.changed_offsets) or "(none)")
        )
        print(
            "Changed ranges: "
            + (", ".join(map(str, comparison.changed_ranges)) or "(none)")
        )
        for change in comparison.changes:
            print(f"  Range 0x{change.start:04X}-0x{change.end:04X}")
            print(f"    old: {change.old_hex}  {change.old_ascii!r}")
            print(f"    new: {change.new_hex}  {change.new_ascii!r}")
            integers = change.integer_candidates
            print(
                "    integer candidates: "
                f"u8 {integers.old_u8}->{integers.new_u8}; "
                f"u16le {integers.old_u16le}->{integers.new_u16le}; "
                f"u16be {integers.old_u16be}->{integers.new_u16be}"
            )
            print(f"    ASCII context before: {change.ascii_context_before!r}")
            print(f"    ASCII context after:  {change.ascii_context_after!r}")
        print(
            "Strings added: "
            + (", ".join(f"0x{x.offset:04X}:{x.value!r}" for x in comparison.strings_added) or "(none)")
        )
        print(
            "Strings removed: "
            + (", ".join(f"0x{x.offset:04X}:{x.value!r}" for x in comparison.strings_removed) or "(none)")
        )
        print(
            "Strings moved: "
            + (", ".join(item.value for item in comparison.strings_moved) or "(none)")
        )
        print(
            "Candidate length bytes: "
            + (
                ", ".join(
                    f"0x{x.offset:04X}={x.value} -> {x.following_text!r}"
                    for x in comparison.candidate_length_bytes
                )
                or "(none)"
            )
        )
    print(
        "Unchanged across all samples: "
        + (", ".join(map(str, report.unchanged_across_all)) or "(none)")
    )


def _format_sectors(sectors: tuple[int, ...]) -> str:
    return ", ".join(map(str, sector_ranges(sectors))) or "(none)"


def _format_candidate_ranges(candidate: MappingCandidate) -> str:
    return ", ".join(
        f"{item.value}:LBA {item.start_lba}-{item.end_lba}"
        for item in candidate.predicted_ranges
    ) or "(none)"


def _print_candidate(candidate: MappingCandidate) -> None:
    print(
        f"  [{candidate.classification}] encoding={candidate.interpretation} "
        f"block={candidate.block_size_sectors} sectors "
        f"anchor={candidate.anchor_name} ({candidate.anchor_lba})"
    )
    print(f"    formula: {candidate.formula}")
    print(f"    values: {', '.join(map(str, candidate.allocation_values)) or '(none)'}")
    print(f"    candidate ranges: {_format_candidate_ranges(candidate)}")
    print(f"    matched non-fill sectors: {_format_sectors(candidate.matched_non_fill_sectors)}")
    print(
        "    unexplained non-fill sectors: "
        f"{_format_sectors(candidate.unexplained_non_fill_sectors)}"
    )
    if candidate.known_structure_overlaps:
        print(
            "    known-structure overlaps: "
            f"{_format_sectors(candidate.known_structure_overlaps)}"
        )
    if candidate.out_of_bounds_values:
        print(
            "    out-of-bounds values: "
            f"{', '.join(map(str, candidate.out_of_bounds_values))}"
        )
    print(f"    assessment: {'; '.join(candidate.reasons)}")


def _print_image_analysis(image: ImageAllocationAnalysis) -> None:
    print(f"Image: {image.path}")
    print(f"Partition: {image.partition}")
    print(f"Active directory entries: {len(image.active_entries)}")
    for entry in image.active_entries:
        print(
            f"  Entry {entry.index}: {entry.filename}; extent=0x{entry.extent:02X}; "
            f"S1=0x{entry.s1:02X}; S2=0x{entry.s2:02X}; "
            f"records={entry.record_count}"
        )
        print(f"    raw allocation bytes: {entry.raw_hex}")
        rendered_bytes = ", ".join(
            f"[{offset:02d}]=0x{value:02X} ({value})"
            for offset, value in enumerate(entry.raw_bytes_decimal)
        )
        print(f"    each byte, hexadecimal and decimal: {rendered_bytes}")
        rendered_words = ", ".join(
            f"[{offset:02d}-{offset + 1:02d}]=0x{value:04X} ({value})"
            for offset, value in zip(range(0, 16, 2), entry.u16le_values, strict=True)
        )
        print(f"    candidate little-endian 16-bit values: {rendered_words}")
    print(f"Physical non-0xE5 sectors: {len(image.non_fill_sectors)}")
    print(f"Physical non-0xE5 ranges: {_format_sectors(image.non_fill_sectors)}")
    print(
        "Unclassified non-0xE5 sectors outside system/directory: "
        f"{_format_sectors(image.unclassified_non_fill_sectors)}"
    )
    print(
        "Matching confirmed-layout DPB offsets: "
        f"{', '.join(map(str, image.matching_dpb_offsets)) or '(none)'}"
    )
    print("Candidate mapping tests:")
    for candidate in image.candidates:
        _print_candidate(candidate)
    print(
        "Confirmed mappings: "
        + (
            ", ".join(candidate.formula for candidate in image.confirmed_mappings)
            if image.confirmed_mappings
            else "none"
        )
    )


def _print_allocation_report(report: AllocationAnalysisReport) -> None:
    for position, image in enumerate(report.images):
        if position:
            print()
        _print_image_analysis(image)
    if report.comparison is not None:
        comparison = report.comparison
        print()
        print(f"Comparison (before): {comparison.before_path}")
        print(f"Comparison (after): {comparison.after_path}")
        print(f"Changed sectors: {_format_sectors(comparison.changed_sectors)}")
        print(
            "Changed non-fill sectors outside system/directory: "
            f"{_format_sectors(comparison.changed_non_fill_sectors)}"
        )
        print(f"Changed-to-fill sectors: {_format_sectors(comparison.changed_to_fill_sectors)}")
        if comparison.directory_changes:
            print("Directory changes:")
            for change in comparison.directory_changes:
                print(
                    f"  entry {change.index}: {change.change}; "
                    f"before={change.before_filename or '(unused)'}; "
                    f"after={change.after_filename or '(unused)'}"
                )
        else:
            print("Directory changes: none")
        print("Comparison candidate mapping tests:")
        for candidate in comparison.candidates:
            _print_candidate(candidate)
        print(
            "Confirmed comparison mappings: "
            + (
                ", ".join(candidate.formula for candidate in comparison.confirmed_mappings)
                if comparison.confirmed_mappings
                else "none"
            )
        )
    print()
    print("Caveats:")
    for caveat in report.caveats:
        print(f"  - {caveat}")


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "inspect":
            return _inspect(args.image)
        if args.command == "list":
            return _list(args.image, args.partition)
        if args.command == "get":
            partition = _choose_partition(args.image, args.partition)
            requested_output = (
                args.output
                if args.output is not None
                else Path(normalize_cpm_filename(args.cpm_file))
            )
            if not _confirm_destination(requested_output, args.interactive):
                print(f"Not overwritten: {requested_output}")
                return 0
            output = extract_file(
                args.image,
                args.cpm_file,
                args.output,
                overwrite=not args.no_clobber,
                partition=partition,
            )
            where = f" from the {partition.name} partition" if partition.name != "single" else ""
            print(f"Extracted {args.cpm_file.upper()}{where} to {output}")
            return 0
        if args.command == "put":
            partition = _choose_partition(args.image, args.partition)
            output = args.output if args.output is not None else args.image
            if not _confirm_destination(output, args.interactive):
                print(f"Not overwritten: {output}")
                return 0
            plan = put_file(
                args.image,
                args.host_file,
                args.output,
                cpm_filename=args.cpm_file,
                overwrite=not args.no_clobber,
                replace=not args.no_clobber,
                partition=partition,
            )
            print(
                f"{'Replaced' if plan.replaced_directory_indices else 'Added'} "
                f"{plan.normalized_filename}: {plan.host_size} host bytes, "
                f"{plan.record_count} CP/M record(s), {len(plan.allocation_blocks)} block(s)"
            )
            target = f" ({partition.name} partition)" if partition.name != "single" else ""
            print(f"Wrote verified image to {output}{target}")
            return 0
        if args.command == "put-many":
            partition = _choose_partition(args.image, args.partition)
            output = args.output if args.output is not None else args.image
            if not _confirm_destination(output, args.interactive):
                print(f"Not overwritten: {output}")
                return 0
            plans = put_files(
                args.image,
                args.host_files,
                args.output,
                overwrite=not args.no_clobber,
                replace=not args.no_clobber,
                partition=partition,
            )
            for plan in plans:
                print(
                    f"{'Replaced' if plan.replaced_directory_indices else 'Added'} "
                    f"{plan.normalized_filename}: {plan.host_size} host bytes, "
                    f"{plan.record_count} record(s), {len(plan.allocation_blocks)} block(s)"
                )
            target = f" ({partition.name} partition)" if partition.name != "single" else ""
            print(f"Wrote verified image to {output}{target}")
            return 0
        if args.command == "delete":
            partition = _choose_partition(args.image, args.partition)
            output = args.output if args.output is not None else args.image
            if not _confirm_destination(output, args.interactive):
                print(f"Not overwritten: {output}")
                return 0
            deleted = delete_file(
                args.image,
                args.cpm_file,
                args.output,
                overwrite=not args.no_clobber,
                partition=partition,
            )
            print(
                f"Deleted user {deleted.user_number} {deleted.normalized_filename} "
                f"from {partition.name} partition in image {output}; "
                "data blocks were not erased"
            )
            return 0
        if args.command == "verify":
            return _verify(args.image, args.partition)
        if args.command == "show-config":
            inspection = inspect_config(args.image)
            if args.json:
                print(json.dumps(inspection.to_dict(), indent=2, sort_keys=True))
            else:
                _print_config(inspection)
            return 0
        if args.command == "set-config":
            updates = ConfigUpdates(
                capslock=(args.capslock == "on") if args.capslock is not None else None,
                printer_timeout=args.printer_timeout,
                autostart=args.autostart,
                clear_autostart=args.clear_autostart,
                welcome=args.welcome,
                clear_welcome=args.clear_welcome,
            )
            if args.printer_timeout is not None:
                effective = effective_printer_timeout(args.printer_timeout)
                print(f"Requested printer timeout: {args.printer_timeout} seconds")
                print(f"Effective printer timeout: {effective} seconds")
            if args.autostart is not None:
                print(
                    "WARNING: Autostart commands execute automatically during IPL and may bypass the CP/M prompt."
                )
            output = args.output if args.output is not None else args.image
            if (
                not args.dry_run
                and not _confirm_destination(output, args.interactive)
            ):
                print(f"Not overwritten: {output}")
                return 0
            inspection, plan, destination = apply_config_updates(
                args.image,
                updates,
                args.output,
                overwrite=not args.no_clobber,
                dry_run=args.dry_run,
            )
            _print_config(inspection)
            _print_patch_plan(plan)
            if args.dry_run:
                print("Dry run: no output file was created.")
            else:
                print(f"Wrote verified configuration image to {destination}")
            return 0
        if args.command == "compare-system":
            report = compare_system_images(args.images)
            if args.json:
                aggregate = compare_system_areas(args.images)
                payload = aggregate.to_dict()
                payload.update(report.to_dict())
                print(json.dumps(payload, indent=2, sort_keys=True))
            else:
                _print_system_comparison(report)
            return 0
        if args.command == "analyze-allocation":
            report = analyze_allocation(
                args.image, args.comparison_image, partition=args.partition
            )
            if args.json:
                print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
            else:
                _print_allocation_report(report)
            return 0
        if args.command == "extract-system":
            if not _confirm_destination(args.output, args.interactive):
                print(f"Not overwritten: {args.output}")
                return 0
            DiskImage(args.image).extract_system(
                args.output, overwrite=not args.no_clobber
            )
            print(f"Extracted {constants.SYSTEM_AREA_SIZE} bytes to {args.output}")
            return 0
        if args.command == "build":
            if not _confirm_destination(args.output, args.interactive):
                print(f"Not overwritten: {args.output}")
                return 0
            build_image(
                args.output,
                args.system,
                overwrite=not args.no_clobber,
                layout=args.layout,
            )
            try:
                built_layout_name = _image_layout(args.output).mode
            except LayoutDetectionError:
                built_layout_name = "unrecognized-system"
            print(
                f"Built {constants.IMAGE_SIZE}-byte {built_layout_name} image "
                f"at {args.output}"
            )
            return 0
    except (
        BuildError,
        ConfigError,
        CPMFileSystemError,
        ConsistencyError,
        DirectoryFormatError,
        ImageFormatError,
        LayoutDetectionError,
        FileExistsError,
        OSError,
        ValueError,
    ) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
