"""Create clearly named, SD-ready release archives from built distributions."""
from __future__ import annotations

import argparse
from hashlib import sha256
from pathlib import Path
import shutil
import tempfile

from .assembly import ROOT
from .changelog import release_notes
from .distribution import verify_distribution
from .version import DISPLAY_VERSION

PACKAGES = (
    "pro",
    "pro-coboard",
    "menu",
    "menu-coboard",
)
PREFIX = f"p2000c-zulublaster-{DISPLAY_VERSION}-"


def create_release_archives(dist: Path, output: Path) -> list[Path]:
    """Verify all packages and publish ZIPs whose roots copy directly to SD."""
    for package in PACKAGES:
        verify_distribution(dist / package)
    if not (dist / "tools/TRKDUMP.COM").is_file():
        raise ValueError("Build dist/tools/TRKDUMP.COM before creating archives")

    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".release-", dir=output) as temporary:
        stage = Path(temporary)
        archives: list[Path] = []
        for package in PACKAGES:
            base = stage / f"{PREFIX}{package}"
            archive = Path(shutil.make_archive(str(base), "zip", dist / package))
            archives.append(archive)
        tools = Path(shutil.make_archive(
            str(stage / f"{PREFIX}tools"), "zip", dist / "tools"
        ))
        archives.append(tools)

        checksums = "".join(
            f"{sha256(path.read_bytes()).hexdigest()}  {path.name}\n"
            for path in archives
        )
        (stage / "SHA256SUMS.txt").write_text(checksums)
        (stage / "RELEASE_NOTES.md").write_text(release_notes(), encoding="utf-8")

        published: list[Path] = []
        for path in [*archives, stage / "SHA256SUMS.txt", stage / "RELEASE_NOTES.md"]:
            destination = output / path.name
            path.replace(destination)
            published.append(destination)
    return published


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist", type=Path, default=ROOT / "dist")
    parser.add_argument("--output", type=Path, default=ROOT / "release")
    args = parser.parse_args(argv)
    try:
        for path in create_release_archives(args.dist, args.output):
            print(path)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
