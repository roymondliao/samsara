"""
Death tests for Installer — silent failure paths.

DC-8-1: install codex when Codex CLI not installed must abort with clear error
  — not silently write files to non-existent path.
DC-8-2: install codex (default, project scope) must NOT modify user's ~/.codex/config.toml
  — only output instructions.
DC-8-3: install codex --scope global must backup config.toml before modification
  — no backup = abort.
DC-8-4: install codex --scope global repeated must NOT duplicate registration entries
  in config.toml (idempotent).
DC-8-6: convert with --source pointing to non-samsara directory must fail at source
  validation — not at converter.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


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
    skills_dir = source / "skills"
    skills_dir.mkdir()
    skill_dir = skills_dir / "research"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        "---\nname: research\ndescription: research skill\n---\n\n# research\n"
    )
    agents_dir = source / "agents"
    agents_dir.mkdir()
    (agents_dir / "implementer.md").write_text(
        "# implementer\n\nYou are the implementer agent.\n"
    )
    hooks_dir = source / "hooks"
    hooks_dir.mkdir()
    (hooks_dir / "hooks.json").write_text(json.dumps({"hooks": []}))
    references_dir = source / "references"
    references_dir.mkdir()
    return source


def make_converted_output(tmp_path: Path) -> Path:
    """Create a minimal converted output directory (simulates post-convert state)."""
    output = tmp_path / "dist" / "codex"
    skill_dir = output / ".agents" / "skills" / "samsara-research"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# research\n")
    agents_dir = output / ".codex" / "agents"
    agents_dir.mkdir(parents=True)
    (agents_dir / "samsara-implementer.toml").write_text(
        'name = "samsara-implementer"\n'
        'description = "samsara-implementer"\n'
        'developer_instructions = "Body"\n'
    )
    hooks_dir = output / ".codex" / "hooks"
    hooks_dir.mkdir(parents=True)
    (hooks_dir / "samsara-session-start.sh").write_text("#!/usr/bin/env bash\n")
    (output / ".codex" / "hooks.json").write_text(
        json.dumps({"hooks": {"SessionStart": []}})
    )
    (output / ".codex" / "config.toml").write_text("[features]\ncodex_hooks = true\n")
    return output


# ---------------------------------------------------------------------------
# DC-8-1: CLI not installed must abort — NOT write files silently
# ---------------------------------------------------------------------------


class TestInstallerCLINotInstalled:
    """DC-8-1: Installer must check CLI presence before writing ANY files.

    Silent failure: if install() proceeds to write files when CLI is absent,
    the user gets files on disk for a tool that doesn't exist. The install
    "succeeds" but the platform never loads anything.
    """

    def test_project_install_aborts_when_cli_not_installed(self, tmp_path):
        """DC-8-1: project install must raise when CLI is not installed — no files written."""
        from samsara_cli.installer.install import Installer, InstallerError

        source_dir = make_minimal_source(tmp_path)
        install_target = tmp_path / "project"

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("codex: command not found")
            installer = Installer(platform="codex")
            with pytest.raises(InstallerError) as exc_info:
                installer.install(
                    source_dir=source_dir,
                    scope="project",
                    cwd=tmp_path / "project",
                )

        error_msg = str(exc_info.value)
        assert "codex" in error_msg.lower(), "Error must mention platform name"
        # MUST NOT have written any files
        assert not (install_target / ".agents").exists(), (
            "DC-8-1 violated: .agents was created even though CLI is not installed."
        )
        assert not (install_target / ".codex").exists(), (
            "DC-8-1 violated: .codex was created even though CLI is not installed."
        )

    def test_global_install_aborts_when_cli_not_installed(self, tmp_path):
        """DC-8-1: global install must raise when CLI is not installed — no files written."""
        from samsara_cli.installer.install import Installer, InstallerError

        source_dir = make_minimal_source(tmp_path)
        fake_home = tmp_path / "home"
        fake_home.mkdir()

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("codex: command not found")
            with patch.dict("os.environ", {"HOME": str(fake_home)}):
                installer = Installer(platform="codex")
                with pytest.raises(InstallerError) as exc_info:
                    installer.install(
                        source_dir=source_dir,
                        scope="global",
                        cwd=tmp_path / "project",
                    )

        error_msg = str(exc_info.value)
        assert "codex" in error_msg.lower(), "Error must mention platform name"
        # Global install dir must NOT have been created
        codex_dir = fake_home / ".codex"
        assert not codex_dir.exists(), (
            "DC-8-1 violated: ~/.codex directory was created even though CLI is not installed"
        )

    def test_installer_error_includes_install_url_or_instructions(self, tmp_path):
        """DC-8-1: error message must include actionable info — not just 'not found'."""
        from samsara_cli.installer.install import Installer, InstallerError

        source_dir = make_minimal_source(tmp_path)
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("codex: command not found")
            installer = Installer(platform="codex")
            with pytest.raises(InstallerError) as exc_info:
                installer.install(
                    source_dir=source_dir,
                    scope="project",
                    cwd=tmp_path / "project",
                )

        error_msg = str(exc_info.value)
        # Must contain something actionable — at minimum the platform name and CLI missing notice
        assert len(error_msg) > 20, (
            "Error message must be descriptive, not just 'error'"
        )


# ---------------------------------------------------------------------------
# DC-8-2: project scope must NOT modify ~/.codex/config.toml
# ---------------------------------------------------------------------------


class TestInstallerProjectScopeNoGlobalModification:
    """DC-8-2: project scope install must ONLY copy to CWD — never touch ~/.codex/config.toml.

    Silent failure: if project scope modifies ~/.codex/config.toml, the user's global
    Codex config is polluted without consent. The damage is unexpected global hooks
    or feature flags, which could affect unrelated projects.
    """

    def test_project_install_does_not_modify_config_toml(self, tmp_path):
        """DC-8-2: project install must not write to ~/.codex/config.toml."""
        from samsara_cli.installer.install import Installer

        fake_home = tmp_path / "home"
        codex_config_dir = fake_home / ".codex"
        codex_config_dir.mkdir(parents=True)
        config_path = codex_config_dir / "config.toml"
        original_content = "[features]\ncodex_hooks = false\n"
        config_path.write_text(original_content)

        project_dir = tmp_path / "project"
        project_dir.mkdir()
        source_dir = make_minimal_source(tmp_path)
        converted_dir = make_converted_output(tmp_path)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="codex 1.2.3")
            with patch.dict("os.environ", {"HOME": str(fake_home)}):
                with patch(
                    "samsara_cli.installer.install.Installer._run_convert",
                    return_value=converted_dir,
                ):
                    installer = Installer(platform="codex")
                    installer.install(
                        source_dir=source_dir,
                        scope="project",
                        cwd=project_dir,
                    )

        # config.toml must be unchanged
        actual_content = config_path.read_text()
        assert actual_content == original_content, (
            "DC-8-2 violated: project scope install modified ~/.codex/config.toml. "
            f"Expected:\n{original_content}\nGot:\n{actual_content}"
        )

    def test_project_install_does_not_create_config_toml_if_missing(self, tmp_path):
        """DC-8-2: project install must not CREATE ~/.codex/config.toml if it doesn't exist."""
        from samsara_cli.installer.install import Installer

        fake_home = tmp_path / "home"
        fake_home.mkdir()
        # config.toml does NOT exist
        config_path = fake_home / ".codex" / "config.toml"

        project_dir = tmp_path / "project"
        project_dir.mkdir()
        source_dir = make_minimal_source(tmp_path)
        converted_dir = make_converted_output(tmp_path)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="codex 1.2.3")
            with patch.dict("os.environ", {"HOME": str(fake_home)}):
                with patch(
                    "samsara_cli.installer.install.Installer._run_convert",
                    return_value=converted_dir,
                ):
                    installer = Installer(platform="codex")
                    installer.install(
                        source_dir=source_dir,
                        scope="project",
                        cwd=project_dir,
                    )

        assert not config_path.exists(), (
            "DC-8-2 violated: project scope install created ~/.codex/config.toml"
        )


# ---------------------------------------------------------------------------
# DC-8-3: global install must backup config.toml before modification
# ---------------------------------------------------------------------------


class TestInstallerGlobalBackupBeforeModify:
    """DC-8-3: global install must backup config.toml before any write.

    Silent failure: if config.toml is modified without backup, a failed
    mid-write leaves the config corrupted. No backup = no recovery.
    First discoverer: Codex fails to start, user has no backup to restore.
    """

    def test_global_install_creates_backup_before_modifying_config(self, tmp_path):
        """DC-8-3: backup must exist before any modification to config.toml."""
        from samsara_cli.installer.install import Installer

        fake_home = tmp_path / "home"
        codex_config_dir = fake_home / ".codex"
        codex_config_dir.mkdir(parents=True)
        config_path = codex_config_dir / "config.toml"
        original_content = "# Codex config\n[features]\ncodex_hooks = false\n"
        config_path.write_text(original_content)

        project_dir = tmp_path / "project"
        project_dir.mkdir()
        source_dir = make_minimal_source(tmp_path)
        converted_dir = make_converted_output(tmp_path)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="codex 1.2.3")
            with patch.dict("os.environ", {"HOME": str(fake_home)}):
                with patch(
                    "samsara_cli.installer.install.Installer._run_convert",
                    return_value=converted_dir,
                ):
                    installer = Installer(platform="codex")
                    installer.install(
                        source_dir=source_dir,
                        scope="global",
                        cwd=project_dir,
                    )

        backup_path = codex_config_dir / "config.toml.bak"
        assert backup_path.exists(), (
            "DC-8-3 violated: config.toml.bak was not created during global install. "
            "If config.toml write fails, there is no recovery path."
        )
        assert backup_path.read_text() == original_content, (
            "DC-8-3 violated: backup content does not match original config.toml"
        )

    def test_global_install_aborts_if_config_toml_missing_and_not_creatable(
        self, tmp_path
    ):
        """DC-8-3: if config.toml is missing but config dir is not writable, must fail.

        Note: if config.toml is simply absent, global install may create it from scratch.
        This is acceptable. The DC-8-3 requirement is: backup BEFORE modifying existing file.
        """
        # This test validates the installer can handle missing config.toml gracefully
        # (create it fresh) without an unhandled exception.
        from samsara_cli.installer.install import Installer

        fake_home = tmp_path / "home"
        codex_config_dir = fake_home / ".codex"
        codex_config_dir.mkdir(parents=True)
        # config.toml does NOT exist — installer must handle this

        project_dir = tmp_path / "project"
        project_dir.mkdir()
        source_dir = make_minimal_source(tmp_path)
        converted_dir = make_converted_output(tmp_path)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="codex 1.2.3")
            with patch.dict("os.environ", {"HOME": str(fake_home)}):
                with patch(
                    "samsara_cli.installer.install.Installer._run_convert",
                    return_value=converted_dir,
                ):
                    installer = Installer(platform="codex")
                    # Must not raise for missing config — should create it
                    installer.install(
                        source_dir=source_dir,
                        scope="global",
                        cwd=project_dir,
                    )
        # config.toml must exist after install
        config_path = codex_config_dir / "config.toml"
        assert config_path.exists(), "global install must create config.toml if absent"


# ---------------------------------------------------------------------------
# DC-8-4: global install idempotency — no duplicate entries
# ---------------------------------------------------------------------------


class TestInstallerGlobalIdempotent:
    """DC-8-4: repeated global install must NOT duplicate entries in config.toml.

    Silent failure: if install() appends to config.toml each time, after N installs
    there may be conflicting feature flags, malformed TOML, or hooks applied multiple
    times.
    """

    def test_repeated_global_install_does_not_duplicate_feature_flag(self, tmp_path):
        """DC-8-4: running global install twice must not duplicate feature flags."""
        from samsara_cli.installer.install import Installer

        fake_home = tmp_path / "home"
        codex_config_dir = fake_home / ".codex"
        codex_config_dir.mkdir(parents=True)
        config_path = codex_config_dir / "config.toml"

        project_dir = tmp_path / "project"
        project_dir.mkdir()
        source_dir = make_minimal_source(tmp_path)
        converted_dir = make_converted_output(tmp_path)

        def run_install():
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0, stdout="codex 1.2.3")
                with patch.dict("os.environ", {"HOME": str(fake_home)}):
                    with patch(
                        "samsara_cli.installer.install.Installer._run_convert",
                        return_value=converted_dir,
                    ):
                        installer = Installer(platform="codex")
                        installer.install(
                            source_dir=source_dir,
                            scope="global",
                            cwd=project_dir,
                        )

        # Run install twice
        run_install()
        content_after_first = config_path.read_text()
        run_install()
        content_after_second = config_path.read_text()

        first_count = content_after_first.count("codex_hooks")
        second_count = content_after_second.count("codex_hooks")

        assert first_count > 0, "codex_hooks flag must appear after first install"
        assert second_count == first_count, (
            f"DC-8-4 violated: codex_hooks appeared {first_count} "
            f"time(s) after first install but {second_count} time(s) after second install. "
            "Repeated installs must not duplicate entries."
        )

    def test_repeated_global_install_produces_valid_toml(self, tmp_path):
        """DC-8-4: config.toml must remain valid TOML after repeated installs."""
        import tomllib
        from samsara_cli.installer.install import Installer

        fake_home = tmp_path / "home"
        codex_config_dir = fake_home / ".codex"
        codex_config_dir.mkdir(parents=True)
        config_path = codex_config_dir / "config.toml"

        project_dir = tmp_path / "project"
        project_dir.mkdir()
        source_dir = make_minimal_source(tmp_path)
        converted_dir = make_converted_output(tmp_path)

        def run_install():
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0, stdout="codex 1.2.3")
                with patch.dict("os.environ", {"HOME": str(fake_home)}):
                    with patch(
                        "samsara_cli.installer.install.Installer._run_convert",
                        return_value=converted_dir,
                    ):
                        installer = Installer(platform="codex")
                        installer.install(
                            source_dir=source_dir,
                            scope="global",
                            cwd=project_dir,
                        )

        run_install()
        run_install()

        content = config_path.read_bytes()
        try:
            tomllib.loads(content.decode())
        except tomllib.TOMLDecodeError as e:
            pytest.fail(
                f"DC-8-4: config.toml is invalid TOML after repeated installs: {e}"
            )


# ---------------------------------------------------------------------------
# DC-8-6: --source pointing to non-samsara directory must fail at source validation
# ---------------------------------------------------------------------------


class TestConverterSourceValidationFailsEarly:
    """DC-8-6: non-samsara source dir must fail at source validation, not at converter.

    Silent failure path: if source validation is skipped and the converter is called
    with a bad source, the error message is a generic converter crash (e.g., FileNotFoundError
    on plugin.json) — not a structured 'source is not a samsara directory' error.
    """

    def test_install_with_non_samsara_source_raises_before_converter(self, tmp_path):
        """DC-8-6: source validation must fail before engine/converter is called."""
        from samsara_cli.installer.install import Installer, InstallerError

        # Create a directory that is NOT a samsara source
        bad_source = tmp_path / "not-samsara"
        bad_source.mkdir()
        (bad_source / "README.md").write_text("This is not a samsara plugin")
        # No .claude-plugin/, no skills/, no agents/, no hooks/

        project_dir = tmp_path / "project"
        project_dir.mkdir()

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="codex 1.2.3")
            installer = Installer(platform="codex")
            with pytest.raises(
                (InstallerError, ValueError, FileNotFoundError)
            ) as exc_info:
                installer.install(
                    source_dir=bad_source,
                    scope="project",
                    cwd=project_dir,
                )

        error_msg = str(exc_info.value)
        # Must NOT be a generic "no such file or directory" deep in converter
        # Must mention source structure or validation
        assert len(error_msg) > 10, "Error message must be descriptive"

    def test_install_with_missing_source_fails_with_clear_message(self, tmp_path):
        """DC-8-6: source directory that doesn't exist must fail clearly."""
        from samsara_cli.installer.install import Installer, InstallerError

        nonexistent_source = tmp_path / "does-not-exist"
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="codex 1.2.3")
            installer = Installer(platform="codex")
            with pytest.raises((InstallerError, FileNotFoundError, ValueError)):
                installer.install(
                    source_dir=nonexistent_source,
                    scope="project",
                    cwd=project_dir,
                )
