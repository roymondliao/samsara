"""Happy-path tests for `samsara-cli release` commands."""

import json
import re
from pathlib import Path

from typer.testing import CliRunner


runner = CliRunner()

_SEMVER = re.compile(r"^\d+\.\d+\.\d+$")


def make_repo(
    tmp_path: Path,
    *,
    marketplace_version: str = "0.9.0",
    plugin_version: str | None = None,
    pyproject_version: str | None = None,
    lock_version: str | None = None,
) -> Path:
    plugin_version = marketplace_version if plugin_version is None else plugin_version
    pyproject_version = (
        marketplace_version if pyproject_version is None else pyproject_version
    )
    lock_version = marketplace_version if lock_version is None else lock_version
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
            lock_version="0.9.0",
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
        assert 'version = "2.0.0"' in (repo / "uv.lock").read_text(encoding="utf-8")

    def test_sync_version_check_mode_does_not_write(self, tmp_path: Path):
        from samsara_cli.main import app

        repo = make_repo(
            tmp_path,
            marketplace_version="2.0.0",
            plugin_version="0.9.0",
            pyproject_version="0.9.0",
            lock_version="0.9.0",
        )
        plugin_before = (repo / ".claude-plugin" / "plugin.json").read_text(
            encoding="utf-8"
        )
        pyproject_before = (repo / "pyproject.toml").read_text(encoding="utf-8")
        lock_before = (repo / "uv.lock").read_text(encoding="utf-8")

        result = runner.invoke(
            app, ["release", "sync-version", "--root", str(repo), "--check"]
        )

        assert result.exit_code == 0, result.output
        assert "plugin.json" in result.output
        assert "uv.lock" in result.output
        assert (repo / ".claude-plugin" / "plugin.json").read_text(
            encoding="utf-8"
        ) == plugin_before
        assert (repo / "pyproject.toml").read_text(encoding="utf-8") == pyproject_before
        assert (repo / "uv.lock").read_text(encoding="utf-8") == lock_before


class TestCurrentReleaseVersionContract:
    """CLI version surfaces must track the source-of-truth, not a hardcoded literal.

    marketplace.json `metadata.version` is the single source of truth. `print-tag`
    derives its value from marketplace.json; `version` derives it independently from
    the installed package metadata (pyproject). Both must agree with the source of
    truth and emit a well-formed value — otherwise the release has drifted. The
    expected version is read at test time, so a routine version bump never edits this
    test; only an actual drift or format break makes it fail.
    """

    @staticmethod
    def _source_of_truth_version() -> str:
        repo_root = Path(__file__).resolve().parents[2]
        marketplace = repo_root / ".claude-plugin" / "marketplace.json"
        data = json.loads(marketplace.read_text(encoding="utf-8"))
        version = data["metadata"]["version"]
        assert _SEMVER.match(version), f"marketplace version is not semver: {version!r}"
        return version

    def test_print_tag_tracks_source_of_truth(self):
        from samsara_cli.main import app

        repo_root = Path(__file__).resolve().parents[2]
        expected = self._source_of_truth_version()

        result = runner.invoke(app, ["release", "print-tag", "--root", str(repo_root)])

        assert result.exit_code == 0, result.output
        assert result.output.strip() == f"v{expected}"

    def test_cli_version_tracks_source_of_truth(self):
        from samsara_cli.main import app

        expected = self._source_of_truth_version()

        result = runner.invoke(app, ["version"])

        assert result.exit_code == 0, result.output
        assert result.output.strip() == f"samsara-cli {expected}"

    def test_print_tag_outputs_exact_tag(self, tmp_path: Path):
        from samsara_cli.main import app

        repo = make_repo(tmp_path, marketplace_version="1.2.3")

        result = runner.invoke(app, ["release", "print-tag", "--root", str(repo)])

        assert result.exit_code == 0, result.output
        assert result.output.strip() == "v1.2.3"
