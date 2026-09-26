from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path

import pytest

from p2000c_disk import constants
from p2000c_disk.config import (
    ConfigConsistencyError,
    ConfigCopy,
    ConfigField,
    ConfigUpdates,
    ConfigValueError,
    SystemLayoutProfile,
    UnknownSystemLayoutError,
    UnsupportedConfigEditError,
    apply_config_updates,
    effective_printer_timeout,
    inspect_config,
    plan_config_updates,
)
from p2000c_disk.image import DiskImage, ImageFormatError
from p2000c_disk.verify import verify_image


def _dpb_bytes() -> bytes:
    return (
        constants.DPB_SECTORS_PER_TRACK.to_bytes(2, "little")
        + bytes(
            [
                constants.DPB_BLOCK_SHIFT,
                constants.DPB_BLOCK_MASK,
                constants.DPB_EXTENT_MASK,
            ]
        )
        + constants.DPB_MAXIMUM_BLOCK.to_bytes(2, "little")
        + constants.DPB_MAXIMUM_DIRECTORY_ENTRY.to_bytes(2, "little")
        + bytes(constants.DPB_ALLOCATION_RESERVED)
        + constants.DPB_DIRECTORY_CHECK_SIZE.to_bytes(2, "little")
        + constants.DPB_RESERVED_TRACKS.to_bytes(2, "little")
    )


def _synthetic_recognizer(system: bytes) -> bool:
    return system[32:43] == b"SYNCONFIG1!"


def _synthetic_partial(system: bytes) -> bool:
    return system[32:35] == b"SYN"


SYNTHETIC_PROFILE = SystemLayoutProfile(
    name="synthetic-config-test-v1",
    image_size=constants.IMAGE_SIZE,
    system_area_size=constants.SYSTEM_AREA_SIZE,
    known_system_hashes=frozenset(),
    fields={
        "capslock": ConfigField(
            "capslock",
            64,
            1,
            "bitmask-flag",
            None,
            "confirmed",
            writable=True,
            bit_mask=0x03,
            enabled_value=0x02,
            disabled_value=0x01,
        ),
        "printer_timeout": ConfigField(
            "printer_timeout",
            65,
            2,
            "uint-le-units",
            None,
            "confirmed",
            writable=True,
            unit_seconds=4,
        ),
        "welcome_message": ConfigField(
            "welcome_message",
            68,
            16,
            "length-prefixed-ascii",
            None,
            "confirmed",
            writable=True,
            length_offset=67,
            capacity=16,
            allow_length_change=True,
            clear_supported=True,
            copies=(
                ConfigCopy("welcome_message_display_copy", 84, 16, "fixed-ascii"),
            ),
        ),
        "autostart": ConfigField(
            "autostart",
            101,
            32,
            "length-prefixed-ascii",
            None,
            "confirmed",
            writable=True,
            length_offset=100,
            capacity=32,
            allow_length_change=True,
            clear_supported=True,
            allowed_command_separators=";",
        ),
        "boot_drive_configuration": ConfigField(
            "boot_drive_configuration",
            140,
            10,
            "fixed-ascii",
            None,
            "confirmed",
        ),
    },
    recognizer=_synthetic_recognizer,
    partial_recognizer=_synthetic_partial,
)
SYNTHETIC_PROFILES = (SYNTHETIC_PROFILE,)


@pytest.fixture
def synthetic_config_image(blank_image: Path) -> Path:
    system = bytearray(constants.SYSTEM_AREA_SIZE)
    system[32:43] = b"SYNCONFIG1!"
    system[64] = 0xA1  # disabled value plus unrelated high bits
    system[65:67] = (5).to_bytes(2, "little")  # 20 seconds in four-second units
    system[67] = 5
    system[68:73] = b"HELLO"
    system[84:89] = b"HELLO"
    system[100] = 0
    system[140:150] = b"A:8MB-HRD1"
    offset = constants.DPB_REFERENCE_OFFSET
    system[offset : offset + 15] = _dpb_bytes()
    with blank_image.open("r+b") as stream:
        stream.seek(0)
        stream.write(system)
    assert verify_image(blank_image).is_valid
    return blank_image


def test_reference_config_is_read_only_and_recognized() -> None:
    path = Path("tests/fixtures/references/HD0_256_BOOT.hda")
    if not path.is_file():
        pytest.skip("reference image not available")
    before = sha256(path.read_bytes()).digest()
    inspection = inspect_config(path)
    assert inspection.layout_status == "recognized"
    assert inspection.profile_name == "p2000c-config-generated-v1"
    assert inspection.fields["welcome_message"].value == "Hello Ivo"
    assert len(inspection.fields["welcome_message"].sources) == 1
    assert inspection.fields["capslock"].value is None
    assert inspection.fields["printer_timeout"].value is None
    assert inspection.fields["autostart"].value == "Hello Ivo"
    assert inspection.boot_drive_configuration == "A:8MB-HRD1"
    assert sha256(path.read_bytes()).digest() == before


def test_config_json_contains_offsets_raw_copies_and_confidence() -> None:
    path = Path("tests/fixtures/references/HD0_256_BOOT.hda")
    if not path.is_file():
        pytest.skip("reference image not available")
    output = json.loads(json.dumps(inspect_config(path).to_dict()))
    welcome = output["decoded_values"]["welcome_message"]
    assert welcome["confidence"] == "confirmed"
    assert [source["offset"] for source in welcome["sources"]] == [6_838]
    assert welcome["sources"][0]["raw_hex"] == "48656C6C6F2049766F"
    assert output["layout_candidates"]


def test_synthetic_profile_reads_every_supported_field(synthetic_config_image: Path) -> None:
    inspection = inspect_config(synthetic_config_image, SYNTHETIC_PROFILES)
    assert inspection.fields["capslock"].value is False
    assert inspection.fields["printer_timeout"].value == 20
    assert inspection.fields["welcome_message"].value == "HELLO"
    assert inspection.fields["autostart"].value == ""


def test_invalid_size_and_unknown_or_partial_layout(tmp_path: Path, blank_image: Path) -> None:
    short = tmp_path / "short.hda"
    short.write_bytes(b"short")
    with pytest.raises(ImageFormatError):
        inspect_config(short, SYNTHETIC_PROFILES)
    unknown = inspect_config(blank_image, SYNTHETIC_PROFILES)
    assert unknown.layout_status == "unknown"
    with blank_image.open("r+b") as stream:
        stream.seek(32)
        stream.write(b"SYN-but-not-complete")
        stream.seek(constants.DPB_REFERENCE_OFFSET)
        stream.write(_dpb_bytes())
    partial = inspect_config(blank_image, SYNTHETIC_PROFILES)
    assert partial.layout_status == "partially recognized"
    with pytest.raises(UnknownSystemLayoutError):
        plan_config_updates(blank_image, ConfigUpdates(welcome="HELLO"), SYNTHETIC_PROFILES)


def test_reference_same_length_welcome_update_is_guarded(tmp_path: Path) -> None:
    source = Path("tests/fixtures/references/HD0_256_BOOT.hda")
    if not source.is_file():
        pytest.skip("reference image not available")
    before = source.read_bytes()
    output = tmp_path / "welcome.hda"
    _, plan, written = apply_config_updates(
        source,
        ConfigUpdates(welcome="Codex Lab"),
        output,
    )
    assert written == output
    assert [(patch.offset, len(patch.new_bytes)) for patch in plan.patches] == [(6_838, 9)]
    after = output.read_bytes()
    changed = {offset for offset, pair in enumerate(zip(before, after, strict=True)) if pair[0] != pair[1]}
    assert changed <= set(range(6_838, 6_847))
    assert after[constants.SYSTEM_AREA_SIZE :] == before[constants.SYSTEM_AREA_SIZE :]
    assert inspect_config(output).fields["welcome_message"].value == "Codex Lab"
    assert verify_image(output).is_valid
    assert source.read_bytes() == before


@pytest.mark.parametrize("value", ["Short", "This welcome is too long", "ééééééééé", "bad\ntext"])
def test_reference_rejects_unsafe_welcome_values(value: str) -> None:
    source = Path("tests/fixtures/references/HD0_256_BOOT.hda")
    if not source.is_file():
        pytest.skip("reference image not available")
    with pytest.raises((ConfigValueError, UnsupportedConfigEditError)):
        plan_config_updates(source, ConfigUpdates(welcome=value))
    with pytest.raises(UnsupportedConfigEditError):
        plan_config_updates(source, ConfigUpdates(clear_welcome=True))


def test_welcome_mismatch_aborts_edit(synthetic_config_image: Path) -> None:
    with synthetic_config_image.open("r+b") as stream:
        stream.seek(84)
        stream.write(b"OTHER")
    inspection = inspect_config(synthetic_config_image, SYNTHETIC_PROFILES)
    assert not inspection.fields["welcome_message"].consistent
    with pytest.raises(ConfigConsistencyError):
        plan_config_updates(
            synthetic_config_image,
            ConfigUpdates(welcome="NEW"),
            SYNTHETIC_PROFILES,
        )


@pytest.mark.parametrize(("value", "expected"), [("WELCOME", "WELCOME"), ("HI", "HI"), ("", "")])
def test_synthetic_welcome_replace_shorter_and_clear(
    synthetic_config_image: Path, tmp_path: Path, value: str, expected: str
) -> None:
    output = tmp_path / f"welcome-{len(value)}.hda"
    updates = ConfigUpdates(clear_welcome=True) if not value else ConfigUpdates(welcome=value)
    apply_config_updates(
        synthetic_config_image,
        updates,
        output,
        profiles=SYNTHETIC_PROFILES,
    )
    system = DiskImage(output).system_area()
    assert system[67] == len(value)
    assert system[68 : 68 + len(value)] == value.encode()
    assert system[68 + len(value) : 84] == bytes(16 - len(value))
    assert system[84 + len(value) : 100] == bytes(16 - len(value))
    assert inspect_config(output, SYNTHETIC_PROFILES).fields["welcome_message"].value == expected


def test_synthetic_welcome_rejects_invalid_values(synthetic_config_image: Path) -> None:
    for value in ("X" * 17, "naïve", "line\n"):
        with pytest.raises(ConfigValueError):
            plan_config_updates(
                synthetic_config_image,
                ConfigUpdates(welcome=value),
                SYNTHETIC_PROFILES,
            )


def test_autostart_set_multiple_clear_and_warning(
    synthetic_config_image: Path, tmp_path: Path
) -> None:
    first = tmp_path / "auto.hda"
    _, plan, _ = apply_config_updates(
        synthetic_config_image,
        ConfigUpdates(autostart="DIR;STAT"),
        first,
        profiles=SYNTHETIC_PROFILES,
    )
    assert any("run automatically" in warning for warning in plan.warnings)
    assert inspect_config(first, SYNTHETIC_PROFILES).fields["autostart"].value == "DIR;STAT"
    cleared = tmp_path / "cleared.hda"
    apply_config_updates(
        first,
        ConfigUpdates(clear_autostart=True),
        cleared,
        profiles=SYNTHETIC_PROFILES,
    )
    assert inspect_config(cleared, SYNTHETIC_PROFILES).fields["autostart"].value == ""


def test_autostart_rejects_separator_overlength_and_controls(synthetic_config_image: Path) -> None:
    for value in ("DIR|STAT", "X" * 33, "DIR\rSTAT"):
        with pytest.raises(ConfigValueError):
            plan_config_updates(
                synthetic_config_image,
                ConfigUpdates(autostart=value),
                SYNTHETIC_PROFILES,
            )


def test_capslock_changes_both_directions_and_preserves_other_bits(
    synthetic_config_image: Path, tmp_path: Path
) -> None:
    enabled = tmp_path / "enabled.hda"
    apply_config_updates(
        synthetic_config_image,
        ConfigUpdates(capslock=True),
        enabled,
        profiles=SYNTHETIC_PROFILES,
    )
    assert DiskImage(enabled).system_area()[64] == 0xA2
    assert inspect_config(enabled, SYNTHETIC_PROFILES).fields["capslock"].value is True
    disabled = tmp_path / "disabled.hda"
    apply_config_updates(
        enabled,
        ConfigUpdates(capslock=False),
        disabled,
        profiles=SYNTHETIC_PROFILES,
    )
    assert DiskImage(disabled).system_area()[64] == 0xA1


def test_capslock_unknown_flag_is_not_coerced(synthetic_config_image: Path) -> None:
    with synthetic_config_image.open("r+b") as stream:
        stream.seek(64)
        stream.write(b"\xA3")
    inspection = inspect_config(synthetic_config_image, SYNTHETIC_PROFILES)
    assert inspection.fields["capslock"].value is None
    with pytest.raises(ConfigConsistencyError):
        plan_config_updates(
            synthetic_config_image,
            ConfigUpdates(capslock=True),
            SYNTHETIC_PROFILES,
        )


@pytest.mark.parametrize(
    ("requested", "effective"), [(1, 4), (4, 4), (5, 8), (21, 24), (1_021, 1_024), (1_024, 1_024)]
)
def test_printer_timeout_rounding_and_encoding(
    synthetic_config_image: Path,
    tmp_path: Path,
    requested: int,
    effective: int,
) -> None:
    assert effective_printer_timeout(requested) == effective
    output = tmp_path / f"timeout-{requested}.hda"
    _, plan, _ = apply_config_updates(
        synthetic_config_image,
        ConfigUpdates(printer_timeout=requested),
        output,
        profiles=SYNTHETIC_PROFILES,
    )
    assert plan.effective_printer_timeout == effective
    assert DiskImage(output).system_area()[65:67] == (effective // 4).to_bytes(2, "little")
    assert inspect_config(output, SYNTHETIC_PROFILES).fields["printer_timeout"].value == effective


@pytest.mark.parametrize("requested", [0, 1_025])
def test_printer_timeout_rejects_out_of_range(
    synthetic_config_image: Path, requested: int
) -> None:
    with pytest.raises(ConfigValueError):
        plan_config_updates(
            synthetic_config_image,
            ConfigUpdates(printer_timeout=requested),
            SYNTHETIC_PROFILES,
        )


def test_dry_run_no_source_change_or_output(synthetic_config_image: Path, tmp_path: Path) -> None:
    before = synthetic_config_image.read_bytes()
    output = tmp_path / "dry-run.hda"
    _, plan, written = apply_config_updates(
        synthetic_config_image,
        ConfigUpdates(welcome="HI"),
        output,
        dry_run=True,
        profiles=SYNTHETIC_PROFILES,
    )
    assert plan.patches
    assert written is None
    assert not output.exists()
    assert synthetic_config_image.read_bytes() == before


def test_output_overwrite_default_no_clobber_and_atomic_cleanup(
    synthetic_config_image: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output = tmp_path / "output.hda"
    output.write_bytes(b"keep")
    apply_config_updates(
        synthetic_config_image,
        ConfigUpdates(welcome="HI"),
        output,
        profiles=SYNTHETIC_PROFILES,
    )
    assert output.stat().st_size == constants.IMAGE_SIZE
    output.write_bytes(b"keep")
    with pytest.raises(FileExistsError):
        apply_config_updates(
            synthetic_config_image,
            ConfigUpdates(welcome="HI"),
            output,
            overwrite=False,
            profiles=SYNTHETIC_PROFILES,
        )
    assert output.read_bytes() == b"keep"
    output.unlink()

    def fail_replace(source: os.PathLike[str] | str, destination: os.PathLike[str] | str) -> None:
        raise OSError("simulated config commit failure")

    monkeypatch.setattr("p2000c_disk.config.os.replace", fail_replace)
    with pytest.raises(OSError, match="simulated config commit failure"):
        apply_config_updates(
            synthetic_config_image,
            ConfigUpdates(welcome="HI"),
            output,
            profiles=SYNTHETIC_PROFILES,
        )
    assert not output.exists()
    assert not any(path.suffix == ".tmp" for path in tmp_path.iterdir())


def test_config_update_preserves_every_unplanned_byte(
    synthetic_config_image: Path, tmp_path: Path
) -> None:
    before = synthetic_config_image.read_bytes()
    output = tmp_path / "updated.hda"
    _, plan, _ = apply_config_updates(
        synthetic_config_image,
        ConfigUpdates(capslock=True, printer_timeout=21, autostart="DIR", welcome="HI"),
        output,
        profiles=SYNTHETIC_PROFILES,
    )
    after = output.read_bytes()
    allowed = {
        offset
        for patch in plan.patches
        for offset in range(patch.offset, patch.offset + len(patch.old_bytes))
    }
    changed = {offset for offset, (old, new) in enumerate(zip(before, after, strict=True)) if old != new}
    assert changed <= allowed
    assert after[constants.SYSTEM_AREA_SIZE :] == before[constants.SYSTEM_AREA_SIZE :]


def test_config_update_can_modify_image_in_place(
    synthetic_config_image: Path,
) -> None:
    _, plan, destination = apply_config_updates(
        synthetic_config_image,
        ConfigUpdates(welcome="HI"),
        profiles=SYNTHETIC_PROFILES,
    )
    assert plan.patches
    assert destination == synthetic_config_image
    assert inspect_config(synthetic_config_image, SYNTHETIC_PROFILES).fields[
        "welcome_message"
    ].value == "HI"
