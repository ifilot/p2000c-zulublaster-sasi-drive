from __future__ import annotations

from pathlib import Path

import pytest

from p2000c_disk import constants
from p2000c_disk.cli import main
from p2000c_disk.filesystem import read_file
from p2000c_disk.verify import verify_image


def test_build_inspect_extract_cli(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    system = tmp_path / "system.bin"
    prefix = b"\x00A:8MB-HRD1\x00"
    system.write_bytes(prefix + b"S" * (constants.SYSTEM_AREA_SIZE - len(prefix)))
    image = tmp_path / "disk.hda"
    assert main(["build", str(image), "--system", str(system)]) == 0
    assert main(["inspect", str(image)]) == 0
    captured = capsys.readouterr()
    assert "Valid size: yes" in captured.out
    assert "System area SHA-256:" in captured.out
    assert "Contains text resembling A:8MB-HRD1: yes" in captured.out

    extracted = tmp_path / "extracted.bin"
    assert main(["extract-system", str(image), str(extracted)]) == 0
    assert extracted.read_bytes() == system.read_bytes()
    extracted.write_bytes(b"old")
    assert main(["extract-system", str(image), str(extracted)]) == 0
    assert extracted.read_bytes() == system.read_bytes()
    assert main(["extract-system", str(image), str(extracted), "-n"]) == 1


def test_list_cli_prints_active_entries(
    blank_image: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    raw = (
        b"\x00PROGRAM COM"
        + bytes([0, 0, 0, 1])
        + (4).to_bytes(2, "little")
        + bytes(14)
    )
    with blank_image.open("r+b") as stream:
        stream.seek(constants.DIRECTORY_START_LBA * constants.SECTOR_SIZE)
        stream.write(raw)
    assert main(["list", str(blank_image)]) == 0
    captured = capsys.readouterr()
    assert "PROGRAM.COM" in captured.out
    assert "       1" in captured.out
    assert "4" in captured.out


def test_cli_reports_malformed_image_with_nonzero_exit(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    bad = tmp_path / "bad.hda"
    bad.write_bytes(b"bad")
    assert main(["inspect", str(bad)]) == 1
    captured = capsys.readouterr()
    assert "Valid size: no" in captured.out
    assert "invalid image size" in captured.err


def test_cli_build_overwrites_by_default_and_supports_no_clobber(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    output = tmp_path / "disk.hda"
    output.write_bytes(b"existing")
    assert main(["build", str(output)]) == 0
    assert output.stat().st_size == constants.IMAGE_SIZE
    before = output.read_bytes()
    assert main(["build", str(output), "--no-clobber"]) == 1
    assert output.read_bytes() == before
    assert main(["build", str(output), "--overwrite"]) == 0


def test_put_get_delete_and_verify_cli(
    blank_image: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    data = bytes(range(128))
    host = tmp_path / "host.bin"
    host.write_bytes(data)
    added = tmp_path / "added.hda"
    assert main(
        [
            "put",
            str(blank_image),
            str(host),
            "--name",
            "CLI.COM",
            "--output",
            str(added),
        ]
    ) == 0
    assert main(["verify", str(added)]) == 0
    extracted = tmp_path / "extracted.bin"
    assert main(["get", str(added), "cli.com", str(extracted)]) == 0
    assert extracted.read_bytes() == data
    deleted = tmp_path / "deleted.hda"
    assert main(
        ["delete", str(added), "CLI.COM", "--output", str(deleted)]
    ) == 0
    assert verify_image(deleted).is_valid
    output = capsys.readouterr().out
    assert "Added CLI.COM" in output
    assert "Filesystem verification: OK" in output
    assert "data blocks were not erased" in output


def test_put_many_cli_keeps_argument_order(
    blank_image: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    first = tmp_path / "FIRST.COM"
    second = tmp_path / "SECOND.COM"
    first.write_bytes(b"first")
    second.write_bytes(b"second")
    output = tmp_path / "many.hda"

    assert main(
        [
            "put-many",
            str(blank_image),
            str(first),
            str(second),
            "--output",
            str(output),
        ]
    ) == 0
    rendered = capsys.readouterr().out
    assert rendered.index("Added FIRST.COM") < rendered.index("Added SECOND.COM")
    assert verify_image(output).is_valid


def test_put_cli_replace_is_distinct_from_output_overwrite(
    blank_image: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    original = tmp_path / "original.com"
    original.write_bytes(b"old")
    populated = tmp_path / "populated.hda"
    assert main(
        [
            "put",
            str(blank_image),
            str(original),
            "--name",
            "FILE.COM",
            "--output",
            str(populated),
        ]
    ) == 0
    replacement = tmp_path / "replacement.com"
    replacement.write_bytes(b"new")
    output = tmp_path / "replaced.hda"
    assert main(
        [
            "put",
            str(populated),
            str(replacement),
            "--name",
            "FILE.COM",
            "--replace",
            "--output",
            str(output),
        ]
    ) == 0
    assert read_file(output, "FILE.COM")[:3] == b"new"
    assert "Replaced FILE.COM" in capsys.readouterr().out


def test_put_cli_defaults_to_in_place_replacement(
    blank_image: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    host = tmp_path / "FILE.COM"
    host.write_bytes(b"first")
    assert main(["put", str(blank_image), str(host)]) == 0
    host.write_bytes(b"second")
    assert main(["put", str(blank_image), str(host)]) == 0
    assert read_file(blank_image, "FILE.COM")[:6] == b"second"
    assert "Replaced FILE.COM" in capsys.readouterr().out


def test_put_cli_interactive_can_decline_in_place_update(
    blank_image: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    host = tmp_path / "FILE.COM"
    host.write_bytes(b"data")
    before = blank_image.read_bytes()
    monkeypatch.setattr("builtins.input", lambda prompt: "n")
    assert main(["put", str(blank_image), str(host), "-i"]) == 0
    assert blank_image.read_bytes() == before
    assert "Not overwritten" in capsys.readouterr().out


def test_verify_cli_returns_nonzero_for_inconsistent_image(
    blank_image: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    raw = (
        b"\x00BROKEN  DAT"
        + bytes([0, 0, 0, 1])
        + (1).to_bytes(2, "little")
        + bytes(14)
    )
    with blank_image.open("r+b") as stream:
        stream.seek(constants.DIRECTORY_START_LBA * constants.SECTOR_SIZE)
        stream.write(raw)
    assert main(["verify", str(blank_image)]) == 1
    output = capsys.readouterr().out
    assert "reserved-block-reference" in output
    assert "Filesystem verification: FAILED" in output


def test_show_config_text_and_json_cli(
    capsys: pytest.CaptureFixture[str]
) -> None:
    image = Path("tests/fixtures/references/HD0_256_BOOT.hda")
    if not image.is_file():
        pytest.skip("reference image not available")
    before = image.read_bytes()
    assert main(["show-config", str(image)]) == 0
    text_output = capsys.readouterr().out
    assert "CAPSLOCK at startup: unknown" in text_output
    assert "Welcome message: Hello Ivo" in text_output
    assert "Configuration layout: recognized" in text_output
    assert main(["show-config", str(image), "--json"]) == 0
    import json

    json_output = json.loads(capsys.readouterr().out)
    assert json_output["decoded_values"]["welcome_message"]["value"] == "Hello Ivo"
    assert json_output["decoded_values"]["welcome_message"]["sources"][0]["offset"] == 6_838
    assert json_output["decoded_values"]["autostart"]["value"] == "Hello Ivo"
    assert image.read_bytes() == before


def test_set_config_dry_run_cli_creates_nothing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    image = Path("tests/fixtures/references/HD0_256_BOOT.hda")
    if not image.is_file():
        pytest.skip("reference image not available")
    output = tmp_path / "dry-run.hda"
    assert main(
        [
            "set-config",
            str(image),
            "--welcome",
            "Codex Lab",
            "--output",
            str(output),
            "--dry-run",
        ]
    ) == 0
    rendered = capsys.readouterr().out
    assert "Field: welcome_message" in rendered
    assert "Old bytes:" in rendered
    assert "New bytes:" in rendered
    assert "Dry run: no output file was created" in rendered
    assert not output.exists()


def test_set_config_rejects_no_settings_and_unsupported_real_fields(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    image = Path("tests/fixtures/references/HD0_256_BOOT.hda")
    if not image.is_file():
        pytest.skip("reference image not available")
    output = tmp_path / "output.hda"
    assert main(["set-config", str(image), "--output", str(output)]) == 1
    assert "at least one configuration setting" in capsys.readouterr().err
    assert main(
        [
            "set-config",
            str(image),
            "--printer-timeout",
            "21",
            "--output",
            str(output),
        ]
    ) == 1
    captured = capsys.readouterr()
    assert "Requested printer timeout: 21 seconds" in captured.out
    assert "Effective printer timeout: 24 seconds" in captured.out
    assert "unsupported for system layout" in captured.err
    assert not output.exists()
