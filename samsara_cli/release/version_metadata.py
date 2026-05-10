"""Structured version loading, validation, drift detection, and sync."""

from __future__ import annotations

import json
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path

import tomli_w

_SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$")

_MARKETPLACE_PATH = Path(".claude-plugin/marketplace.json")
_PLUGIN_PATH = Path(".claude-plugin/plugin.json")
_PYPROJECT_PATH = Path("pyproject.toml")


class VersionMetadataError(Exception):
    """Raised for malformed, missing, or invalid version metadata."""


@dataclass(frozen=True)
class VersionMismatch:
    """A file whose version field does not match marketplace metadata."""

    path: Path
    field: str
    expected: str
    actual: str


class VersionDriftError(VersionMetadataError):
    """Raised when release-related version files disagree."""

    def __init__(self, mismatches: list[VersionMismatch]) -> None:
        self.mismatches = mismatches
        detail = "; ".join(
            f"{mismatch.path}: expected {mismatch.expected!r} in {mismatch.field}, "
            f"got {mismatch.actual!r}"
            for mismatch in mismatches
        )
        super().__init__(f"Version drift detected: {detail}")


class PartialSyncError(VersionMetadataError):
    """Raised when sync writes some files and then fails."""

    def __init__(self, changed_paths: list[Path], cause: Exception) -> None:
        self.changed_paths = changed_paths
        self.cause = cause
        changed_text = ", ".join(str(path) for path in changed_paths) or "none"
        super().__init__(
            f"Partial version sync detected after writing: {changed_text}. Cause: {cause}"
        )


@dataclass(frozen=True)
class SyncResult:
    """Result of syncing plugin/pyproject versions to marketplace version."""

    version: str
    tag: str
    changed_paths: list[Path]
    check_only: bool


@dataclass(frozen=True)
class VersionMetadata:
    """Structured view of release version metadata files."""

    repo_root: Path
    marketplace_version: str
    plugin_version: str
    pyproject_version: str
    mismatches: list[VersionMismatch]

    @property
    def is_synced(self) -> bool:
        return len(self.mismatches) == 0

    @property
    def tag(self) -> str:
        return f"v{self.marketplace_version}"

    @classmethod
    def inspect(cls, repo_root: Path) -> "VersionMetadata":
        repo_root = repo_root.resolve()
        marketplace_path = repo_root / _MARKETPLACE_PATH
        plugin_path = repo_root / _PLUGIN_PATH
        pyproject_path = repo_root / _PYPROJECT_PATH

        marketplace_data = _read_json(marketplace_path)
        plugin_data = _read_json(plugin_path)
        pyproject_data = _read_toml(pyproject_path)

        marketplace_version = _validate_version(
            _read_nested_required(
                marketplace_data, ["metadata", "version"], marketplace_path
            ),
            marketplace_path,
            "metadata.version",
        )
        plugin_version = _validate_version(
            _read_required(plugin_data, "version", plugin_path),
            plugin_path,
            "version",
        )
        pyproject_version = _validate_version(
            _read_nested_required(
                pyproject_data, ["project", "version"], pyproject_path
            ),
            pyproject_path,
            "project.version",
        )

        mismatches: list[VersionMismatch] = []
        if plugin_version != marketplace_version:
            mismatches.append(
                VersionMismatch(
                    path=plugin_path,
                    field="version",
                    expected=marketplace_version,
                    actual=plugin_version,
                )
            )
        if pyproject_version != marketplace_version:
            mismatches.append(
                VersionMismatch(
                    path=pyproject_path,
                    field="project.version",
                    expected=marketplace_version,
                    actual=pyproject_version,
                )
            )

        return cls(
            repo_root=repo_root,
            marketplace_version=marketplace_version,
            plugin_version=plugin_version,
            pyproject_version=pyproject_version,
            mismatches=mismatches,
        )

    @classmethod
    def load(cls, repo_root: Path) -> "VersionMetadata":
        metadata = cls.inspect(repo_root)
        if metadata.mismatches:
            raise VersionDriftError(metadata.mismatches)
        return metadata

    @classmethod
    def sync_from_marketplace(
        cls, repo_root: Path, check_only: bool = False
    ) -> SyncResult:
        metadata = cls.inspect(repo_root)
        changed_paths = [mismatch.path for mismatch in metadata.mismatches]
        if check_only or not changed_paths:
            return SyncResult(
                version=metadata.marketplace_version,
                tag=metadata.tag,
                changed_paths=changed_paths,
                check_only=check_only,
            )

        written_paths: list[Path] = []
        try:
            if any(path == metadata.repo_root / _PLUGIN_PATH for path in changed_paths):
                _write_plugin_version(
                    metadata.repo_root / _PLUGIN_PATH, metadata.marketplace_version
                )
                written_paths.append(metadata.repo_root / _PLUGIN_PATH)
            if any(
                path == metadata.repo_root / _PYPROJECT_PATH for path in changed_paths
            ):
                _write_pyproject_version(
                    metadata.repo_root / _PYPROJECT_PATH, metadata.marketplace_version
                )
                written_paths.append(metadata.repo_root / _PYPROJECT_PATH)
        except Exception as exc:
            raise PartialSyncError(written_paths, exc) from exc

        refreshed = cls.load(metadata.repo_root)
        return SyncResult(
            version=refreshed.marketplace_version,
            tag=refreshed.tag,
            changed_paths=written_paths,
            check_only=False,
        )


def _read_json(path: Path) -> dict:
    _ensure_file_exists(path)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise VersionMetadataError(
            f"Malformed JSON in {path}: {exc.msg} at line {exc.lineno} column {exc.colno}"
        ) from exc
    except OSError as exc:
        raise VersionMetadataError(f"Failed to read {path}: {exc}") from exc


def _read_toml(path: Path) -> dict:
    _ensure_file_exists(path)
    try:
        return tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        raise VersionMetadataError(f"Malformed TOML in {path}: {exc}") from exc
    except OSError as exc:
        raise VersionMetadataError(f"Failed to read {path}: {exc}") from exc


def _ensure_file_exists(path: Path) -> None:
    if not path.exists():
        raise VersionMetadataError(f"Required version file not found: {path}")


def _read_required(data: dict, key: str, path: Path) -> object:
    if key not in data:
        raise VersionMetadataError(f"Missing required field {key!r} in {path}")
    return data[key]


def _read_nested_required(data: dict, keys: list[str], path: Path) -> object:
    current: object = data
    traversed: list[str] = []
    for key in keys:
        traversed.append(key)
        if not isinstance(current, dict) or key not in current:
            raise VersionMetadataError(
                f"Missing required field {'.'.join(traversed)!r} in {path}"
            )
        current = current[key]
    return current


def _validate_version(value: object, path: Path, field: str) -> str:
    if not isinstance(value, str):
        raise VersionMetadataError(f"Missing required field {field!r} in {path}")

    version = value.strip()
    if not _SEMVER_RE.fullmatch(version):
        raise VersionMetadataError(
            f"Found invalid version {version!r} in {path} field {field!r}"
        )
    return version


def _write_plugin_version(path: Path, version: str) -> None:
    data = _read_json(path)
    data["version"] = version
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _write_pyproject_version(path: Path, version: str) -> None:
    data = _read_toml(path)
    project = data.get("project")
    if not isinstance(project, dict):
        raise VersionMetadataError(f"Missing required field 'project' in {path}")
    project["version"] = version
    path.write_text(tomli_w.dumps(data), encoding="utf-8")
