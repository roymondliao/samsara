"""
Happy-path tests for release version metadata.
"""

import json
from pathlib import Path


def make_repo(
    tmp_path: Path,
    *,
    marketplace_version: str = "0.9.0",
    plugin_version: str | None = None,
    pyproject_version: str | None = None,
    lock_version: str | None = None,
) -> Path:
    repo = tmp_path / "repo"
    plugin_version = marketplace_version if plugin_version is None else plugin_version
    pyproject_version = (
        marketplace_version if pyproject_version is None else pyproject_version
    )
    lock_version = marketplace_version if lock_version is None else lock_version
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
    (repo / "uv.lock").write_text(
        (
            "version = 1\n\n"
            "[[package]]\n"
            'name = "samsara"\n'
            f'version = "{lock_version}"\n'
            'source = { editable = "." }\n'
        ),
        encoding="utf-8",
    )
    return repo


class TestVersionMetadata:
    def test_load_returns_synced_versions_and_tag(self, tmp_path: Path):
        from samsara_cli.release.version_metadata import VersionMetadata

        repo = make_repo(tmp_path, marketplace_version="1.2.3")

        metadata = VersionMetadata.load(repo)

        assert metadata.marketplace_version == "1.2.3"
        assert metadata.plugin_version == "1.2.3"
        assert metadata.pyproject_version == "1.2.3"
        assert metadata.lock_version == "1.2.3"
        assert metadata.tag == "v1.2.3"

    def test_inspect_reports_sync_state_without_raising(self, tmp_path: Path):
        from samsara_cli.release.version_metadata import VersionMetadata

        repo = make_repo(
            tmp_path,
            marketplace_version="1.0.0",
            plugin_version="0.9.0",
            pyproject_version="1.0.0",
        )

        metadata = VersionMetadata.inspect(repo)

        assert len(metadata.mismatches) == 1
        assert metadata.mismatches[0].path.name == "plugin.json"
        assert metadata.is_synced is False

    def test_sync_from_marketplace_updates_secondary_files(self, tmp_path: Path):
        from samsara_cli.release.version_metadata import VersionMetadata

        repo = make_repo(
            tmp_path,
            marketplace_version="2.0.0",
            plugin_version="0.9.0",
            pyproject_version="0.9.0",
            lock_version="0.9.0",
        )

        result = VersionMetadata.sync_from_marketplace(repo)

        assert result.version == "2.0.0"
        assert result.tag == "v2.0.0"
        assert {path.name for path in result.changed_paths} == {
            "plugin.json",
            "pyproject.toml",
            "uv.lock",
        }

        metadata = VersionMetadata.load(repo)
        assert metadata.is_synced is True

    def test_sync_from_marketplace_check_mode_does_not_write(self, tmp_path: Path):
        from samsara_cli.release.version_metadata import VersionMetadata

        repo = make_repo(
            tmp_path,
            marketplace_version="2.1.0",
            plugin_version="0.9.0",
            pyproject_version="0.9.0",
            lock_version="0.9.0",
        )
        plugin_before = (repo / ".claude-plugin" / "plugin.json").read_text(
            encoding="utf-8"
        )
        pyproject_before = (repo / "pyproject.toml").read_text(encoding="utf-8")

        result = VersionMetadata.sync_from_marketplace(repo, check_only=True)

        assert {path.name for path in result.changed_paths} == {
            "plugin.json",
            "pyproject.toml",
            "uv.lock",
        }
        assert (repo / ".claude-plugin" / "plugin.json").read_text(
            encoding="utf-8"
        ) == plugin_before
        assert (repo / "pyproject.toml").read_text(encoding="utf-8") == pyproject_before

    def test_sync_from_marketplace_accepts_prerelease_versions(self, tmp_path: Path):
        from samsara_cli.release.version_metadata import VersionMetadata

        repo = make_repo(
            tmp_path,
            marketplace_version="1.0.0-rc.1",
            plugin_version="0.9.0",
            pyproject_version="0.9.0",
            lock_version="0.9.0",
        )

        result = VersionMetadata.sync_from_marketplace(repo)

        assert result.tag == "v1.0.0-rc.1"
        metadata = VersionMetadata.load(repo)
        assert metadata.marketplace_version == "1.0.0-rc.1"
