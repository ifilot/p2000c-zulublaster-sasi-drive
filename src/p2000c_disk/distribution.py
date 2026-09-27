"""Build the CP/M SD-card package for P2000C/ZuluBlaster."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time

from .assembly import ROOT, assemble_program, build_trkdump
from .builder import build_image
from .config import ConfigUpdates, apply_config_updates, inspect_config
from .filesystem import put_files, set_system_attribute
from .games import materialize_games, materialize_local_games
from .layout import detect_image_layout
from .menu import build_menu
from .menu_boot import cold_menu_boot, is_menu_boot
from .payload import load_payload
from .verify import require_valid_image
from .version import DISTRIBUTION_NAME, VERSION

VARIANTS = ("pro", "menu")
SD_FILES = ("HD0_256.hda", "HD1_256.hda", "zuluscsi.ini")
# Confirmed by booting the reference tracks with distinct partition markers.
SASI_DRIVES = {
    "A": {"image": "HD0_256.hda", "partition": "low", "role": "system"},
    "D": {"image": "HD0_256.hda", "partition": "high", "role": "applications"},
    "E": {"image": "HD1_256.hda", "partition": "low", "role": "development"},
    "F": {"image": "HD1_256.hda", "partition": "high", "role": "games"},
}


def package_name(variant: str, coboard: bool = False) -> str:
    if variant not in VARIANTS:
        raise ValueError(f"Unknown edition: {variant}; choose pro or menu")
    return variant + ("-coboard" if coboard else "")


def system_tracks(coboard: bool, supplied: Path | None, root: Path = ROOT) -> Path:
    if not coboard:
        if supplied is not None:
            raise ValueError("--coboard-system requires --coboard (make: COBOARD=1)")
        return root / "assets/boot/hdboot-split.trk"
    path = supplied or root / "assets/boot/hdboot-coboard.trk"
    if not path.is_file():
        raise ValueError(
            "CoPower needs verified CONFIG-generated SASI boot tracks with A-F preserved "
            "and the original RAM driver at G:. Supply COBOARD_SYSTEM=/path/to/tracks "
            "(CLI: --coboard-system). The captured floppy tracks cannot be used directly. "
            "See docs/building.md. No package was built."
        )
    data = path.read_bytes()
    if len(data) != 8192 or detect_image_layout(data).mode != "split":
        raise ValueError("CoPower boot tracks must be an 8192-byte split SASI system")
    required = (b"A:5MB-HRD1", b"B:640K-FL1", b"C:640K-FL2",
                b"D:5MB-HRD1", b"E:5MB-HRD2", b"F:5MB-HRD2")
    if not all(label in data for label in required) or not re.search(rb"G:(127|128|256|508|512)K-MEM", data):
        raise ValueError("CoPower boot display must preserve A-F and include G: RAM")
    return path


def digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def verify_distribution(directory: Path) -> None:
    manifest = json.loads((directory / "manifest.json").read_text())
    if (manifest.get("schema") != 4 or manifest.get("version") != VERSION or
            manifest.get("name") != DISTRIBUTION_NAME or manifest.get("variant") not in VARIANTS
            or type(manifest.get("coboard")) is not bool):
        raise ValueError("Unsupported distribution manifest")
    records = manifest["files"]
    if not set(SD_FILES).issubset(records):
        raise ValueError("Manifest is missing SD card files")
    for name, expected in records.items():
        relative = Path(name)
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError(f"Invalid manifest path: {name}")
        path = directory / relative
        if not path.resolve().is_relative_to(directory.resolve()) or path.is_symlink() or not path.is_file() or digest(path) != expected:
            raise ValueError(f"Missing or changed package file: {name}")
    for name in SD_FILES[:2]:
        require_valid_image(directory / name)
    if manifest["variant"] == "menu" and not is_menu_boot((directory / SD_FILES[0]).read_bytes()[:8192]):
        raise ValueError("Missing cold-only menu startup")
    actual = inspect_config(directory / SD_FILES[0]).fields["autostart"].value
    if actual != ("A:MENU" if manifest["variant"] == "menu" else ""):
        raise ValueError(f"Unexpected boot command: {actual!r}")


def _process_exists(pid: int) -> bool:
    """Return whether a process still owns a recorded build lock."""
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


@contextmanager
def _build_lock(path: Path):
    """Own a build lock and recover locks abandoned by dead processes."""
    owner = path / "owner.pid"
    for _ in range(3):
        try:
            path.mkdir()
        except FileExistsError:
            try:
                pid = int(owner.read_text(encoding="ascii").strip())
            except (OSError, ValueError):
                try:
                    recent = time.time() - path.stat().st_mtime < 2
                except FileNotFoundError:
                    continue
                if recent:
                    raise ValueError(
                        f"Build lock exists: {path}; another build may be starting"
                    )
                pid = 0
            if pid > 0 and _process_exists(pid):
                raise ValueError(
                    f"Build lock exists: {path}; owned by live process {pid}"
                )
            stale = path.with_name(f"{path.name}.stale-{os.getpid()}")
            try:
                path.rename(stale)
            except FileNotFoundError:
                continue
            except FileExistsError:
                raise ValueError(f"Could not recover stale build lock: {path}")
            shutil.rmtree(stale)
            continue
        try:
            owner.write_text(f"{os.getpid()}\n", encoding="ascii")
            yield
        finally:
            try:
                recorded = owner.read_text(encoding="ascii").strip()
            except OSError:
                recorded = ""
            if recorded == str(os.getpid()):
                shutil.rmtree(path, ignore_errors=True)
        return
    raise ValueError(f"Could not acquire build lock: {path}")


def build_distribution(variant: str, dist: Path, *, coboard: bool = False,
                       coboard_system: Path | None = None, config: Path | None = None,
                       assembler: str = "z80asm", root: Path = ROOT, zcc: str = "zcc",
                       external_games: dict[str, dict[int, list[Path]]] | None = None) -> Path:
    dist = dist.resolve()
    name = package_name(variant, coboard)
    tracks = system_tracks(coboard, coboard_system, root)
    settings, payload = load_payload(config or root / "distribution.json", root)
    dist.mkdir(parents=True, exist_ok=True)
    destination = dist / name
    if destination.is_symlink():
        raise ValueError(f"Refusing symlink output: {destination}")
    lock = dist / f".{name}.lock"
    with _build_lock(lock):
        with tempfile.TemporaryDirectory(prefix=f".{name}-", dir=dist) as temporary:
            work = Path(temporary)
            stage = work / name
            stage.mkdir()
            game_files = external_games
            if game_files is None:
                game_files = materialize_games(work / "locked-games",
                                               root / "games.lock.toml")
            for drive, areas in game_files.items():
                for user, paths in areas.items():
                    payload[drive].setdefault(user, []).extend(paths)
            trkdump, readme = (work / f"{p}.COM" for p in ("TRKDUMP", "README"))
            assemble_program(root / "src/asm/trkdump.asm", trkdump, assembler, maximum_size=0x3F00)
            assemble_program(root / "src/asm/readme.asm", readme, assembler, maximum_size=0x1000)
            payload["A"].setdefault(0, []).append(trkdump)
            payload["D"].setdefault(0, []).append(readme)
            if variant == "menu":
                build_menu(work, zcc, root, payload, assembler)
                names = {p.name.upper() for p in payload["A"].get(0, [])}
                menu_names = {"MENU.COM", "MENU.BIN", "MENU.DAT"}
                if names & menu_names:
                    raise ValueError("MENU.COM, MENU.BIN and MENU.DAT are reserved in the menu edition")
                payload["A"].setdefault(0, []).extend(work / name for name in sorted(menu_names))
            for image in SD_FILES[:2]:
                build_image(stage / image, tracks, layout="split")
            for drive, mapping in SASI_DRIVES.items():
                for user, paths in payload[drive].items():
                    if paths:
                        put_files(stage / mapping["image"], paths,
                                  partition=mapping["partition"], user_number=user)
            if variant == "menu":
                for name in ("MENU.BIN", "MENU.DAT"):
                    set_system_attribute(
                        stage / SD_FILES[0], name, partition="low",
                        user_number=0,
                    )
            apply_config_updates(stage / SD_FILES[0], ConfigUpdates(autostart="A:MENU") if variant == "menu"
                                 else ConfigUpdates(clear_autostart=True))
            if variant == "menu":
                with (stage / SD_FILES[0]).open("r+b") as image:
                    system = cold_menu_boot(image.read(8192))
                    image.seek(0)
                    image.write(system)
            shutil.copyfile(root / "assets/zuluscsi.ini", stage / SD_FILES[2])
            shutil.copytree(root / "assets/hardware", stage / "assets/hardware")
            shutil.copytree(root / "docs", stage / "docs")
            shutil.copyfile(root / "README.md", stage / "README.md")
            (stage / "distribution.json").write_text(json.dumps(settings, indent=2) + "\n")
            (stage / "VERSION.txt").write_text(
                f"{DISTRIBUTION_NAME} v{VERSION}\n", encoding="ascii"
            )
            manifest = {
                "schema": 4, "name": DISTRIBUTION_NAME, "version": VERSION,
                "variant": variant, "coboard": coboard,
                "system_sha256": digest(tracks), "sasi_drives": SASI_DRIVES,
                "programs": {
                    drive: {str(user): [p.name.upper() for p in paths]
                            for user, paths in areas.items()}
                    for drive, areas in payload.items()
                },
                "files": {p.relative_to(stage).as_posix(): digest(p)
                          for p in sorted(stage.rglob("*")) if p.is_file()},
            }
            (stage / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
            verify_distribution(stage)
            backup = work / "previous"
            if destination.exists():
                if not destination.is_dir():
                    raise ValueError(f"Output is not a directory: {destination}")
                destination.rename(backup)
            try:
                stage.rename(destination)
            except OSError:
                if backup.exists():
                    backup.rename(destination)
                raise
        return destination


def build_development_distributions(dist: Path, repositories: Path, *,
                                    config: Path | None = None,
                                    assembler: str = "z80asm", root: Path = ROOT,
                                    zcc: str = "zcc",
                                    coboard_system: Path | None = None,
                                    game_cache: Path | None = None,
                                    jobs: int = 2) -> tuple[Path, ...]:
    """Build local games, then generate independent editions in parallel."""
    if jobs < 1:
        raise ValueError("development build jobs must be at least one")
    dist = dist.resolve()
    repositories = repositories.resolve()
    config = config.resolve() if config is not None else None
    coboard_system = coboard_system.resolve() if coboard_system is not None else None
    cache = (game_cache or dist / ".game-cache").resolve()
    variants = (("pro", False), ("pro", True),
                ("menu", False), ("menu", True))

    with tempfile.TemporaryDirectory(prefix="p2000c-dev-games-") as temporary:
        game_files = materialize_local_games(
            Path(temporary), repositories, cache, root / "games.lock.toml",
            jobs=jobs,
        )

        def build(specification: tuple[str, bool]) -> Path:
            variant, coboard = specification
            return build_distribution(
                variant, dist, coboard=coboard,
                coboard_system=coboard_system if coboard else None,
                config=config, assembler=assembler, root=root, zcc=zcc,
                external_games=game_files,
            )

        if jobs == 1:
            return tuple(build(specification) for specification in variants)
        with ThreadPoolExecutor(max_workers=min(jobs, len(variants))) as executor:
            return tuple(executor.map(build, variants))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("dist", "verify"):
        command = commands.add_parser(name)
        command.add_argument("--variant", choices=VARIANTS, default="pro")
        command.add_argument("--dist", type=Path, default=ROOT / "dist")
        command.add_argument("--coboard", action="store_true", help="enable the original CoPower RAM driver at G:")
        if name == "dist":
            command.add_argument("--coboard-system", type=Path)
            command.add_argument("--config", type=Path, default=ROOT / "distribution.json")
            command.add_argument("--assembler", default="z80asm")
            command.add_argument("--zcc", default=os.environ.get("ZCC", "zcc"))
    development = commands.add_parser(
        "dev", help="build all editions from sibling game working trees"
    )
    development.add_argument("--dist", type=Path, default=ROOT / "dist/dev")
    development.add_argument("--games-root", type=Path, default=ROOT.parent)
    development.add_argument("--game-cache", type=Path)
    development.add_argument("--jobs", type=int, default=2)
    development.add_argument("--coboard-system", type=Path,
                             default=ROOT / "assets/boot/hdboot-coboard.trk")
    development.add_argument("--config", type=Path, default=ROOT / "distribution.json")
    development.add_argument("--assembler", default="z80asm")
    development.add_argument("--zcc", default=os.environ.get("ZCC", "zcc"))
    for name in ("trkdump",):
        utility = commands.add_parser(name, help=f"build standalone {name.upper()}.COM")
        utility.add_argument("--dist", type=Path, default=ROOT / "dist")
        utility.add_argument("--assembler", default="z80asm")
    args = parser.parse_args(argv)
    try:
        if args.command == "dist":
            output = build_distribution(args.variant, args.dist, coboard=args.coboard,
                                        coboard_system=args.coboard_system, config=args.config,
                                        assembler=args.assembler, zcc=args.zcc)
            print(f"Built and verified {output}")
        elif args.command == "dev":
            outputs = build_development_distributions(
                args.dist, args.games_root, config=args.config,
                assembler=args.assembler, zcc=args.zcc,
                coboard_system=args.coboard_system, game_cache=args.game_cache, jobs=args.jobs,
            )
            for output in outputs:
                print(f"Built and verified {output}")
        elif args.command == "verify":
            output = args.dist / package_name(args.variant, args.coboard)
            verify_distribution(output)
            print(f"Verified {output}")
        else:
            print(f"Built {build_trkdump(args.dist, args.assembler)}")
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        detail = exc.stderr if isinstance(exc, subprocess.CalledProcessError) else str(exc)
        print(f"error: {detail}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
