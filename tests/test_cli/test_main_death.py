"""
Death tests for CLI commands — silent failure paths at the CLI boundary.

DC-8-1: convert/install with CLI not installed must produce clear error, not exit 0
DC-8-5: convert with invalid --platform must fail with list of available platforms
DC-8-6: convert with non-samsara --source must fail at source validation
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner


runner = CliRunner()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_minimal_source(tmp_path: Path) -> Path:
    """Create a minimal valid samsara source directory."""
    source = tmp_path / "source"
    plugin_dir = source / ".claude-plugin"
    plugin_dir.mkdir(parents=True)
    (plugin_dir / "plugin.json").write_text(
        json.dumps({"name": "samsara", "version": "0.8.0"})
    )
    (source / "skills").mkdir()
    skill = source / "skills" / "research"
    skill.mkdir()
    (skill / "SKILL.md").write_text(
        "---\nname: research\ndescription: research skill\n---\n\n# research\n"
    )
    (source / "agents").mkdir()
    (source / "agents" / "implementer.md").write_text(
        "# implementer\n\nYou are the implementer agent.\n"
    )
    (source / "hooks").mkdir()
    (source / "hooks" / "hooks.json").write_text(json.dumps({"hooks": []}))
    (source / "references").mkdir()
    return source


# ---------------------------------------------------------------------------
# DC-8-5: invalid --platform must list available platforms
# ---------------------------------------------------------------------------


class TestCLIConvertInvalidPlatform:
    """DC-8-5: convert with invalid --platform must exit non-zero with platform list.

    Silent failure path: if CLI exits 0 with a generic "platform not found" message,
    the user has no guidance on what platforms are valid.
    """

    def test_convert_invalid_platform_exits_nonzero(self, tmp_path):
        """DC-8-5: convert --platform nonexistent must exit non-zero."""
        from samsara_cli.main import app

        result = runner.invoke(
            app,
            ["convert", "--platform", "nonexistent-xyz", "--source", str(tmp_path)],
        )
        assert result.exit_code != 0, (
            "DC-8-5: convert with invalid platform must exit non-zero, not 0. "
            f"Exit code: {result.exit_code}, output: {result.output}"
        )

    def test_convert_invalid_platform_output_contains_platform_list(self, tmp_path):
        """DC-8-5: convert error must list available platforms."""
        from samsara_cli.main import app

        result = runner.invoke(
            app,
            ["convert", "--platform", "nonexistent-xyz", "--source", str(tmp_path)],
        )
        output = result.output.lower()
        # Must mention 'codex' (the only known platform)
        assert "codex" in output, (
            f"DC-8-5: error output must list available platforms (should include 'codex'). "
            f"Got: {result.output!r}"
        )
        assert "gemini-cli" in output, (
            "DC-8-5: error output must list available platforms and include 'gemini-cli'. "
            f"Got: {result.output!r}"
        )


# ---------------------------------------------------------------------------
# DC-8-1: install with CLI not installed must exit non-zero
# ---------------------------------------------------------------------------


class TestCLIInstallCLINotInstalled:
    """DC-8-1: install when platform CLI absent must exit non-zero with clear message."""

    def test_install_exits_nonzero_when_cli_not_found(self, tmp_path):
        """DC-8-1: samsara-cli install codex must exit non-zero when codex is not installed."""
        from samsara_cli.main import app

        source_dir = make_minimal_source(tmp_path)
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("codex: command not found")
            result = runner.invoke(
                app,
                ["install", "codex", "--source", str(source_dir)],
                catch_exceptions=False,
            )
        assert result.exit_code != 0, (
            f"DC-8-1: install must exit non-zero when CLI is not installed. "
            f"Exit code: {result.exit_code}, output: {result.output}"
        )

    def test_install_error_mentions_platform_not_installed(self, tmp_path):
        """DC-8-1: error message must indicate platform CLI is not installed."""
        from samsara_cli.main import app

        source_dir = make_minimal_source(tmp_path)
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("codex: command not found")
            result = runner.invoke(
                app,
                ["install", "codex", "--source", str(source_dir)],
            )
        output = result.output.lower()
        assert "codex" in output, "Error message must mention the platform name"
        # Must not just say "done" or be empty
        assert len(result.output.strip()) > 5, "Error message must not be empty"


# ---------------------------------------------------------------------------
# project destination must be explicit when installing from samsara repo
# ---------------------------------------------------------------------------


class TestCLIProjectDirDestination:
    """Project installs must support a destination separate from samsara source."""

    def test_install_project_dir_is_destination_not_source(self, tmp_path):
        """--project-dir must be passed as installer cwd while source defaults to cwd."""
        from samsara_cli.main import app

        project_dir = tmp_path / "target-project"
        project_dir.mkdir()

        with patch("samsara_cli.main.Installer") as MockInstaller:
            mock_installer = MagicMock()
            MockInstaller.return_value = mock_installer
            mock_installer.install.return_value = "installed"

            source_cwd = Path.cwd()
            result = runner.invoke(
                app,
                ["install", "codex", "--project-dir", str(project_dir)],
            )

        assert result.exit_code == 0, result.output
        mock_installer.install.assert_called_once_with(
            source_dir=source_cwd,
            scope="project",
            cwd=project_dir,
            converted_source_dir=None,
        )

    def test_update_project_dir_is_destination_not_source(self, tmp_path):
        """update must use --project-dir as destination while source defaults to cwd."""
        from samsara_cli.main import app

        project_dir = tmp_path / "target-project"
        project_dir.mkdir()

        with patch("samsara_cli.main.Installer") as MockInstaller:
            mock_installer = MagicMock()
            MockInstaller.return_value = mock_installer
            mock_installer.update.return_value = "updated"

            source_cwd = Path.cwd()
            result = runner.invoke(
                app,
                ["update", "gemini-cli", "--project-dir", str(project_dir)],
            )

        assert result.exit_code == 0, result.output
        mock_installer.update.assert_called_once_with(
            source_dir=source_cwd,
            scope="project",
            cwd=project_dir,
        )

    def test_global_scope_rejects_project_dir(self, tmp_path):
        """--project-dir must not be silently ignored for global installs."""
        from samsara_cli.main import app

        project_dir = tmp_path / "target-project"
        project_dir.mkdir()

        result = runner.invoke(
            app,
            [
                "install",
                "codex",
                "--scope",
                "global",
                "--project-dir",
                str(project_dir),
            ],
        )

        assert result.exit_code != 0
        assert "--project-dir is only valid with --scope project" in result.output


# ---------------------------------------------------------------------------
# DC-8-6: --source pointing to non-samsara dir must fail at source validation
# ---------------------------------------------------------------------------


class TestCLIConvertNonSamsaraSource:
    """DC-8-6: convert/install with non-samsara source must fail at source validation."""

    def test_convert_non_samsara_source_exits_nonzero(self, tmp_path):
        """DC-8-6: convert with non-samsara --source must exit non-zero."""
        from samsara_cli.main import app

        bad_source = tmp_path / "not-samsara"
        bad_source.mkdir()
        (bad_source / "README.md").write_text("Not a samsara plugin")

        result = runner.invoke(
            app,
            ["convert", "--platform", "codex", "--source", str(bad_source)],
        )
        assert result.exit_code != 0, (
            f"DC-8-6: convert with non-samsara source must exit non-zero. "
            f"Exit code: {result.exit_code}"
        )

    def test_convert_non_samsara_source_error_is_descriptive(self, tmp_path):
        """DC-8-6: source validation error must be more informative than generic crash."""
        from samsara_cli.main import app

        bad_source = tmp_path / "not-samsara"
        bad_source.mkdir()

        result = runner.invoke(
            app,
            ["convert", "--platform", "codex", "--source", str(bad_source)],
        )
        # Error output must say something useful (not just a Python traceback)
        assert len(result.output.strip()) > 0, "Error output must not be empty"
