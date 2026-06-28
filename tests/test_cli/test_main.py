"""
Unit tests for CLI commands (Typer app) — happy path and behavioral contracts.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from conftest import FIXTURE_VERSION


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
        json.dumps({"name": "samsara", "version": FIXTURE_VERSION})
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


def make_converted_output(tmp_path: Path) -> Path:
    """Create a minimal converted output directory."""
    output = tmp_path / "dist" / "codex"
    skill_dir = output / ".agents" / "skills" / "samsara-research"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\nname: samsara:research\ndescription: research skill\n---\n\n# research\n"
    )
    agents_dir = output / ".codex" / "agents"
    agents_dir.mkdir(parents=True)
    (agents_dir / "samsara-implementer.toml").write_text(
        'name = "samsara-implementer"\n'
        'description = "samsara-implementer"\n'
        'developer_instructions = "Body"\n'
    )
    (output / ".codex" / "hooks.json").write_text(json.dumps({"hooks": {}}))
    return output


# ---------------------------------------------------------------------------
# list-platforms command
# ---------------------------------------------------------------------------


class TestCLIListPlatforms:
    """list-platforms must show available platforms."""

    def test_list_platforms_exits_zero(self):
        """list-platforms exits 0."""
        from samsara_cli.main import app

        result = runner.invoke(app, ["list-platforms"])
        assert result.exit_code == 0, (
            f"exit code: {result.exit_code}, output: {result.output}"
        )

    def test_list_platforms_includes_codex(self):
        """list-platforms output includes 'codex'."""
        from samsara_cli.main import app

        result = runner.invoke(app, ["list-platforms"])
        assert "codex" in result.output.lower(), (
            f"list-platforms must include 'codex' in output. Got: {result.output!r}"
        )

    def test_list_platforms_includes_gemini_cli(self):
        """list-platforms output includes 'gemini-cli'."""
        from samsara_cli.main import app

        result = runner.invoke(app, ["list-platforms"])
        assert "gemini-cli" in result.output.lower(), (
            f"list-platforms must include 'gemini-cli'. Got: {result.output!r}"
        )


# ---------------------------------------------------------------------------
# version command
# ---------------------------------------------------------------------------


class TestCLIVersion:
    """version command basic behavior."""

    def test_version_exits_zero(self):
        """version exits 0."""
        from samsara_cli.main import app

        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0

    def test_version_outputs_something(self):
        """version outputs non-empty string."""
        from samsara_cli.main import app

        result = runner.invoke(app, ["version"])
        assert len(result.output.strip()) > 0

    def test_version_outputs_release_version(self):
        """version reports the current packaged release."""
        from importlib.metadata import version as pkg_version

        from samsara_cli.main import app

        result = runner.invoke(app, ["version"])
        assert result.output.strip() == f"samsara-cli {pkg_version('samsara')}"


# ---------------------------------------------------------------------------
# convert command
# ---------------------------------------------------------------------------


class TestCLIConvert:
    """convert command: basic invocation contracts."""

    def test_convert_valid_platform_exits_zero(self, tmp_path):
        """convert --platform codex with valid source exits 0."""
        from samsara_cli.main import app

        source_dir = make_minimal_source(tmp_path)
        output_dir = tmp_path / "dist" / "codex"

        with patch("samsara_cli.main.ConversionEngine") as MockEngine:
            mock_engine = MagicMock()
            MockEngine.return_value = mock_engine
            mock_engine.run.return_value = None

            result = runner.invoke(
                app,
                [
                    "convert",
                    "--platform",
                    "codex",
                    "--source",
                    str(source_dir),
                    "--output",
                    str(output_dir),
                ],
            )

        assert result.exit_code == 0, (
            f"convert must exit 0 on success. exit code: {result.exit_code}, "
            f"output: {result.output}"
        )

    def test_convert_invalid_platform_exits_nonzero(self, tmp_path):
        """convert with invalid platform exits non-zero."""
        from samsara_cli.main import app

        result = runner.invoke(
            app,
            ["convert", "--platform", "invalid-xyz", "--source", str(tmp_path)],
        )
        assert result.exit_code != 0

    def test_convert_missing_source_exits_nonzero(self, tmp_path):
        """convert with nonexistent --source exits non-zero."""
        from samsara_cli.main import app

        result = runner.invoke(
            app,
            [
                "convert",
                "--platform",
                "codex",
                "--source",
                str(tmp_path / "does-not-exist"),
            ],
        )
        assert result.exit_code != 0

    def test_convert_accepts_no_source_argument(self, tmp_path):
        """convert accepts invocation without --source (uses cwd as default).

        We cannot easily test the actual cwd default behavior without either
        changing cwd (side effect) or patching Path.cwd() (fragile). Instead,
        we test that the command signature accepts omission of --source.
        The CLI code path is: source = source or Path.cwd() — verified by code review.
        """
        from samsara_cli.main import app

        output_dir = tmp_path / "dist" / "codex"

        with patch("samsara_cli.main.ConversionEngine") as MockEngine:
            mock_engine = MagicMock()
            MockEngine.return_value = mock_engine
            mock_engine.run.return_value = None
            # Invoke without --source — should not raise a "missing required argument" error
            # It will try to use cwd as source (may fail if cwd is not samsara source, but
            # that's a source validation error, not a CLI argument error)
            result = runner.invoke(
                app,
                [
                    "convert",
                    "--platform",
                    "codex",
                    "--output",
                    str(output_dir),
                ],
            )
            # Either succeeds (if run from samsara root) or fails with source validation error
            # Must NOT fail with "missing required argument --source"
            if result.exit_code != 0:
                assert (
                    "missing" not in result.output.lower()
                    or "source" not in result.output.lower()
                ), "--source must be optional (has default). Got: " + result.output


# ---------------------------------------------------------------------------
# install command
# ---------------------------------------------------------------------------


class TestCLIInstall:
    """install command: basic invocation contracts."""

    def test_install_valid_platform_exits_zero(self, tmp_path):
        """install codex exits 0 when CLI is present and source is valid."""
        from samsara_cli.main import app

        source_dir = make_minimal_source(tmp_path)
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        converted_dir = make_converted_output(tmp_path)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="codex 1.2.3")
            with patch(
                "samsara_cli.installer.install.Installer._run_convert",
                return_value=converted_dir,
            ):
                result = runner.invoke(
                    app,
                    [
                        "install",
                        "codex",
                        "--source",
                        str(source_dir),
                        "--scope",
                        "project",
                        "--project-dir",
                        str(project_dir),
                    ],
                    env={"HOME": str(tmp_path / "home")},
                )

        assert result.exit_code == 0, (
            f"install must exit 0 on success. exit: {result.exit_code}, output: {result.output}"
        )

    def test_install_gemini_cli_constructs_gemini_installer(self, tmp_path):
        """install gemini-cli must pass gemini-cli to Installer."""
        from samsara_cli.main import app

        source_dir = make_minimal_source(tmp_path)

        with patch("samsara_cli.main.Installer") as MockInstaller:
            mock_installer = MagicMock()
            MockInstaller.return_value = mock_installer
            mock_installer.install.return_value = "installed"

            result = runner.invoke(
                app,
                ["install", "gemini-cli", "--source", str(source_dir)],
            )

        assert result.exit_code == 0
        MockInstaller.assert_called_once_with(platform="gemini-cli")

    def test_install_prints_post_install_instructions(self, tmp_path):
        """install must print post-install instructions."""
        from samsara_cli.main import app

        source_dir = make_minimal_source(tmp_path)
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        converted_dir = make_converted_output(tmp_path)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="codex 1.2.3")
            with patch(
                "samsara_cli.installer.install.Installer._run_convert",
                return_value=converted_dir,
            ):
                result = runner.invoke(
                    app,
                    [
                        "install",
                        "codex",
                        "--source",
                        str(source_dir),
                        "--scope",
                        "project",
                        "--project-dir",
                        str(project_dir),
                    ],
                    env={"HOME": str(tmp_path / "home")},
                )

        assert len(result.output.strip()) > 0, "install must produce output"

    def test_install_invalid_platform_exits_nonzero(self, tmp_path):
        """install with invalid platform exits non-zero."""
        from samsara_cli.main import app

        result = runner.invoke(
            app,
            ["install", "invalid-xyz", "--source", str(tmp_path)],
        )
        assert result.exit_code != 0

    def test_install_global_scope_accepted(self, tmp_path):
        """install --scope global is a valid argument."""
        from samsara_cli.main import app

        source_dir = make_minimal_source(tmp_path)
        fake_home = tmp_path / "home"
        fake_home.mkdir()
        converted_dir = make_converted_output(tmp_path)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="codex 1.2.3")
            with patch(
                "samsara_cli.installer.install.Installer._run_convert",
                return_value=converted_dir,
            ):
                result = runner.invoke(
                    app,
                    [
                        "install",
                        "codex",
                        "--source",
                        str(source_dir),
                        "--scope",
                        "global",
                    ],
                    env={"HOME": str(fake_home)},
                )

        # Exit code 0 = accepted (even if instructions printed)
        assert result.exit_code == 0, (
            f"install --scope global must exit 0. exit: {result.exit_code}, "
            f"output: {result.output}"
        )


# ---------------------------------------------------------------------------
# update command
# ---------------------------------------------------------------------------


class TestCLIUpdate:
    """update command: basic invocation contracts."""

    def test_update_valid_platform_exits_zero(self, tmp_path):
        """update codex exits 0 when CLI is present and source is valid."""
        from samsara_cli.main import app

        source_dir = make_minimal_source(tmp_path)
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        converted_dir = make_converted_output(tmp_path)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="codex 1.2.3")
            with patch(
                "samsara_cli.installer.install.Installer._run_convert",
                return_value=converted_dir,
            ):
                result = runner.invoke(
                    app,
                    [
                        "update",
                        "codex",
                        "--source",
                        str(source_dir),
                        "--scope",
                        "project",
                        "--project-dir",
                        str(project_dir),
                    ],
                    env={"HOME": str(tmp_path / "home")},
                )

        assert result.exit_code == 0, (
            f"update must exit 0. exit: {result.exit_code}, output: {result.output}"
        )

    def test_update_gemini_cli_constructs_gemini_installer(self, tmp_path):
        """update gemini-cli must pass gemini-cli to Installer."""
        from samsara_cli.main import app

        source_dir = make_minimal_source(tmp_path)

        with patch("samsara_cli.main.Installer") as MockInstaller:
            mock_installer = MagicMock()
            MockInstaller.return_value = mock_installer
            mock_installer.update.return_value = "updated"

            result = runner.invoke(
                app,
                ["update", "gemini-cli", "--source", str(source_dir)],
            )

        assert result.exit_code == 0
        MockInstaller.assert_called_once_with(platform="gemini-cli")

    def test_update_invalid_platform_exits_nonzero(self):
        """update with invalid platform exits non-zero."""
        from samsara_cli.main import app

        result = runner.invoke(app, ["update", "invalid-xyz"])
        assert result.exit_code != 0


# ---------------------------------------------------------------------------
# validate command
# ---------------------------------------------------------------------------


class TestCLIValidate:
    """validate command: basic invocation contracts."""

    def test_validate_valid_output_exits_zero(self, tmp_path):
        """validate --platform codex with valid converted output exits 0."""
        from samsara_cli.main import app

        converted_dir = make_converted_output(tmp_path)

        with patch("samsara_cli.main.TargetValidator") as MockValidator:
            mock_validator = MagicMock()
            MockValidator.return_value = mock_validator
            mock_validator.validate.return_value = []  # no errors

            result = runner.invoke(
                app,
                [
                    "validate",
                    "--platform",
                    "codex",
                    "--source",
                    str(converted_dir),
                ],
            )

        assert result.exit_code == 0, (
            f"validate must exit 0 when no errors. exit: {result.exit_code}, "
            f"output: {result.output}"
        )

    def test_validate_passes_gemini_platform_to_validator(self, tmp_path):
        """validate --platform gemini-cli must pass platform context to validator."""
        from samsara_cli.main import app

        converted_dir = make_converted_output(tmp_path)

        with patch("samsara_cli.main.TargetValidator") as MockValidator:
            mock_validator = MagicMock()
            MockValidator.return_value = mock_validator
            mock_validator.validate.return_value = []

            result = runner.invoke(
                app,
                [
                    "validate",
                    "--platform",
                    "gemini-cli",
                    "--source",
                    str(converted_dir),
                ],
            )

        assert result.exit_code == 0
        mock_validator.validate.assert_called_once_with(
            output_dir=converted_dir,
            platform="gemini-cli",
        )

    def test_validate_with_errors_exits_nonzero(self, tmp_path):
        """validate exits non-zero when validator reports errors."""
        from samsara_cli.main import app

        converted_dir = make_converted_output(tmp_path)

        with patch("samsara_cli.main.TargetValidator") as MockValidator:
            mock_validator = MagicMock()
            MockValidator.return_value = mock_validator
            mock_validator.validate.return_value = ["Error: unconverted pattern found"]

            result = runner.invoke(
                app,
                [
                    "validate",
                    "--platform",
                    "codex",
                    "--source",
                    str(converted_dir),
                ],
            )

        assert result.exit_code != 0, (
            "validate must exit non-zero when errors are reported"
        )

    def test_validate_invalid_platform_exits_nonzero(self, tmp_path):
        """validate with invalid --platform exits non-zero."""
        from samsara_cli.main import app

        result = runner.invoke(
            app,
            ["validate", "--platform", "invalid-xyz", "--source", str(tmp_path)],
        )
        assert result.exit_code != 0
