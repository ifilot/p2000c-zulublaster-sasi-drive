# SPDX-FileCopyrightText: 2026 P2000C SASI Distribution contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Exercise the combined SASI/CoPower boot system with both original size profiles."""
import shutil
import subprocess
import sys

import pytest

from p2000c_disk.assembly import ROOT
from p2000c_disk.config import ConfigUpdates, apply_config_updates, inspect_config
from p2000c_disk.distribution import build_distribution, verify_distribution
from p2000c_disk.filesystem import list_files, put_file, read_file

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def coboard_packages(tmp_path_factory, headless_emulator):
    executable, _, ipl = headless_emulator
    if not shutil.which("z80asm"):
        pytest.skip("install z80asm")
    directory = tmp_path_factory.mktemp("coboard-packages")
    package = build_distribution("pro", directory, coboard=True)
    verify_distribution(package)
    return directory, executable, ipl


@pytest.mark.parametrize("capacity", [256, 512])
def test_ram_files_roundtrip_after_warm_boot_and_sasi_drives_stay_distinct(
        coboard_packages, tmp_path, capacity):
    directory, executable, ipl = coboard_packages
    hd0, hd1 = (tmp_path / name for name in ("HD0_256.hda", "HD1_256.hda"))
    for image in (hd0, hd1):
        shutil.copyfile(directory / "pro-coboard" / image.name, image)
    # Fill the entire 126 KiB file capacity of the 127 KiB profile. Pattern
    # changes across every byte, sector and bank; binary PIP prevents ^Z EOF.
    data = bytes((i * 37 + i // 256 * 19 + i // 65536 * 71) % 256 for i in range(126 * 1024))
    source = tmp_path / "CHECK.BIN"
    source.write_bytes(data)
    put_file(hd0, source, partition="low")
    for image, partition, drive in ((hd0, "high", "D"), (hd1, "low", "E"), (hd1, "high", "F")):
        marker = tmp_path / f"{drive}MARK.TXT"
        marker.write_bytes(f"SASI-{drive}-UNCHANGED\r\n".encode())
        put_file(image, marker, partition=partition)
    hd1_before = hd1.read_bytes()
    floppy = tmp_path / "blank.flp"
    floppy.write_bytes(bytes([0xE5]) * (640 * 1024))
    command = [executable, "--ipl", ipl, "--hard-disk-0", str(hd0), "--hard-disk-1", str(hd1),
               "--fast-storage", "--copower-ram", str(capacity), "--write-through",
               "--wait-for", "G:127K-MEM" if capacity == 256 else "G:508K-MEM",
               "--wait-for", "A>", "--swap-floppy-a", str(floppy),
               "--swap-floppy-b", str(floppy), "--send", "DIR B:\\r", "--run", "2000000",
               "--send", "DIR C:\\r", "--run", "2000000"]
    for drive in "DEF":
        command += ["--send", f"TYPE {drive}:{drive}MARK.TXT\\r", "--wait-for", f"SASI-{drive}-UNCHANGED",
                    "--run", "1000000"]
    command += ["--run", "1000000", "--send", "PIP G:=A:CHECK.BIN[OV]\\r", "--run", "60000000",
                "--send", "\\x03\\r", "--run", "2000000",
                "--send", "PIP A:BACK.BIN=G:CHECK.BIN[O]\\r", "--run", "60000000"]
    result = subprocess.run(command, capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Bdos Err" not in result.stdout
    assert "BACK.BIN" in {f.normalized_filename for f in list_files(hd0, "low")}, result.stdout
    assert read_file(hd0, "BACK.BIN", partition="low") == data
    assert read_file(hd0, "CHECK.BIN", partition="low") == data
    assert hd1.read_bytes() == hd1_before
    assert floppy.read_bytes() == bytes([0xE5]) * (640 * 1024)


def test_cpm_boots_with_coboard(coboard_packages):
    directory, executable, ipl = coboard_packages
    package = directory / "pro-coboard"
    assert inspect_config(package / "HD0_256.hda").fields["autostart"].value == ""
    result = subprocess.run([executable, "--ipl", ipl, "--hard-disk-0", str(package / "HD0_256.hda"),
                             "--hard-disk-1", str(package / "HD1_256.hda"), "--copower", "--fast-storage",
                             "--wait-for", "G:508K-MEM", "--wait-for", "A>", "--run", "1000000"],
                            capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Bdos Err" not in result.stdout


def test_configuration_edit_cannot_change_driver(coboard_packages, tmp_path):
    source = coboard_packages[0] / "pro-coboard/HD0_256.hda"
    image = tmp_path / "edit.hda"
    shutil.copyfile(source, image)
    before = image.read_bytes()[:8192]
    apply_config_updates(image, ConfigUpdates(autostart="A:MENU"))
    after = image.read_bytes()[:8192]
    assert before[:135] == after[:135] and before[264:] == after[264:]
    with image.open("r+b") as stream:
        stream.seek(0x1C99)
        stream.write(b"\x00")
    with pytest.raises(ValueError, match="editing is refused"):
        apply_config_updates(image, ConfigUpdates(clear_autostart=True))


def test_original_config_reproduces_bundled_tracks(coboard_packages):
    _, executable, ipl = coboard_packages
    result = subprocess.run([sys.executable, str(ROOT / "src/maintenance/generate_coboard.py"),
                             "--emulator", executable, "--ipl", ipl, "--check"],
                            capture_output=True, text=True, timeout=90)
    assert result.returncode == 0, result.stdout + result.stderr
