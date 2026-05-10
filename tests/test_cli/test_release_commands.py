"""Happy-path tests for `samsara-cli release` commands."""

import json
from pathlib import Path

from typer.testing import CliRunner


runner = CliRunner()


def make_repo(
    tmp_path: Path,
    *,
    marketplace_version: str = "0.9.0",
    plugin_version: str | None = None,
    pyproject_version: str | None = None,
) -> Path:
    plugin_version = marketplace_version if plugin_version is None else plugin_version
    pyproject_version = (
        marketplace_version if pyproject_version is None else pyproject_version
    )
    repo = tmp_path / "repo"
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
        json.dumps({"name": "samsara", "version": plugin_version}, indent=2) + "\n",
        encoding="utf-8",
    )
    (repo / "pyproject.toml").write_text(
        (f'[project]\nname = "samsara"\nversion = "{pyproject_version}"\n'),
        encoding="utf-8",
    )
    return repo


class TestReleaseCommands:
    def test_check_version_success(self, tmp_path: Path):
        from samsara_cli.main import app

        repo = make_repo(tmp_path, marketplace_version="1.2.3")

        result = runner.invoke(app, ["release", "check-version", "--root", str(repo)])

        assert result.exit_code == 0, result.output
        assert "1.2.3" in result.output
        assert "v1.2.3" in result.output

    def test_check_version_json_success(self, tmp_path: Path):
        from samsara_cli.main import app

        repo = make_repo(tmp_path, marketplace_version="1.2.3")

        result = runner.invoke(
            app, ["release", "check-version", "--root", str(repo), "--json"]
        )

        assert result.exit_code == 0, result.output
        payload = json.loads(result.output)
        assert payload["version"] == "1.2.3"
        assert payload["tag"] == "v1.2.3"
        assert payload["is_synced"] is True

    def test_sync_version_updates_files(self, tmp_path: Path):
        from samsara_cli.main import app

        repo = make_repo(
            tmp_path,
            marketplace_version="2.0.0",
            plugin_version="0.9.0",
            pyproject_version="0.9.0",
        )

        result = runner.invoke(app, ["release", "sync-version", "--root", str(repo)])

        assert result.exit_code == 0, result.output
        plugin_data = json.loads(
            (repo / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        assert plugin_data["version"] == "2.0.0"
        assert 'version = "2.0.0"' in (repo / "pyproject.toml").read_text(
            encoding="utf-8"
        )

    def test_sync_version_check_mode_does_not_write(self, tmp_path: Path):
        from samsara_cli.main import app

        repo = make_repo(
            tmp_path,
            marketplace_version="2.0.0",
            plugin_version="0.9.0",
            pyproject_version="0.9.0",
        )
        plugin_before = (repo / ".claude-plugin" / "plugin.json").read_text(
            encoding="utf-8"
        )

        result = runner.invoke(
            app, ["release", "sync-version", "--root", str(repo), "--check"]
        )

        assert result.exit_code == 0, result.output
        assert "plugin.json" in result.output
        assert (repo / ".claude-plugin" / "plugin.json").read_text(
            encoding="utf-8"
        ) == plugin_before

    def test_print_tag_outputs_exact_tag(self, tmp_path: Path):
        from samsara_cli.main import app

        repo = make_repo(tmp_path, marketplace_version="1.2.3")

        result = runner.invoke(app, ["release", "print-tag", "--root", str(repo)])

        assert result.exit_code == 0, result.output
        assert result.output.strip() == "v1.2.3"
