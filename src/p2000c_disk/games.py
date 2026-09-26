"""Fetch and verify the immutable external games used by a distribution."""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import os
from pathlib import Path
import re
import shutil
import subprocess
import tarfile
import tempfile
import tomllib
from typing import Any
from urllib.request import Request, urlopen

from .assembly import ROOT

LOCK_SCHEMA = 1
SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")
COMMIT_RE = re.compile(r"[0-9a-f]{40}\Z")
DATE_RE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}\Z")


@dataclass(frozen=True)
class GameArtifact:
    """One verified CP/M file produced by a locked game."""

    path: str
    sha256: str


@dataclass(frozen=True)
class LockedGame:
    """A source-build or release-asset game selected for this distro version."""

    identifier: str
    repository: str
    tag: str
    commit: str
    drive: str
    user: int
    artifacts: tuple[GameArtifact, ...]
    archive_sha256: str | None = None
    build_date: str | None = None
    build_command: tuple[str, ...] = ()
    release_url: str | None = None


def _require_string(table: dict[str, Any], key: str, context: str) -> str:
    """Read a non-empty string from a lock-file table."""
    value = table.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{context}.{key} must be a non-empty string")
    return value


def _require_hash(value: str, context: str) -> str:
    """Validate and normalize a SHA-256 digest."""
    value = value.lower()
    if not SHA256_RE.fullmatch(value):
        raise ValueError(f"{context} must be a lowercase SHA-256 digest")
    return value


def _safe_relative(path: str, context: str) -> Path:
    """Validate a relative source or artifact path."""
    relative = Path(path)
    if relative.is_absolute() or ".." in relative.parts or not relative.parts:
        raise ValueError(f"{context} must be a safe relative path")
    return relative


def load_game_lock(path: Path = ROOT / "games.lock.toml") -> tuple[LockedGame, ...]:
    """Load and validate the immutable external-game selection."""
    try:
        document = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        raise ValueError(f"invalid game lock TOML: {exc}") from exc
    if document.get("schema") != LOCK_SCHEMA or set(document) - {"schema", "games"}:
        raise ValueError("unsupported game lock schema")
    raw_games = document.get("games")
    if not isinstance(raw_games, list) or not raw_games:
        raise ValueError("games lock must contain at least one game")
    games: list[LockedGame] = []
    identifiers: set[str] = set()
    targets: set[tuple[str, int, str]] = set()
    for index, raw in enumerate(raw_games, 1):
        context = f"games[{index}]"
        if not isinstance(raw, dict):
            raise ValueError(f"{context} must be a table")
        allowed = {"id", "repository", "tag", "commit", "drive", "user", "artifacts",
                   "archive_sha256", "build_date", "build_command", "release_url"}
        unknown = set(raw) - allowed
        if unknown:
            raise ValueError(f"unknown key in {context}: {sorted(unknown)[0]}")
        identifier = _require_string(raw, "id", context)
        if not re.fullmatch(r"[a-z0-9-]+", identifier) or identifier in identifiers:
            raise ValueError(f"{context}.id must be unique lowercase text")
        identifiers.add(identifier)
        repository = _require_string(raw, "repository", context)
        if not re.fullmatch(r"https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
            raise ValueError(f"{context}.repository must be a GitHub repository URL")
        tag = _require_string(raw, "tag", context)
        commit = _require_string(raw, "commit", context).lower()
        if not COMMIT_RE.fullmatch(commit):
            raise ValueError(f"{context}.commit must be a 40-character commit ID")
        drive = _require_string(raw, "drive", context).upper()
        user = raw.get("user")
        if drive < "A" or drive > "G" or type(user) is not int or not 0 <= user <= 15:
            raise ValueError(f"{context} has an invalid CP/M drive or user")
        raw_artifacts = raw.get("artifacts")
        if not isinstance(raw_artifacts, list) or not raw_artifacts:
            raise ValueError(f"{context}.artifacts must be a non-empty list")
        artifacts: list[GameArtifact] = []
        for artifact_index, raw_artifact in enumerate(raw_artifacts, 1):
            artifact_context = f"{context}.artifacts[{artifact_index}]"
            if not isinstance(raw_artifact, dict) or set(raw_artifact) != {"path", "sha256"}:
                raise ValueError(f"{artifact_context} must contain path and sha256")
            artifact_path = _safe_relative(_require_string(raw_artifact, "path", artifact_context), artifact_context)
            target = (drive, user, artifact_path.name.upper())
            if target in targets:
                raise ValueError(f"duplicate installed game artifact: {artifact_path.name}")
            targets.add(target)
            artifacts.append(GameArtifact(artifact_path.as_posix(), _require_hash(
                _require_string(raw_artifact, "sha256", artifact_context), f"{artifact_context}.sha256")))
        release_url = raw.get("release_url")
        archive_sha256 = raw.get("archive_sha256")
        build_date = raw.get("build_date")
        build_command = raw.get("build_command")
        source_build = archive_sha256 is not None or build_date is not None or build_command is not None
        if release_url is not None:
            if source_build or not isinstance(release_url, str) or not release_url.startswith(repository + "/releases/download/"):
                raise ValueError(f"{context}.release_url must be the only artifact source")
        else:
            if not (isinstance(archive_sha256, str) and isinstance(build_date, str) and isinstance(build_command, list)):
                raise ValueError(f"{context} needs source archive, build date, and build command")
            archive_sha256 = _require_hash(archive_sha256, f"{context}.archive_sha256")
            if not DATE_RE.fullmatch(build_date):
                raise ValueError(f"{context}.build_date must use YYYY-MM-DD")
            if not build_command or not all(isinstance(part, str) and part for part in build_command):
                raise ValueError(f"{context}.build_command must be a non-empty string list")
        games.append(LockedGame(identifier, repository, tag, commit, drive, user,
                                tuple(artifacts), archive_sha256, build_date,
                                tuple(build_command or ()), release_url))
    return tuple(games)


def _digest(data: bytes) -> str:
    """Return the lowercase SHA-256 digest of bytes."""
    return sha256(data).hexdigest()


def _download(url: str) -> bytes:
    """Download one immutable GitHub source or release asset."""
    request = Request(url, headers={"User-Agent": "p2000c-sasi-distribution"})
    try:
        with urlopen(request, timeout=60) as response:
            return response.read()
    except OSError as exc:
        raise ValueError(f"could not download {url}: {exc}") from exc


def _extract_source(archive: bytes, destination: Path) -> None:
    """Extract a GitHub tarball without permitting path traversal or links."""
    with tempfile.NamedTemporaryFile(suffix=".tar.gz") as temporary:
        temporary.write(archive)
        temporary.flush()
        with tarfile.open(temporary.name, "r:gz") as source:
            members = source.getmembers()
            if not members:
                raise ValueError("empty game source archive")
            root = members[0].name.split("/", 1)[0]
            for member in members:
                relative = Path(member.name)
                inside_root = member.name in {root, root + "/"} or member.name.startswith(root + "/")
                if (member.issym() or member.islnk() or relative.is_absolute() or
                        ".." in relative.parts or not inside_root):
                    raise ValueError("unsafe game source archive")
            source.extractall(destination, members=members, filter="data")
    extracted = destination / root
    if not extracted.is_dir():
        raise ValueError("game source archive has no root directory")
    for child in extracted.iterdir():
        shutil.move(str(child), destination / child.name)
    extracted.rmdir()


def _verify_artifact(path: Path, expected: str) -> None:
    """Check that one produced CP/M artifact exists and matches its lock hash."""
    if not path.is_file():
        raise ValueError(f"locked game artifact was not produced: {path.name}")
    actual = _digest(path.read_bytes())
    if actual != expected:
        raise ValueError(f"locked game artifact hash mismatch for {path.name}: {actual}")


def _cache_root(lock_path: Path) -> Path:
    """Return the cache namespace for the exact contents of the game lock."""
    configured = os.environ.get("P2000C_GAME_CACHE")
    root = Path(configured) if configured else Path.home() / ".cache/p2000c-disk-tool/games"
    return root / _digest(lock_path.read_bytes())


def materialize_games(destination: Path, lock_path: Path = ROOT / "games.lock.toml") -> dict[str, dict[int, list[Path]]]:
    """Download, build, verify, and stage every game selected by the lock file."""
    games = load_game_lock(lock_path)
    cache = _cache_root(lock_path)
    destination.mkdir(parents=True, exist_ok=True)
    installed: dict[str, dict[int, list[Path]]] = {}
    for game in games:
        game_cache = cache / game.identifier
        valid = all((game_cache / Path(artifact.path).name).is_file() and
                    _digest((game_cache / Path(artifact.path).name).read_bytes()) == artifact.sha256
                    for artifact in game.artifacts)
        if not valid:
            game_cache.mkdir(parents=True, exist_ok=True)
            with tempfile.TemporaryDirectory(prefix=f".game-{game.identifier}-", dir=destination) as temporary:
                work = Path(temporary)
                if game.release_url:
                    sources = {artifact.path: _download(game.release_url) for artifact in game.artifacts}
                else:
                    repository_path = game.repository.removeprefix("https://github.com/")
                    archive_url = f"https://codeload.github.com/{repository_path}/tar.gz/{game.commit}"
                    archive = _download(archive_url)
                    if _digest(archive) != game.archive_sha256:
                        raise ValueError(f"locked source archive hash mismatch for {game.identifier}")
                    source = work / "source"
                    source.mkdir()
                    _extract_source(archive, source)
                    environment = dict(os.environ)
                    environment["BUILD_DATE"] = game.build_date or ""
                    try:
                        subprocess.run(game.build_command, cwd=source, env=environment,
                                       check=True, capture_output=True, text=True)
                    except subprocess.CalledProcessError as exc:
                        raise ValueError(exc.stderr or f"locked game build failed: {game.identifier}") from exc
                    sources = {artifact.path: (source / artifact.path).read_bytes()
                               for artifact in game.artifacts}
                for artifact in game.artifacts:
                    cached = game_cache / Path(artifact.path).name
                    data = sources[artifact.path]
                    if _digest(data) != artifact.sha256:
                        raise ValueError(f"locked game artifact hash mismatch for {cached.name}: {_digest(data)}")
                    cached.write_bytes(data)
        for artifact in game.artifacts:
            cached = game_cache / Path(artifact.path).name
            _verify_artifact(cached, artifact.sha256)
            staged = destination / game.identifier / cached.name
            staged.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(cached, staged)
            installed.setdefault(game.drive, {}).setdefault(game.user, []).append(staged)
    return installed
