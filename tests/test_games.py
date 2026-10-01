# SPDX-FileCopyrightText: 2026 P2000C SASI Distribution contributors
# SPDX-License-Identifier: GPL-3.0-or-later

from hashlib import sha256
from pathlib import Path
import subprocess
from threading import Barrier

from p2000c_disk.assembly import ROOT
from p2000c_disk import games as games_module
from p2000c_disk.games import load_game_lock, materialize_games, materialize_local_games
from p2000c_disk import distribution


def create_repositories(root: Path, marker: str) -> None:
    for game in load_game_lock():
        repository = root / game.repository.rsplit("/", 1)[-1]
        repository.mkdir(parents=True, exist_ok=True)
        commands = ["\tmkdir -p build"]
        for artifact in game.artifacts:
            name = Path(artifact.path).name
            commands.append(f"\tprintf \"%s\" \"{game.identifier}-{marker}\" > build/{name}")
        (repository / "Makefile").write_text(
            ".PHONY: build\nbuild:\n" + "\n".join(commands) + "\n"
        )
        (repository / "working-tree.txt").write_text(marker)
        old_build = repository / "build"
        old_build.mkdir(exist_ok=True)
        for artifact in game.artifacts:
            (old_build / Path(artifact.path).name).write_text("stale")


def test_local_games_build_current_working_trees_without_locked_hashes(tmp_path):
    repositories = tmp_path / "repositories"
    create_repositories(repositories, "development")

    installed = materialize_local_games(
        tmp_path / "stage", repositories, tmp_path / "cache", jobs=2
    )

    files = {path.name: path.read_text() for path in installed["F"][0]}
    assert files == {
        "SCHAKEN.COM": "chess-development",
        "SCHAKEN.GFX": "chess-development",
        "MINES.COM": "minesweeper-development",
        "ZEESLAG.COM": "battleship-development",
        "OTHELLO.COM": "othello-development",
        "TETRIS.COM": "tetris-development",
        "KAKURO.COM": "kakuro-development",
    }
    assert all(path.read_text() == "stale" for repository in repositories.iterdir()
               for path in (repository / "build").iterdir())

    create_repositories(repositories, "newer")
    rebuilt = materialize_local_games(
        tmp_path / "new-stage", repositories, tmp_path / "cache", jobs=2
    )
    assert {path.name: path.read_text() for path in rebuilt["F"][0]} == {
        "SCHAKEN.COM": "chess-newer",
        "SCHAKEN.GFX": "chess-newer",
        "MINES.COM": "minesweeper-newer",
        "ZEESLAG.COM": "battleship-newer",
        "OTHELLO.COM": "othello-newer",
        "TETRIS.COM": "tetris-newer",
        "KAKURO.COM": "kakuro-newer",
    }


def test_make_dev_uses_sibling_repositories_and_separate_output():
    command = subprocess.check_output(["make", "-n", "dev"], cwd=ROOT, text=True)
    assert "p2000c_disk.distribution dev" in command
    assert "--dist \"dist/dev\"" in command
    assert "--games-root \"..\"" in command
    assert "--game-cache \"dist/dev/.game-cache\"" in command
    assert "--jobs \"2\"" in command


def test_development_build_normalizes_paths_and_builds_variants_in_parallel(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    seen = []
    prepared = {}
    barrier = Barrier(2)
    game_files = {"F": {0: []}}

    def materialize(destination, repositories, cache, lock_path, *, jobs):
        prepared.update(destination=destination, repositories=repositories,
                        cache=cache, lock_path=lock_path, jobs=jobs)
        return game_files

    def build(variant, dist, **options):
        barrier.wait(timeout=5)
        seen.append((variant, dist, options))
        return dist / (variant + ("-coboard" if options["coboard"] else ""))

    monkeypatch.setattr(distribution, "materialize_local_games", materialize)
    monkeypatch.setattr(distribution, "build_distribution", build)
    outputs = distribution.build_development_distributions(
        Path("output"), Path("games"), config=Path("distribution.json"),
        coboard_system=Path("coboard.trk"), jobs=2,
    )

    assert len(outputs) == 4
    assert prepared["jobs"] == 2
    assert prepared["repositories"].is_absolute()
    assert prepared["cache"].is_absolute()
    assert all(dist.is_absolute() for _, dist, _ in seen)
    assert all(options["external_games"] is game_files for _, _, options in seen)
    assert all(options["config"].is_absolute() for _, _, options in seen)
    assert all(options["coboard_system"] is None or
               options["coboard_system"].is_absolute()
               for _, _, options in seen)



def test_artifact_release_urls_are_downloaded_and_verified(monkeypatch, tmp_path):
    payload = b"official release"
    digest = sha256(payload).hexdigest()
    lock = tmp_path / "games.lock.toml"
    lock.write_text(f"""schema = 1
[[games]]
id = "release-game"
repository = "https://github.com/owner/release-game"
version = "v1.2.3"
commit = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
drive = "F"
user = 0
[[games.artifacts]]
path = "GAME.COM"
sha256 = "{digest}"
release_url = "https://github.com/owner/release-game/releases/download/v1.2.3/GAME.COM"
""")
    seen = []
    monkeypatch.setattr(games_module, "_download",
                        lambda url: seen.append(url) or payload)
    monkeypatch.setenv("P2000C_GAME_CACHE", str(tmp_path / "cache"))

    installed = materialize_games(tmp_path / "stage", lock)

    assert installed["F"][0][0].read_bytes() == payload
    assert seen == [
        "https://github.com/owner/release-game/releases/download/v1.2.3/GAME.COM"
    ]


def test_locked_make_build_date_overrides_upstream_makefile(monkeypatch, tmp_path):
    archive = b"source archive"
    payload = b"reproducible game"
    lock = tmp_path / "games.lock.toml"
    lock.write_text(f'''schema = 1
[[games]]
id = "source-game"
repository = "https://github.com/owner/source-game"
version = "v1.2.3"
commit = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
archive_sha256 = "{sha256(archive).hexdigest()}"
build_date = "2026-09-27"
build_command = ["make", "build"]
drive = "F"
user = 0
[[games.artifacts]]
path = "build/GAME.COM"
sha256 = "{sha256(payload).hexdigest()}"
''')
    seen = {}

    def extract(_archive, destination):
        seen["archive"] = _archive

    def run(command, *, cwd, env, check, capture_output, text):
        seen.update(command=command, build_date=env["BUILD_DATE"], check=check,
                    capture_output=capture_output, text=text)
        output = cwd / "build" / "GAME.COM"
        output.parent.mkdir()
        output.write_bytes(payload)

    monkeypatch.setattr(games_module, "_download", lambda _url: archive)
    monkeypatch.setattr(games_module, "_extract_source", extract)
    monkeypatch.setattr(games_module.subprocess, "run", run)
    monkeypatch.setenv("P2000C_GAME_CACHE", str(tmp_path / "cache"))

    installed = materialize_games(tmp_path / "stage", lock)

    assert installed["F"][0][0].read_bytes() == payload
    assert seen == {
        "archive": archive,
        "command": ["make", "build", "BUILD_DATE=2026-09-27"],
        "build_date": "2026-09-27",
        "check": True,
        "capture_output": True,
        "text": True,
    }
