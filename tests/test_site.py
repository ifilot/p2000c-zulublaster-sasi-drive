# SPDX-FileCopyrightText: 2026 P2000C SASI Distribution contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Validate the static browser-emulator site assembly."""
import gzip
from hashlib import sha256
from pathlib import Path

import pytest

from p2000c_disk.site import build_site


def fixture_tree(tmp_path: Path):
    root = tmp_path / "root"
    (root / "web").mkdir(parents=True)
    (root / "web/index.html").write_text(
        '<script src="p2000c-web.js"></script><script src="app.js"></script>'
    )
    (root / "web/app.js").write_text("const emulator = true;")
    (root / "web/p2000c-font.png").write_bytes(bytes(2265))
    (root / "web/gallery").mkdir()
    (root / "web/gallery/navigator.webp").write_bytes(b"gallery image")
    (root / "tools/emulator/firmware").mkdir(parents=True)
    (root / "tools/emulator/firmware/IPLDUMP.BIN").write_bytes(bytes(4096))
    media = tmp_path / "media"
    media.mkdir()
    for name in ("HD0_256.hda", "HD1_256.hda"):
        with (media / name).open("wb") as output:
            output.truncate(10 * 1024 * 1024)
    emulator = tmp_path / "p2000c-web"
    emulator.with_suffix(".js").write_text("createP2000C = () => {};")
    emulator.with_suffix(".wasm").write_bytes(b"wasm")
    return root, media, emulator


def test_site_contains_real_emulator_and_distribution(tmp_path):
    root, media, emulator = fixture_tree(tmp_path)
    output = build_site(tmp_path / "site", media, emulator, root)
    assert (output / ".nojekyll").is_file()
    assert (output / "IPLDUMP.BIN").stat().st_size == 4096
    for name in ("HD0_256.hda", "HD1_256.hda"):
        compressed = output / f"{name}.gz"
        assert compressed.stat().st_size < (media / name).stat().st_size
        assert gzip.decompress(compressed.read_bytes()) == (media / name).read_bytes()
        assert not (output / name).exists()
    assert (output / "p2000c-web.js").is_file()
    assert (output / "p2000c-web.wasm").read_bytes() == b"wasm"
    assert (output / "p2000c-font.png").stat().st_size == 2265
    assert (output / "gallery/navigator.webp").read_bytes() == b"gallery image"


def test_site_rejects_incomplete_media_without_replacing_output(tmp_path):
    root, media, emulator = fixture_tree(tmp_path)
    output = tmp_path / "site"
    output.mkdir()
    (output / "keep").write_text("old")
    (media / "HD1_256.hda").write_bytes(b"short")
    with pytest.raises(ValueError, match="exactly"):
        build_site(output, media, emulator, root)
    assert (output / "keep").read_text() == "old"


def test_repository_site_describes_full_webassembly_emulator():
    root = Path(__file__).parents[1]
    html = (root / "web/index.html").read_text()
    javascript = (root / "web/app.js").read_text()
    stylesheet = (root / "web/style.css").read_text()
    font = root / "web/p2000c-font.png"
    assert '<html lang="nl">' in html
    assert "Dit is een webemulator van de Philips P2000C" in html
    assert "Met Reset start u de geëmuleerde computer opnieuw" in html
    assert 'id="language-toggle"' in html
    assert 'role="switch"' in html and 'aria-checked="false"' in html
    assert '<span class="prompt">&gt;</span> PHILIPS P2000C' in html
    assert 'class="model"' not in html
    assert 'id="emulator-title"' not in html
    assert 'data-i18n="speedOriginal" value="1" selected' in html
    assert "This is a web-based emulator of the Philips P2000C" in javascript
    assert "Reset restarts the emulated computer" in javascript
    assert 'const LANGUAGE_STORAGE_KEY = "p2000c-language"' in javascript
    assert "applyLanguage(savedLanguage())" in javascript
    assert 'document.documentElement.lang = language' in javascript
    assert "createP2000C" in javascript
    assert "HD0_256.hda" in javascript and "HD1_256.hda" in javascript
    assert "HD0_256.hda.gz" in javascript and "HD1_256.hda.gz" in javascript
    assert 'new DecompressionStream(asset.compression)' in javascript
    assert "CHARACTER_SHEET_PITCH = 12" in javascript
    assert "DISPLAY_SCALE = 2" in javascript
    assert 'width="1280" height="576"' in html
    assert '<section class="intro">' not in html
    assert "display-screen" in html
    assert "repeating-linear-gradient" not in stylesheet
    assert sha256(font.read_bytes()).hexdigest() == (
        "daac2776c03a24beac228f0ed0f7ff04ee0fe44dce06d4fafc4e52bb6a9cb87d"
    )
