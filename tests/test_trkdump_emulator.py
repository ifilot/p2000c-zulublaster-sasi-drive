# SPDX-FileCopyrightText: 2026 P2000C SASI Distribution contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Run the capture COM under real CP/M in the bundled headless core."""
import shutil
import subprocess

import pytest

from p2000c_disk.builder import build_image
from p2000c_disk.distribution import ROOT, build_trkdump
from p2000c_disk.filesystem import list_files, put_file, read_file
from p2000c_disk.verify import require_valid_image

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def capture_template(tmp_path_factory, headless_emulator):
    if not shutil.which("z80asm"):
        pytest.skip("install z80asm")
    directory = tmp_path_factory.mktemp("capture-template")
    program = build_trkdump(directory)
    image = build_image(directory / "HD0_256.hda", ROOT / "assets/boot/hdboot-split.trk")
    put_file(image, program, partition="low")
    return [*headless_emulator, "--fast-storage", "--write-through"], image


@pytest.fixture
def capture_media(capture_template, tmp_path):
    command, template = capture_template
    image = tmp_path / "HD0_256.hda"
    shutil.copyfile(template, image)
    # Distinct contents across both halves of each 256-byte sector, all sectors
    # and both tracks: detects skew, off-by-one, half-sector, and track errors.
    system = bytes((i * 37 + i // 128 * 13 + i // 256 * 7) % 256 for i in range(8192))
    floppy = tmp_path / "source.flp"
    floppy.write_bytes(system + bytes([0xE5]) * (640 * 1024 - len(system)))
    return command + ["--hard-disk-0", str(image)], image, floppy, system


def execute(command, text, expected):
    result = subprocess.run(command + [
        "--send", text + "\\r", "--wait-for", expected, "--run", "200000",
    ], capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stdout + result.stderr
    return result.stdout


@pytest.mark.parametrize("drive", ["B", "C"])
def test_capture_matches_raw_reserved_tracks(capture_media, drive):
    command, image, floppy, system = capture_media
    original_floppy = floppy.read_bytes()
    if drive == "B":
        command += ["--wait-for", "A>", "--swap-floppy-a", str(floppy)]
    else:
        command += ["--floppy-b", str(floppy), "--wait-for", "A>"]
    execute(command, f"TRKDUMP {drive}:", "SUCCESS: A:COBOARD.TRK contains 8192 verified bytes.")
    assert read_file(image, "COBOARD.TRK", partition="low") == system
    assert floppy.read_bytes() == original_floppy
    assert {f.normalized_filename for f in list_files(image, "low")} == {"TRKDUMP.COM", "COBOARD.TRK"}
    require_valid_image(image)


def test_default_media_copies_discard_successful_guest_writes(capture_media):
    command, image, floppy, _ = capture_media
    command = [arg for arg in command if arg != "--write-through"]
    before = image.read_bytes()
    command += ["--wait-for", "A>", "--swap-floppy-a", str(floppy)]
    execute(command, "TRKDUMP B:", "SUCCESS: A:COBOARD.TRK contains 8192 verified bytes.")
    assert image.read_bytes() == before
    assert "COBOARD.TRK" not in {f.normalized_filename for f in list_files(image, "low")}


@pytest.mark.parametrize("filename", ["COBOARD.TRK", "COBOARD.TMP"])
def test_existing_capture_is_not_overwritten(capture_media, tmp_path, filename):
    command, image, floppy, _ = capture_media
    old = tmp_path / filename
    old.write_bytes(b"precious capture" * 128)
    put_file(image, old, partition="low")
    before = image.read_bytes()
    execute(command + ["--wait-for", "A>", "--swap-floppy-a", str(floppy)],
            "TRKDUMP B:", f"A:{filename} already exists")
    assert image.read_bytes() == before


def test_missing_floppy_does_not_create_a_capture(capture_media):
    command, image, _, _ = capture_media
    before = image.read_bytes()
    execute(command + ["--wait-for", "A>"], "TRKDUMP B:", "No output created.")
    assert image.read_bytes() == before


@pytest.mark.parametrize("argument", ["", "A:", "B: EXTRA"])
def test_bad_arguments_do_not_write(capture_media, argument):
    command, image, _, _ = capture_media
    before = image.read_bytes()
    execute(command + ["--wait-for", "A>"], "TRKDUMP " + argument, "Usage: TRKDUMP")
    assert image.read_bytes() == before


def test_full_destination_does_not_publish_partial_capture(capture_media, tmp_path):
    command, image, floppy, _ = capture_media
    used = {block for file in list_files(image, "low") for block in file.allocation_blocks}
    filler = tmp_path / "FILLER.DAT"
    # Match free-space fill bytes: this occupies every allocation block without
    # needlessly changing megabytes of payload while constructing the fixture.
    filler.write_bytes(bytes([0xE5]) * ((1222 - 2 - len(used)) * 4096))
    put_file(image, filler, partition="low")
    execute(command + ["--wait-for", "A>", "--swap-floppy-a", str(floppy)],
            "TRKDUMP B:", "Write/close failed.")
    names = {file.normalized_filename for file in list_files(image, "low")}
    assert "COBOARD.TRK" not in names
    assert "COBOARD.TMP" not in names
    assert read_file(image, "FILLER.DAT", partition="low") == filler.read_bytes()
    require_valid_image(image)
