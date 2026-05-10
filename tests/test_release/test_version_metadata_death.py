"""
Death tests for release version metadata.

These tests guard against silent release corruption:
- version drift across marketplace/plugin/pyproject
- invalid or missing version fields
- malformed JSON/TOML inputs
- partial writes during sync
"""

import json
from pathlib import Path

import pytest


def make_repo(
    tmp_path: Path,
    *,
    marketplace_version: str = "0.9.0",
    plugin_version: str | None = None,
    pyproject_version: str | None = None,
) -> Path:
    repo = tmp_path / "repo"
    plugin_version = marketplace_version if plugin_version is None else plugin_version
    pyproject_version = (
        marketplace_version if pyproject_version is None else pyproject_version
    )
    plugin_dir = repo / ".claude-plugin"
    plugin_dir.mkdir(parents=True)
    (plugin_dir / "marketplace.json").write_text(
        json.dumps(
            {
                "$schema": "https://anthropic.com/claude-code/marketplace.schema.json",
                "name": "samsara-marketplace",
                "metadata": {"version": marketplace_version},
                "plugins": [],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (plugin_dir / "plugin.json").write_text(
        json.dumps(
            {
                "name": "samsara",
                "description": "Test plugin",
                "version": plugin_version,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (repo / "pyproject.toml").write_text(
        (
            "[build-system]\n"
            'requires = ["uv_build>=0.11.9,<0.12"]\n'
            'build-backend = "uv_build"\n\n'
            "[project]\n"
            'name = "samsara"\n'
            f'version = "{pyproject_version}"\n'
            'description = "Test package"\n'
        ),
        encoding="utf-8",
    )
    return repo


class TestVersionMetadataDeath:
    def test_load_raises_with_all_mismatches_listed(self, tmp_path: Path):
        from samsara_cli.release.version_metadata import (
            VersionDriftError,
            VersionMetadata,
        )

        repo = make_repo(
            tmp_path,
            marketplace_version="0.10.0",
            plugin_version="0.9.0",
            pyproject_version="0.8.0",
        )

        with pytest.raises(VersionDriftError) as exc_info:
            VersionMetadata.load(repo)

        error = exc_info.value
        assert len(error.mismatches) == 2, (
            "SILENT FAILURE: version drift error must list every mismatched file, "
            f"not just the first mismatch. Got: {error.mismatches!r}"
        )
        paths = {mismatch.path.name for mismatch in error.mismatches}
        assert paths == {"plugin.json", "pyproject.toml"}

    @pytest.mark.parametrize(
        ("file_kind", "expected_pattern"),
        [
            ("marketplace", r"metadata\.version"),
            ("plugin", r"\bversion\b"),
            ("pyproject", r"project\.version"),
        ],
    )
    def test_missing_version_field_raises(
        self, tmp_path: Path, file_kind: str, expected_pattern: str
    ):
        from samsara_cli.release.version_metadata import (
            VersionMetadata,
            VersionMetadataError,
        )

        repo = make_repo(tmp_path)

        if file_kind == "marketplace":
            path = repo / ".claude-plugin" / "marketplace.json"
            path.write_text(
                json.dumps({"name": "samsara-marketplace", "metadata": {}}, indent=2)
                + "\n",
                encoding="utf-8",
            )
        elif file_kind == "plugin":
            path = repo / ".claude-plugin" / "plugin.json"
            path.write_text(
                json.dumps({"name": "samsara"}, indent=2) + "\n", encoding="utf-8"
            )
        else:
            path = repo / "pyproject.toml"
            path.write_text('[project]\nname = "samsara"\n', encoding="utf-8")

        with pytest.raises(VersionMetadataError, match=expected_pattern):
            VersionMetadata.load(repo)

    @pytest.mark.parametrize("bad_version", ["latest", "v1.2.3", "", "1.0"])
    def test_invalid_version_string_raises(self, tmp_path: Path, bad_version: str):
        from samsara_cli.release.version_metadata import (
            VersionMetadata,
            VersionMetadataError,
        )

        repo = make_repo(tmp_path, marketplace_version=bad_version)

        with pytest.raises(VersionMetadataError, match=r"invalid version"):
            VersionMetadata.inspect(repo)

    def test_malformed_json_or_toml_raises_with_path_context(self, tmp_path: Path):
        from samsara_cli.release.version_metadata import (
            VersionMetadata,
            VersionMetadataError,
        )

        repo = make_repo(tmp_path)
        marketplace_path = repo / ".claude-plugin" / "marketplace.json"
        marketplace_path.write_text("{not json", encoding="utf-8")

        with pytest.raises(VersionMetadataError) as exc_info:
            VersionMetadata.inspect(repo)

        assert "marketplace.json" in str(exc_info.value)

        repo = make_repo(tmp_path / "second")
        pyproject_path = repo / "pyproject.toml"
        pyproject_path.write_text(
            '[project]\nversion = "0.9.0"\nname = ', encoding="utf-8"
        )

        with pytest.raises(VersionMetadataError) as exc_info:
            VersionMetadata.inspect(repo)

        assert "pyproject.toml" in str(exc_info.value)

    def test_sync_surfaces_partial_write_risk(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        from samsara_cli.release.version_metadata import (
            PartialSyncError,
            VersionMetadata,
        )

        repo = make_repo(
            tmp_path,
            marketplace_version="1.0.0",
            plugin_version="0.9.0",
            pyproject_version="0.9.0",
        )
        plugin_path = repo / ".claude-plugin" / "plugin.json"
        pyproject_path = repo / "pyproject.toml"

        original_write_text = Path.write_text

        def failing_write_text(
            self: Path,
            data: str,
            encoding: str | None = None,
            errors: str | None = None,
            newline: str | None = None,
        ) -> int:
            if self == pyproject_path:
                raise OSError("simulated pyproject write failure")
            return original_write_text(
                self, data, encoding=encoding, errors=errors, newline=newline
            )

        monkeypatch.setattr(Path, "write_text", failing_write_text)

        with pytest.raises(PartialSyncError) as exc_info:
            VersionMetadata.sync_from_marketplace(repo)

        error = exc_info.value
        assert error.changed_paths == [plugin_path], (
            "SILENT FAILURE: partial sync error must report which files were already "
            f"written. Got: {error.changed_paths!r}"
        )
        plugin_data = json.loads(plugin_path.read_text(encoding="utf-8"))
        assert plugin_data["version"] == "1.0.0"
        assert 'version = "0.9.0"' in pyproject_path.read_text(encoding="utf-8")
