"""Death tests for `samsara-cli release` commands."""

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
                "name": "samsara-marketplace",
                "metadata": {"version": marketplace_version},
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


class TestReleaseCommandDeaths:
    def test_check_version_fails_on_drift_and_lists_all_files(self, tmp_path: Path):
        from samsara_cli.main import app

        repo = make_repo(
            tmp_path,
            marketplace_version="1.0.0",
            plugin_version="0.9.0",
            pyproject_version="0.8.0",
        )

        result = runner.invoke(app, ["release", "check-version", "--root", str(repo)])

        assert result.exit_code != 0
        assert "plugin.json" in result.output
        assert "pyproject.toml" in result.output

    def test_print_tag_fails_on_drift_instead_of_printing_tag(self, tmp_path: Path):
        from samsara_cli.main import app

        repo = make_repo(
            tmp_path,
            marketplace_version="1.0.0",
            plugin_version="0.9.0",
            pyproject_version="0.9.0",
        )

        result = runner.invoke(app, ["release", "print-tag", "--root", str(repo)])

        assert result.exit_code != 0
        assert result.output.strip() != "v1.0.0"

    def test_sync_version_check_does_not_write_even_on_drift(self, tmp_path: Path):
        from samsara_cli.main import app

        repo = make_repo(
            tmp_path,
            marketplace_version="1.0.0",
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
        assert (repo / ".claude-plugin" / "plugin.json").read_text(
            encoding="utf-8"
        ) == plugin_before

    def test_expected_errors_do_not_dump_python_tracebacks(self, tmp_path: Path):
        from samsara_cli.main import app

        repo = make_repo(tmp_path)
        (repo / ".claude-plugin" / "marketplace.json").write_text(
            "{not json", encoding="utf-8"
        )

        result = runner.invoke(app, ["release", "check-version", "--root", str(repo)])

        assert result.exit_code != 0
        assert "traceback" not in result.output.lower()
