"""Check the Python/native boundary and useful failure diagnostics."""
import json
import subprocess

import pytest

from p2000c_disk.emulator import run_scenario


def test_json_state_and_memory(headless_emulator):
    state = run_scenario(["--run", "1000", "--dump-memory", "0:4"],
                         command=headless_emulator)
    assert state["status"] == "ok"
    assert state["cycles"] >= 1000
    assert len(state["screen"]) == 24
    assert all(len(row) == 80 for row in state["screen"])
    assert len(state["memory"][0]["bytes"].split()) == 4
    assert state["copower"]["enabled"] is False


def test_wait_timeout_preserves_diagnostics(headless_emulator):
    with pytest.raises(subprocess.CalledProcessError) as failure:
        run_scenario(["--wait-cycles", "1000", "--wait-for", "impossible screen text"],
                     command=headless_emulator)
    assert failure.value.returncode == 3
    state = json.loads(failure.value.stdout)
    assert state["status"] != "ok"
    assert "impossible screen text" in state["message"]
    assert len(state["screen"]) == 24


def test_invalid_ram_capacity_fails(headless_emulator):
    result = subprocess.run([*headless_emulator, "--copower-ram", "128"],
                            capture_output=True, text=True, timeout=10)
    assert result.returncode != 0
    assert "256 or 512" in result.stderr
