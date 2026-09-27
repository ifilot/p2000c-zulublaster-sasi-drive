"""Assemble the static WebAssembly P2000C site for GitHub Pages."""
from __future__ import annotations

import argparse
import gzip
import os
from pathlib import Path
import shutil
import tempfile

from .assembly import ROOT

MEDIA_FILES = {
    "HD0_256.hda": 10 * 1024 * 1024,
    "HD1_256.hda": 10 * 1024 * 1024,
}
EMULATOR_SUFFIXES = (".js", ".wasm")


def _require_file(path: Path, description: str, size: int | None = None) -> Path:
    if not path.is_file():
        raise ValueError(f"Missing {description}: {path}")
    if size is not None and path.stat().st_size != size:
        raise ValueError(
            f"{description} must be exactly {size} bytes: {path}"
        )
    return path


def _gzip_file(source: Path, destination: Path) -> None:
    """Write a deterministic, maximally compressed copy of source."""
    with source.open("rb") as input_file, destination.open("wb") as output_file:
        with gzip.GzipFile(
            filename="", mode="wb", fileobj=output_file, compresslevel=9, mtime=0
        ) as compressed:
            shutil.copyfileobj(input_file, compressed)


def build_site(destination: Path, media: Path, emulator: Path,
               root: Path = ROOT) -> Path:
    """Atomically assemble web files, firmware, media, and WebAssembly."""
    destination = destination.resolve()
    media = media.resolve()
    emulator = emulator.resolve()
    source = root / "web"
    _require_file(source / "index.html", "web index")
    _require_file(source / "p2000c-font.png",
                  "P2000C character generator", 2265)
    assets = [
        (_require_file(root / "tools/emulator/firmware/IPLDUMP.BIN",
                       "P2000C IPL", 4096), "IPLDUMP.BIN"),
    ]
    media_assets = [
        (_require_file(media / name, name, size), name)
        for name, size in MEDIA_FILES.items()
    ]
    assets.extend(
        (_require_file(emulator.with_suffix(suffix),
                       f"WebAssembly emulator {suffix}"),
         f"p2000c-web{suffix}")
        for suffix in EMULATOR_SUFFIXES
    )

    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=f".{destination.name}-", dir=destination.parent
    ) as temporary:
        work = Path(temporary)
        stage = work / destination.name
        shutil.copytree(source, stage)
        for source_path, name in assets:
            shutil.copyfile(source_path, stage / name)
        for source_path, name in media_assets:
            _gzip_file(source_path, stage / f"{name}.gz")
        (stage / ".nojekyll").write_text("", encoding="ascii")

        backup = work / "previous"
        if destination.exists():
            if not destination.is_dir() or destination.is_symlink():
                raise ValueError(f"Site output is not a normal directory: {destination}")
            destination.rename(backup)
        try:
            stage.rename(destination)
        except OSError:
            if backup.exists():
                backup.rename(destination)
            raise
    return destination


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "_site")
    parser.add_argument("--media", type=Path, default=ROOT / "dist/menu")
    parser.add_argument(
        "--emulator", type=Path,
        default=ROOT / "build/emulator-web/p2000c-web",
        help="Web emulator path without the .js/.wasm suffix",
    )
    args = parser.parse_args()
    try:
        print(f"Built {build_site(args.output, args.media, args.emulator)}")
    except (OSError, ValueError) as exc:
        parser.exit(1, f"{exc}\n")


if __name__ == "__main__":
    main()
