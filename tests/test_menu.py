"""Execute Z88DK's actual COM under the Philips CP/M BIOS, not a BDOS mock."""
import os
import re
from pathlib import Path
import shutil

import pytest

from p2000c_disk.assembly import assemble_program
from p2000c_disk.config import ConfigUpdates, apply_config_updates, inspect_config
from p2000c_disk.directory import read_directory
from p2000c_disk.distribution import build_distribution, verify_distribution
from p2000c_disk.emulator import run_scenario
from p2000c_disk.filesystem import put_files, read_file
from p2000c_disk.image import DiskImage
from p2000c_disk.menu import compile_menu_data
from p2000c_disk.menu_boot import is_menu_boot


@pytest.fixture(scope="module")
def menu_package(tmp_path_factory):
    zcc = os.environ.get("ZCC", "zcc")
    if not shutil.which(zcc):
        pytest.skip("install Z88DK or set ZCC to run compiled-menu tests")
    root = tmp_path_factory.mktemp("menu")
    return build_distribution("menu", root, zcc=zcc)


def scenario(package, headless_emulator, *actions):
    return run_scenario([
        "--hard-disk-0", str(package / "HD0_256.hda"),
        "--hard-disk-1", str(package / "HD1_256.hda"), "--fast-storage",
        "--wait-for", "Omhoog/Omlaag kiezen", *actions,
    ], command=headless_emulator)


def screen(state):
    return "\n".join(state["screen"])


def custom_package(menu_package, tmp_path, menu_toml):
    for name in ("HD0_256.hda", "HD1_256.hda"):
        shutil.copyfile(menu_package / name, tmp_path / name)
    source = tmp_path / "menu.toml"
    source.write_text(menu_toml)
    path = compile_menu_data(source, tmp_path / "MENU.DAT")
    put_files(tmp_path / "HD0_256.hda", [path], partition="low", overwrite=True)
    return tmp_path


def one_program_menu(label, command, description, *, drive="D", user=0,
                     arguments="", saver=120):
    return f"""[menu]
title = \"P2000C NAVIGATOR\"
footer = \"Home Computer Museum\"
screensaver_seconds = {saver}
[[categories]]
label = \"Programma's\"
description = \"Kies een programma.\"
[[categories.programs]]
label = \"{label}\"
drive = \"{drive}\"
user = {user}
command = \"{command}\"
arguments = \"{arguments}\"
description = \"{description}\"
"""


def test_menu_shows_loading_message_before_second_stage(menu_package, headless_emulator):
    state = run_scenario([
        "--hard-disk-0", str(menu_package / "HD0_256.hda"),
        "--hard-disk-1", str(menu_package / "HD1_256.hda"),
        "--fast-storage", "--chunk-cycles", "1000",
        "--wait-for", "Inladen menu...",
        "--wait-for", "Omhoog/Omlaag kiezen",
    ], command=headless_emulator)

    assert "P2000C NAVIGATOR" in screen(state)


def test_help_contains_build_information(menu_package, headless_emulator):
    state = scenario(
        menu_package,
        headless_emulator,
        "--send", "h",
        "--wait-for", "Druk op een toets om terug te keren",
    )

    display = screen(state)
    assert "S laadt de screensaver" in display
    assert "S spaart het scherm" not in display
    assert "R herlaadt" not in display
    assert "SASI-distributie: v1.2.0" in display
    assert "github.com/ifilot/p2000c-zulublaster-sasi-drive" in display
    assert re.search(r"Compilatiedatum: \d{4}-\d{2}-\d{2}", display)
    assert "BEDIENING" in display and "INFORMATIE" in display
    assert state["screen"][2][2] == chr(0xA9)
    assert state["screen"][2][77] == chr(0xB9)
    assert state["screen"][12][2] == chr(0xAA)
    assert state["screen"][12][77] == chr(0xBA)
    assert state["screen"][14][2] == chr(0xA9)
    assert state["screen"][14][77] == chr(0xB9)
    assert state["screen"][20][2] == chr(0xAA)
    assert state["screen"][20][77] == chr(0xBA)
    assert state["screen"][3][2] == state["screen"][15][77] == chr(0xFA)


def test_menu_boot_navigation_help_and_exit(menu_package, headless_emulator):
    verify_distribution(menu_package)
    menu_files = {
        entry.normalized_filename: entry
        for entry in read_directory(DiskImage(menu_package / "HD0_256.hda"), "low")
        if entry.user_number == 0 and entry.normalized_filename.startswith("MENU.")
    }
    assert menu_files["MENU.DAT"].is_system
    assert menu_files["MENU.BIN"].is_system
    assert not menu_files["MENU.COM"].is_system
    assert menu_files["MENU.COM"].record_count == 2
    assert 0 < menu_files["MENU.BIN"].record_count < 150
    menu_data = read_file(
        menu_package / "HD0_256.hda", "MENU.DAT", partition="low", user_number=0
    )
    launcher = read_file(
        menu_package / "HD0_256.hda", "MENU.COM", partition="low", user_number=0
    )
    assert b"Inladen menu..." in launcher
    assert menu_data.startswith(b"P2MN\x01")
    menu_source = (Path(__file__).parents[1] / "src/menu/menu.toml").read_text()
    assert "WordStar" not in menu_source and "P2EDIT" not in menu_source
    assert not (menu_package / "WORDSTAR.FLP").exists()
    state = scenario(menu_package, headless_emulator, "--run", "3000000")
    display = screen(state)
    assert "P2000C NAVIGATOR" in display
    assert "P2000C NAVIGATOR v" not in display
    assert "Home Computer Museum" in display
    assert "SASI-distro" not in display
    assert "Spellen" in display and "Kantoor" in display and "Hulpmiddelen" in display
    assert 'command = "MBASIC"' in menu_source
    assert "Zork I" in display and "Zork II" in display and "Zork III" in display
    assert "Othello" in display and "Chess" in display and "Schaken" in display
    assert "Mijnenveger" in display and "Zeeslag" in display and "Tetris" in display
    assert "Ontdek klassieke avonturen" in display
    assert "Tekstavontuur in het Grote Ondergrondse Rijk" not in display
    assert "Bestandsbeheer" not in display
    assert "Kermit overdracht" not in display
    assert "Menu-instellingen" not in display
    assert "Diskettesporen opslaan" not in display
    assert state["screen"][5][3] == chr(0xA9)
    assert state["screen"][5][22] == chr(0xB9)
    assert state["screen"][6][3] == chr(0xFA)
    assert state["screen"][9][3] == chr(0xAA)
    assert not state["cursor"]["visible"]
    state = scenario(menu_package, headless_emulator, "--send", "h",
                     "--wait-for", "Druk op een toets om terug te keren",
                     "--send", "x", "--run", "6000000",
                     "--send", "q", "--wait-for", "Navigator afsluiten",
                     "--send", "n", "--wait-for", "Omhoog/Omlaag kiezen",
                     "--send", "q", "--wait-for", "Navigator afsluiten",
                     "--send", "j", "--wait-for", "A>",
                     "--send", "DIR\\r", "--run", "6000000")
    assert state["graphics_mode"] == "character"
    assert state["nonzero_graphics_bytes"] == 0
    assert state["cursor"]["visible"]
    assert "MENU?" not in screen(state)
    assert "MENU     COM" in screen(state)
    assert "MENU     DAT" not in screen(state)


def test_tools_menu_contains_microsoft_basic(menu_package, headless_emulator):
    state = scenario(menu_package, headless_emulator,
                     "--send", "\\n\\n\\x06\\n",
                     "--wait-for", "Leer programmeren met Microsoft BASIC-80")
    display = screen(state)
    assert "Microsoft BASIC" in display
    assert "Programmagids" in display


def test_category_selection_changes_cascading_submenu(menu_package, headless_emulator,
                                                       tmp_path):
    state = scenario(menu_package, headless_emulator, "--send", "\\n", "--run", "3000000")
    display = screen(state)
    assert "SuperCalc" in display
    assert "Tekstverwerker" not in display
    assert "Zork I" not in display
    assert "Maak tabellen en berekeningen" in display
    assert "WordStar voor de P2000C" not in display

    state = scenario(menu_package, headless_emulator, "--send", "\\x06\\n",
                     "--wait-for", "Het avontuur gaat verder", "--run", "3000000")
    display = screen(state)
    assert "Het avontuur gaat verder" in display
    assert "Tekstavontuur in het Grote Ondergrondse Rijk" not in display

    # Enter Office's program panel, move within it, then return to categories.
    state = scenario(menu_package, headless_emulator, "--send", "\\n\\x06\\n\\x15\\n",
                     "--run", "8000000")
    display = screen(state)
    assert "Programmagids" in display
    assert "Tekstverwerker" not in display
    assert "Leer programmeren en ontdek" in display

    state = scenario(menu_package, headless_emulator, "--send", "\\n\\n\\x06",
                     "--wait-for", "Bekijk een overzicht van de programma's",
                     "--run", "3000000")
    display = screen(state)
    assert "Bekijk een overzicht van de programma's" in display
    assert "veilige achtergrondinformatie" not in display

    trace = tmp_path / "terminal.bin"
    scenario(menu_package, headless_emulator, "--trace-terminal", str(trace),
             "--send", "\\x06", "--run", "1000000")
    selected = b"\x1b0P" + b"Zork I".ljust(32) + b"\x1b0@"
    assert selected in trace.read_bytes()



def test_hardware_arrow_codes(menu_package, headless_emulator):
    state = scenario(menu_package, headless_emulator,
                     "--send", "\\x18",  # hardware Down (^X): Kantoor
                     "--wait-for", "Maak tabellen en berekeningen",
                     "--send", "\\x04",  # hardware Right (^D): program pane
                     "--wait-for", "Maak berekeningen en tabellen",
                     "--send", "\\x13",  # hardware Left (^S): category pane
                     "--wait-for", "Maak tabellen en berekeningen",
                     "--send", "\\x05",  # hardware Up (^E): Spellen
                     "--wait-for", "Ontdek klassieke avonturen")
    assert "Zork I" in screen(state)

def test_real_application_warm_boot_returns_to_menu(menu_package, headless_emulator):
    state = scenario(
        menu_package,
        headless_emulator,
        "--send", "\\n\\n\\x06\\r",
        "--wait-for", "D: APPLICATIONS BY CP/M USER AREA",
        "--wait-for", "Omhoog/Omlaag kiezen",
    )
    assert "P2000C NAVIGATOR" in screen(state)
    assert "MENU?" not in screen(state)
    assert not state["cursor"]["visible"]





def test_schaken_launches_from_menu(menu_package, headless_emulator):
    state = scenario(
        menu_package,
        headless_emulator,
        "--send", "\\x06" + "\\n" * 5 + "\\r",
        "--run", "24000000",
        "--send", " ",
        "--wait-for", "Sterkte van de computer",
    )
    assert state["graphics_mode"] == "character"


def test_mijnenveger_launches_from_menu(menu_package, headless_emulator):
    state = scenario(
        menu_package,
        headless_emulator,
        "--send", "\\x06" + "\\n" * 6 + "\\r",
        "--wait-for", "Kies een niveau",
        "--send", "1",
        "--run", "18000000",
        "--wait-for", "Mijnen",
    )
    assert state["graphics_mode"] == "high-512"
    assert state["nonzero_graphics_bytes"] > 0


def test_zeeslag_launches_from_menu(menu_package, headless_emulator):
    state = scenario(
        menu_package,
        headless_emulator,
        "--send", "\\x06" + "\\n" * 7 + "\\r",
        "--run", "12000000",
        "--send", " ",
        "--wait-for", "1, 2 of 3: spelen",
        "--send", "1",
        "--run", "20000000",
    )
    assert state["graphics_mode"] == "high-512"
    assert state["nonzero_graphics_bytes"] > 0


def test_tetris_launches_from_menu_in_text_mode(menu_package, headless_emulator):
    state = scenario(
        menu_package,
        headless_emulator,
        "--send", "\\x06" + "\\n" * 8 + "\\r",
        "--wait-for", "KIES STARTNIVEAU",
        "--send", "0",
        "--wait-for", "VOLGENDE",
        "--send", "q",
        "--wait-for", "KIES STARTNIVEAU",
        "--send", "q",
        "--wait-for", "Omhoog/Omlaag kiezen",
    )
    display = screen(state)
    assert state["graphics_mode"] == "character"
    assert state["nonzero_graphics_bytes"] == 0
    assert "P2000C NAVIGATOR" in display


def test_mbasic_521_launches_from_menu(menu_package, headless_emulator):
    state = scenario(
        menu_package,
        headless_emulator,
        "--send", "\\n\\n\\x06\\n\\r",
        "--wait-for", "BASIC-80 Rev. 5.21",
        "--wait-for", "Ok",
        "--send", "PRINT 6*7\\r",
        "--wait-for", " 42 ",
        "--send", "SYSTEM\\r",
        "--wait-for", "Omhoog/Omlaag kiezen",
    )
    display = screen(state)
    assert "P2000C NAVIGATOR" in display
    assert "MENU?" not in display

def test_large_com_arguments_user_and_full_memory(menu_package, tmp_path, headless_emulator):
    package = custom_package(
        menu_package, tmp_path,
        one_program_menu("Probe", "PROBE", "Large program handoff", drive="D", user=3,
                         arguments="input.txt B:*.dat"),
    )
    source = tmp_path / "probe.asm"
    source.write_text('''org 0100h
        ld (0200h),a
        ld a,c
        ld (0201h),a
        ld hl,0
        add hl,sp
        ld (0202h),hl
        ld c,25
        call 5
        ld (0204h),a
        ld c,32
        ld e,255
        call 5
        ld (0205h),a
        ld hl,(6)
        ld de,-512
        add hl,de
        ld (hl),055h
        ld a,(0c0ffh)
        ld (0206h),a
        ld de,message
        ld c,9
        call 5
wait:   ld c,6
        ld e,255
        call 5
        or a
        jr z,wait
        ret
message: db 'LARGE PROGRAM READY','$'
        defs 0c0ffh-$,0a5h
        db 05ah
''')
    probe = tmp_path / "PROBE.COM"
    assemble_program(source, probe)
    put_files(package / "HD0_256.hda", [probe], partition="high", user_number=3)
    state = scenario(package, headless_emulator, "--send", "\\r\\r",
                     "--wait-for", "LARGE PROGRAM READY",
                     "--dump-memory", "0x200:7", "--dump-memory", "0x5c:36",
                     "--dump-memory", "0x80:23")
    probe_state, fcbs, tail = [bytes.fromhex(m["bytes"]) for m in state["memory"]]
    assert probe_state[0:2] == bytes([0, 3])  # A flags and C default drive
    assert probe_state[4:] == bytes([3, 3, 0x5a])  # drive, user, last loaded byte
    assert fcbs[:12] == b"\x00INPUT   TXT"
    assert fcbs[16:28] == b"\x02????????DAT"
    assert tail.startswith(b"\x12 INPUT.TXT B:*.DAT\r")
    state = scenario(
        package,
        headless_emulator,
        "--send", "\\r\\r",
        "--wait-for", "LARGE PROGRAM READY",
        "--send", "x",
        "--wait-for", "Omhoog/Omlaag kiezen",
    )
    assert "P2000C NAVIGATOR" in screen(state)
    assert "MENU?" not in screen(state)


def test_saver_moves_and_wake_does_not_launch(menu_package, tmp_path, headless_emulator):
    package = custom_package(
        menu_package, tmp_path,
        one_program_menu("Guide", "README", "Read the guide", saver=5),
    )
    trace = tmp_path / "saver-terminal.bin"
    first = scenario(package, headless_emulator, "--trace-terminal", str(trace),
                     "--run", "28000000")
    assert "druk op een toets" in screen(first)
    assert screen(first).count("P2000C - druk op een toets") == 1
    assert "PROGRAM LIBRARY" not in screen(first)
    # Every movement starts with form feed, as in the hardware-tested Othello
    # saver, rather than trying to overwrite only the previous caption.
    assert trace.read_bytes().count(b"\x0c") >= 3
    later = scenario(package, headless_emulator, "--run", "38000000")
    assert first["screen"] != later["screen"]
    assert screen(later).count("P2000C - druk op een toets") == 1
    state = scenario(package, headless_emulator, "--send", "s", "--wait-for", "druk op een toets",
                     "--send", "\\r", "--wait-for", "Omhoog/Omlaag kiezen")
    assert "Programma's" in screen(state)
    assert state["graphics_mode"] == "character"
    assert state["nonzero_graphics_bytes"] == 0


def test_corrupt_data_and_missing_program_recover(menu_package, tmp_path, headless_emulator):
    corrupt = tmp_path / "corrupt"
    corrupt.mkdir()
    for name in ("HD0_256.hda", "HD1_256.hda"):
        shutil.copyfile(menu_package / name, corrupt / name)
    menu_data = bytearray(read_file(corrupt / "HD0_256.hda", "MENU.DAT",
                                    partition="low", user_number=0))
    menu_data[20] ^= 0x40
    path = corrupt / "MENU.DAT"
    path.write_bytes(menu_data)
    put_files(corrupt / "HD0_256.hda", [path], partition="low", overwrite=True)
    state = run_scenario([
        "--hard-disk-0", str(corrupt / "HD0_256.hda"), "--fast-storage",
        "--wait-for", "MENU.DAT is ongeldig", "--send", "q",
        "--wait-for", "Navigator afsluiten", "--send", "j", "--wait-for", "A>",
    ], command=headless_emulator)
    assert "A>" in screen(state)

    valid = tmp_path / "valid"
    valid.mkdir()
    package = custom_package(
        menu_package, valid,
        one_program_menu("Missing", "NOFILE", "Does not exist"),
    )
    state = run_scenario([
        "--hard-disk-0", str(package / "HD0_256.hda"), "--fast-storage",
        "--wait-for", "Omhoog/Omlaag kiezen", "--send", "\r\r",
        "--wait-for", "Programma niet gevonden",
    ], command=headless_emulator)
    assert "Programma niet gevonden" in screen(state)


def test_config_edits_preserve_cold_start_helper(menu_package, tmp_path):
    image = tmp_path / "system.hda"
    shutil.copyfile(menu_package / "HD0_256.hda", image)
    apply_config_updates(image, ConfigUpdates(clear_autostart=True))
    assert inspect_config(image).fields["autostart"].value == ""
    assert is_menu_boot(image.read_bytes()[:8192])


def test_menu_coboard_cold_and_warm_boot(tmp_path, headless_emulator):
    zcc = os.environ.get("ZCC", "zcc")
    if not shutil.which(zcc):
        pytest.skip("install Z88DK or set ZCC")
    package = build_distribution("menu", tmp_path, coboard=True, zcc=zcc)
    verify_distribution(package)
    assert "menu-coboard" in inspect_config(package / "HD0_256.hda").profile_name
    state = run_scenario([
        "--hard-disk-0", str(package / "HD0_256.hda"), "--copower", "--fast-storage",
        "--wait-for", "Omhoog/Omlaag kiezen",
        "--send", "\\n\\n\\x06\\r",
        "--wait-for", "D: APPLICATIONS BY CP/M USER AREA",
        "--wait-for", "Omhoog/Omlaag kiezen",
        "--send", "q", "--wait-for", "Navigator afsluiten",
        "--send", "j", "--wait-for", "A>",
        "--send", "G:\\rDIR\\r", "--wait-for", "NO FILE",
    ], command=headless_emulator)
    assert state["copower"]["enabled"]
    assert "MENU?" not in screen(state)
