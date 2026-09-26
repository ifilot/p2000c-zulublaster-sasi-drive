import configparser
from hashlib import sha256
import json
from pathlib import Path

import pytest

from p2000c_disk.config import inspect_config
from p2000c_disk.distribution import (
    ROOT, build_distribution, build_trkdump, digest, main, package_name,
    system_tracks, verify_distribution,
)
from p2000c_disk.filesystem import list_files, read_file
from p2000c_disk.games import _cache_root, load_game_lock
from p2000c_disk.image import DiskImage


def test_pro_builds_all_drives_reproducibly(tmp_path):
    output = build_distribution("pro", tmp_path)
    assert DiskImage(output / "HD0_256.hda").system_area() == (ROOT / "assets/boot/hdboot-split.trk").read_bytes()
    assert inspect_config(output / "HD0_256.hda").fields["autostart"].value == ""
    manifest = json.loads((output / "manifest.json").read_text())
    assert manifest["schema"] == 4
    assert manifest["name"] == "P2000C SASI Distribution"
    assert manifest["version"] == "1.0.0"
    assert (output / "VERSION.txt").read_text() == "P2000C SASI Distribution v1.0.0\n"
    expected = {("HD0_256.hda", "low"): 20, ("HD0_256.hda", "high"): 14,
                ("HD1_256.hda", "low"): 0, ("HD1_256.hda", "high"): 16}
    for (image, partition), count in expected.items():
        assert len(list_files(output / image, partition)) == count
    assert "RAMTEST.COM" not in {f.normalized_filename for f in list_files(output / "HD0_256.hda", "low")}
    assert read_file(output / "HD1_256.hda", "ZORK1.DAT", partition="high")
    cache = _cache_root(ROOT / "games.lock.toml")
    for game in load_game_lock():
        for artifact in game.artifacts:
            original = cache / game.identifier / Path(artifact.path).name
            deployed = read_file(output / "HD1_256.hda", original.name, partition="high")
            assert deployed.startswith(original.read_bytes())
            assert deployed[len(original.read_bytes()):] == bytes([0x1A]) * (len(deployed) - len(original.read_bytes()))
            assert sha256(original.read_bytes()).hexdigest() == artifact.sha256
    assert "DIAG.COM" not in {file.normalized_filename for file in list_files(output / "HD1_256.hda", "high")}
    assert read_file(output / "HD0_256.hda", "KERMIT.COM", partition="low") == (ROOT / "assets/software/cpm/communications/kermit/KERMIT.COM").read_bytes()
    applications = list_files(output / "HD0_256.hda", "high")
    assert {file.normalized_filename for file in applications if file.user_number == 3} == {
        "SC2.COM", "SC2.OVL", "SC2.HLP",
    }
    for name in ("SC2.COM", "SC2.OVL", "SC2.HLP"):
        assert read_file(output / "HD0_256.hda", name, partition="high", user_number=3) == (
            ROOT / "assets/software/cpm/applications/supercalc-2" / name
        ).read_bytes()
    assert {(file.user_number, file.normalized_filename) for file in applications} >= {
        (0, "README.COM"), (1, "MBASIC.COM"), (2, "COBOL.COM"),
        (3, "SC2.COM"),
    }
    assert not {file.normalized_filename for file in applications if file.user_number == 4}
    assert b"WordStar" not in read_file(
        output / "HD0_256.hda", "README.COM", partition="high", user_number=0
    )
    mbasic = read_file(
        output / "HD0_256.hda", "MBASIC.COM", partition="high", user_number=1
    )
    assert mbasic == (ROOT / "assets/software/cpm/development/basic-80/MBASIC.COM").read_bytes()
    assert sha256(mbasic).hexdigest() == "29d957fc6899c24f6296a1662a27eca545d85ee3f7d70d2794c9d045d92ff157"
    before = {p.relative_to(output): digest(p) for p in output.rglob("*") if p.is_file()}
    build_distribution("pro", tmp_path)
    assert before == {p.relative_to(output): digest(p) for p in output.rglob("*") if p.is_file()}
    verify_distribution(output)


def test_supercalc_uses_p2000c_terminal_profile():
    program = ROOT / "assets/software/cpm/applications/supercalc-2/SC2.COM"
    data = program.read_bytes()
    assert sha256(data).hexdigest() == "1967497109491a0b3d7754ef132c735c541a70dc77c2cd826a2938500eca2412"
    assert data[0x80:0x8F] == b"P2000C VT52   \0"
    assert data[0xF4:0xFA] == bytes([1, 12, 0, 0, 0, 0])
    assert data[0x15F:0x167] == bytes([1, 5, 1, 24, 1, 19, 1, 4])
    assert data[0xEB:0xF4] == bytes([1, 1]) + bytes(7)
    assert data[0x106:0x10F] == bytes([2, 27, ord("k")]) + bytes(6)
    assert data[0x123:0x12C] == bytes([3, 27, ord("0"), 0x50]) + bytes(5)
    assert data[0x12C:0x135] == bytes([3, 27, ord("0"), 0x40]) + bytes(5)


def test_coboard_is_an_independent_switch_and_requires_tracks(tmp_path, capsys):
    assert package_name("pro", True) == "pro-coboard"
    assert main(["dist", "--variant", "pro", "--coboard", "--coboard-system",
                 str(tmp_path / "missing.trk"), "--dist", str(tmp_path / "dist")]) == 1
    assert "verified CONFIG-generated SASI boot tracks" in capsys.readouterr().err
    assert not (tmp_path / "dist").exists()
    with pytest.raises(ValueError, match="include G"):
        system_tracks(True, ROOT / "assets/boot/hdboot-split.trk")
    with pytest.raises(ValueError, match="requires --coboard"):
        system_tracks(False, ROOT / "assets/boot/hdboot-split.trk")


@pytest.mark.parametrize("change,expected", [
    (lambda c: c["drives"]["A"].append("core/ASM.COM"), "duplicate"),
    (lambda c: c["drives"].update(G=[]), "SASI drives"),
    (lambda c: c["drives"]["F"].append("../secret"), "relative"),
    (lambda c: c["drives"]["F"].append("nothing/*.COM"), "no files match"),
])
def test_invalid_configuration_fails_before_publishing(tmp_path, change, expected):
    config = json.loads((ROOT / "distribution.json").read_text())
    change(config)
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(config))
    with pytest.raises(ValueError, match=expected):
        build_distribution("pro", tmp_path / "dist", config=path)
    assert not (tmp_path / "dist").exists()


def test_verify_detects_changed_configuration(tmp_path):
    output = build_distribution("pro", tmp_path)
    (output / "zuluscsi.ini").write_text("[SCSI]\nEnableParity=1\n")
    with pytest.raises(ValueError, match="changed package file"):
        verify_distribution(output)


def test_zuluscsi_configuration_has_real_ini_lines():
    parser = configparser.ConfigParser()
    parser.read(ROOT / "assets/zuluscsi.ini")
    assert parser.getint("SCSI", "MapLunsToIDs") == 1
    assert parser.getint("SCSI", "EnableParity") == 0
    assert parser.getint("SCSI0", "BlockSize") == 256


def test_standalone_capture_failed_rebuild_is_atomic(tmp_path):
    program = build_trkdump(tmp_path)
    original = program.read_bytes()
    assert 0 < len(original) <= 0x3F00
    assert not list(tmp_path.rglob("*.hda"))
    assert (program.parent / "README.md").is_file()
    with pytest.raises(ValueError, match="Assembler not found"):
        build_trkdump(tmp_path, assembler="nonexistent-assembler-xyz")
    assert program.read_bytes() == original
