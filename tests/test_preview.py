"""Preview lifecycle: disposable media, isolated preferences and CLI failures."""
from pathlib import Path
import subprocess

import pytest

from p2000c_disk import preview as runner


@pytest.mark.parametrize('coboard', [False, True])
def test_preview_isolates_disks_settings_and_cleans_up(monkeypatch, tmp_path, coboard):
    monkeypatch.setenv('DISPLAY', ':99')
    monkeypatch.setattr(runner.sys, 'platform', 'linux')
    executable = tmp_path / 'emulator with spaces'
    monkeypatch.setattr(runner, 'find_emulator', lambda value, root: executable)
    seen = {}

    def build(variant, dist, **kwargs):
        seen['variant'], seen['options'] = variant, kwargs
        dist.mkdir()
        for name in ('HD0_256.hda', 'HD1_256.hda'):
            (dist / name).write_bytes(b'fresh image')
        return dist

    class Emulator:
        def __init__(self, command, env):
            assert command[0] == str(executable)
            settings = Path(env['XDG_CONFIG_HOME']) / 'P2000C Emulator Project/P2000C Emulator.conf'
            assert f'copowerEnabled={str(coboard).lower()}' in settings.read_text()
            assert env['DISPLAY'] == ':99'
            seen['temporary'] = settings.parents[2]
            assert Path(command[command.index('--floppy-a') + 1]).read_bytes() == b'\xe5' * (640 * 1024)
            assert Path(command[command.index('--floppy-b') + 1]).read_bytes() == b'\xe5' * (640 * 1024)
            for flag in ('--hard-disk-0', '--hard-disk-1'):
                path = Path(command[command.index(flag) + 1])
                assert path.read_bytes() == b'fresh image'
                path.write_bytes(b'guest changes')

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def wait(self):
            return 7

    monkeypatch.setattr(runner, 'build_distribution', build)
    monkeypatch.setattr(runner.subprocess, 'Popen', Emulator)
    assert runner.preview(coboard=coboard) == 7
    assert seen['variant'] == 'menu' and seen['options']['coboard'] == coboard
    assert not seen['temporary'].exists()


def test_missing_emulator_is_actionable_and_does_not_build(monkeypatch, capsys):
    monkeypatch.setattr(runner.shutil, 'which', lambda _: None)
    monkeypatch.setattr(runner, 'build_distribution', lambda *a, **kw: pytest.fail('must not build'))
    assert runner.main(['--emulator', '/missing/p2000c']) == 1
    assert 'EMULATOR=/path/to/p2000c' in capsys.readouterr().err


def test_no_display_fails_before_build(monkeypatch):
    monkeypatch.setattr(runner.sys, 'platform', 'linux')
    monkeypatch.setattr(runner, 'find_emulator', lambda *a: Path('/emulator'))
    monkeypatch.delenv('DISPLAY', raising=False)
    monkeypatch.delenv('WAYLAND_DISPLAY', raising=False)
    monkeypatch.setattr(runner, 'build_distribution', lambda *a, **kw: pytest.fail('must not build'))
    with pytest.raises(ValueError, match='No graphical display'):
        runner.preview()


@pytest.mark.parametrize('arguments,variant,ram', [([], 'menu', False),
                                                   (['COBOARD=1'], 'menu', True),
                                                   (['VARIANT=pro'], 'pro', False),
                                                   (['VARIANT=pro', 'COBOARD=1'], 'pro', True)])
def test_make_run_defaults_and_overrides(arguments, variant, ram):
    command = subprocess.check_output(['make', '-n', 'run', *arguments], cwd=runner.ROOT, text=True)
    assert f'--variant "{variant}"' in command
    assert ('--coboard ' in command) == ram
