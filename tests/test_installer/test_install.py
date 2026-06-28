"""
Unit tests for Installer — happy path and behavioral contracts.
"""

import json
import tomllib
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from conftest import FIXTURE_VERSION


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
    """Create a minimal converted output directory."""
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
    (output / ".codex" / "config.toml").write_text("[features]\nhooks = true\n")
    return output


# ---------------------------------------------------------------------------
# Project scope install
# ---------------------------------------------------------------------------


class TestInstallerProjectScope:
    """Project scope install: copies native Codex files, no global config changes."""

    def test_project_install_copies_to_cwd(self, tmp_path):
        """Project install copies native Codex skills and config to CWD."""
        from samsara_cli.installer.install import Installer

        project_dir = tmp_path / "project"
        project_dir.mkdir()
        source_dir = make_minimal_source(tmp_path)
        converted_dir = make_converted_output(tmp_path)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="codex 1.2.3")
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

        assert (project_dir / ".agents" / "skills" / "samsara-research").is_dir()
        assert (project_dir / ".codex" / "agents").is_dir()
        assert (project_dir / ".codex" / "hooks.json").exists()

    def test_project_install_migrates_deprecated_codex_feature_flag(self, tmp_path):
        """Project install replaces deprecated codex_hooks with hooks."""
        from samsara_cli.installer.install import Installer

        project_dir = tmp_path / "project"
        project_codex_dir = project_dir / ".codex"
        project_codex_dir.mkdir(parents=True)
        config_path = project_codex_dir / "config.toml"
        config_path.write_text("[features]\ncodex_hooks = true\n")
        source_dir = make_minimal_source(tmp_path)
        converted_dir = make_converted_output(tmp_path)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="codex 1.2.3")
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

        config = tomllib.loads(config_path.read_text())
        features = config.get("features", {})
        assert features.get("hooks") is True
        assert "codex_hooks" not in features

    def test_project_install_returns_instructions(self, tmp_path):
        """Project install returns post-install instructions string."""
        from samsara_cli.installer.install import Installer

        project_dir = tmp_path / "project"
        project_dir.mkdir()
        source_dir = make_minimal_source(tmp_path)
        converted_dir = make_converted_output(tmp_path)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="codex 1.2.3")
            with patch(
                "samsara_cli.installer.install.Installer._run_convert",
                return_value=converted_dir,
            ):
                installer = Installer(platform="codex")
                instructions = installer.install(
                    source_dir=source_dir,
                    scope="project",
                    cwd=project_dir,
                )

        assert instructions is not None
        assert isinstance(instructions, str)
        assert len(instructions) > 0

    def test_project_install_instructions_mention_feature_flags(self, tmp_path):
        """Project install instructions must mention feature flags for manual setup."""
        from samsara_cli.installer.install import Installer

        project_dir = tmp_path / "project"
        project_dir.mkdir()
        source_dir = make_minimal_source(tmp_path)
        converted_dir = make_converted_output(tmp_path)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="codex 1.2.3")
            with patch(
                "samsara_cli.installer.install.Installer._run_convert",
                return_value=converted_dir,
            ):
                installer = Installer(platform="codex")
                instructions = installer.install(
                    source_dir=source_dir,
                    scope="project",
                    cwd=project_dir,
                )

        assert "hooks = true" in instructions.lower()


# ---------------------------------------------------------------------------
# Global scope install
# ---------------------------------------------------------------------------


class TestInstallerGlobalScope:
    """Global scope install: native file copy + config.toml modifications."""

    def test_global_install_creates_native_dirs(self, tmp_path):
        """Global install creates native ~/.agents and ~/.codex structures."""
        from samsara_cli.installer.install import Installer

        fake_home = tmp_path / "home"
        fake_home.mkdir()
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

        assert (fake_home / ".agents" / "skills" / "samsara-research").is_dir()
        assert (fake_home / ".codex" / "agents").is_dir()

    def test_global_install_modifies_config_toml(self, tmp_path):
        """Global install adds feature flags to config.toml."""
        from samsara_cli.installer.install import Installer

        fake_home = tmp_path / "home"
        codex_dir = fake_home / ".codex"
        codex_dir.mkdir(parents=True)
        config_path = codex_dir / "config.toml"
        config_path.write_text("# Codex config\n")

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

        content = config_path.read_text()
        assert "hooks = true" in content
        assert "codex_hooks" not in content

    def test_global_install_config_toml_is_valid_toml(self, tmp_path):
        """Global install must produce valid TOML in config.toml."""
        from samsara_cli.installer.install import Installer

        fake_home = tmp_path / "home"
        codex_dir = fake_home / ".codex"
        codex_dir.mkdir(parents=True)
        config_path = codex_dir / "config.toml"
        config_path.write_text("")

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

        content = config_path.read_bytes()
        try:
            tomllib.loads(content.decode())
        except tomllib.TOMLDecodeError as e:
            pytest.fail(f"config.toml after global install is not valid TOML: {e}")

    def test_global_install_returns_instructions(self, tmp_path):
        """Global install returns post-install instructions."""
        from samsara_cli.installer.install import Installer

        fake_home = tmp_path / "home"
        codex_dir = fake_home / ".codex"
        codex_dir.mkdir(parents=True)

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
                    instructions = installer.install(
                        source_dir=source_dir,
                        scope="global",
                        cwd=project_dir,
                    )

        assert instructions is not None
        assert isinstance(instructions, str)
        assert "restart" in instructions.lower() or "codex" in instructions.lower()


def _write_realistic_codex_hooks_json(converted_dir: Path) -> str:
    """Overwrite the converted hooks.json with a realistic session-start command.

    The real converter bakes a scope-agnostic RELATIVE command
    ('.codex/hooks/samsara-session-start.sh'). The make_converted_output helper
    writes an empty SessionStart list, so it cannot exercise command-path rewriting.
    """
    relative_command = ".codex/hooks/samsara-session-start.sh"
    (converted_dir / ".codex" / "hooks.json").write_text(
        json.dumps(
            {
                "hooks": {
                    "SessionStart": [
                        {
                            "matcher": "startup|resume",
                            "hooks": [
                                {
                                    "type": "command",
                                    "command": relative_command,
                                    "statusMessage": "Injecting Samsara bootstrap context",
                                }
                            ],
                        }
                    ]
                }
            }
        )
    )
    return relative_command


def _session_start_commands(hooks_json_path: Path) -> list[str]:
    data = json.loads(hooks_json_path.read_text(encoding="utf-8"))
    return [
        hook["command"]
        for entry in data["hooks"]["SessionStart"]
        for hook in entry["hooks"]
    ]


class TestInstallerGlobalHookCommandPath:
    """Global install must make samsara hook commands resolvable from any cwd.

    Codex/Gemini launched from a project dir resolve a relative hook command
    against the PROJECT root. A global install places the script under $HOME, so
    a relative command silently never resolves and the hook never fires.
    """

    def test_global_install_hook_command_is_absolute_and_exists(self, tmp_path):
        """DEATH TEST: global hook command must be absolute and point to a real file.

        Fails on pre-fix code because the command stays
        '.codex/hooks/samsara-session-start.sh' (relative), which does not exist
        relative to the process cwd and is not resolvable to the global script.
        """
        from samsara_cli.installer.install import Installer

        fake_home = tmp_path / "home"
        fake_home.mkdir()
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        source_dir = make_minimal_source(tmp_path)
        converted_dir = make_converted_output(tmp_path)
        _write_realistic_codex_hooks_json(converted_dir)

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

        commands = _session_start_commands(fake_home / ".codex" / "hooks.json")
        assert commands, "global hooks.json has no SessionStart command"
        for command in commands:
            assert Path(command).is_absolute(), (
                f"Global hook command {command!r} is not absolute — Codex would "
                "resolve it against the project cwd, not $HOME, and never find it."
            )
            assert Path(command).exists(), (
                f"Global hook command {command!r} does not point to an existing "
                "script — the hook would silently never fire."
            )
            assert str(fake_home) in command, (
                f"Global hook command {command!r} must resolve under the install "
                f"root {fake_home}."
            )

    def test_project_install_hook_command_stays_relative(self, tmp_path):
        """Project scope must NOT rewrite the command — relative resolves correctly there."""
        from samsara_cli.installer.install import Installer

        project_dir = tmp_path / "project"
        project_dir.mkdir()
        source_dir = make_minimal_source(tmp_path)
        converted_dir = make_converted_output(tmp_path)
        relative_command = _write_realistic_codex_hooks_json(converted_dir)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="codex 1.2.3")
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

        commands = _session_start_commands(project_dir / ".codex" / "hooks.json")
        assert relative_command in commands, (
            "Project install must keep the relative command — it resolves against "
            "the project root where the script actually lives."
        )

    def test_global_install_leaves_foreign_hook_commands_untouched(self, tmp_path):
        """A user's pre-existing non-samsara hook command must not be rewritten."""
        from samsara_cli.installer.install import Installer

        fake_home = tmp_path / "home"
        codex_dir = fake_home / ".codex"
        codex_dir.mkdir(parents=True)
        # Pre-existing user hooks.json with a foreign command
        (codex_dir / "hooks.json").write_text(
            json.dumps(
                {
                    "hooks": {
                        "SessionStart": [
                            {
                                "matcher": "startup",
                                "hooks": [
                                    {"type": "command", "command": "my-own-tool.sh"}
                                ],
                            }
                        ]
                    }
                }
            )
        )

        project_dir = tmp_path / "project"
        project_dir.mkdir()
        source_dir = make_minimal_source(tmp_path)
        converted_dir = make_converted_output(tmp_path)
        _write_realistic_codex_hooks_json(converted_dir)

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

        commands = _session_start_commands(fake_home / ".codex" / "hooks.json")
        assert "my-own-tool.sh" in commands, (
            "User's own relative hook command must be left untouched — only samsara's "
            "plugin-dir-prefixed commands get rewritten."
        )


def make_gemini_converted_output(tmp_path: Path) -> Path:
    """Create a minimal converted output directory for the gemini-cli platform.

    Mirrors the real converter's .gemini tree, including the hook script itself,
    so a global install can assert the rewritten command points to an existing
    file. Gemini differs from Codex in one way that matters here: its hooks_file
    (settings.json) is ALSO the global config_path, so the rewrite must be the
    final write to that file — this fixture lets a test prove that end to end.
    """
    output = tmp_path / "dist" / "gemini"
    skill_dir = output / ".agents" / "skills" / "samsara-research"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# research\n")
    agents_dir = output / ".gemini" / "agents"
    agents_dir.mkdir(parents=True)
    (agents_dir / "samsara-implementer.md").write_text("# implementer\n")
    hooks_dir = output / ".gemini" / "hooks"
    hooks_dir.mkdir(parents=True)
    (hooks_dir / "samsara-session-start.sh").write_text("#!/usr/bin/env bash\n")
    return output


def _write_realistic_gemini_settings_json(converted_dir: Path) -> str:
    """Write a converted settings.json with a realistic RELATIVE hook command.

    The real converter bakes '.gemini/hooks/samsara-session-start.sh' — scope
    agnostic and relative, identical in shape to the Codex case but nested in
    settings.json instead of hooks.json.
    """
    relative_command = ".gemini/hooks/samsara-session-start.sh"
    (converted_dir / ".gemini" / "settings.json").write_text(
        json.dumps(
            {
                "hooks": {
                    "SessionStart": [
                        {
                            "matcher": "startup|resume",
                            "hooks": [
                                {
                                    "type": "command",
                                    "command": relative_command,
                                }
                            ],
                        }
                    ]
                }
            }
        )
    )
    return relative_command


class TestInstallerGeminiGlobalHookCommandPath:
    """Same false-success failure mode as Codex, guarded for the gemini-cli path.

    The commit that fixed the Codex relative-command bug claimed the structure-
    agnostic rewrite also covers Gemini's settings.json — but only Codex was
    tested. These tests turn that claim into a guarded fact. Gemini is the
    riskier surface because settings.json doubles as the global config file, so
    the rewrite must survive the settings-merge that runs before it.
    """

    def test_global_install_hook_command_is_absolute_and_exists(self, tmp_path):
        """DEATH TEST: gemini global hook command must be absolute and point to a real file.

        Fails on pre-fix code because the command stays
        '.gemini/hooks/samsara-session-start.sh' (relative), which Gemini would
        resolve against the project cwd rather than $HOME — the hook never fires.
        """
        from samsara_cli.installer.install import Installer

        fake_home = tmp_path / "home"
        fake_home.mkdir()
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        source_dir = make_minimal_source(tmp_path)
        converted_dir = make_gemini_converted_output(tmp_path)
        _write_realistic_gemini_settings_json(converted_dir)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="gemini 1.2.3")
            with patch.dict("os.environ", {"HOME": str(fake_home)}):
                with patch(
                    "samsara_cli.installer.install.Installer._run_convert",
                    return_value=converted_dir,
                ):
                    installer = Installer(platform="gemini-cli")
                    installer.install(
                        source_dir=source_dir,
                        scope="global",
                        cwd=project_dir,
                    )

        commands = _session_start_commands(fake_home / ".gemini" / "settings.json")
        assert commands, "global settings.json has no SessionStart command"
        for command in commands:
            assert Path(command).is_absolute(), (
                f"Global hook command {command!r} is not absolute — Gemini would "
                "resolve it against the project cwd, not $HOME, and never find it."
            )
            assert Path(command).exists(), (
                f"Global hook command {command!r} does not point to an existing "
                "script — the hook would silently never fire."
            )
            assert str(fake_home) in command, (
                f"Global hook command {command!r} must resolve under the install "
                f"root {fake_home}."
            )

    def test_global_install_leaves_foreign_hook_commands_untouched(self, tmp_path):
        """A user's pre-existing non-samsara command in settings.json must survive.

        settings.json carries user config beyond hooks, so over-broad rewriting
        here is more dangerous than for Codex — this pins the prefix guard.
        """
        from samsara_cli.installer.install import Installer

        fake_home = tmp_path / "home"
        gemini_dir = fake_home / ".gemini"
        gemini_dir.mkdir(parents=True)
        # Pre-existing user settings.json with a foreign hook command.
        (gemini_dir / "settings.json").write_text(
            json.dumps(
                {
                    "hooks": {
                        "SessionStart": [
                            {
                                "matcher": "startup",
                                "hooks": [
                                    {"type": "command", "command": "my-own-tool.sh"}
                                ],
                            }
                        ]
                    }
                }
            )
        )

        project_dir = tmp_path / "project"
        project_dir.mkdir()
        source_dir = make_minimal_source(tmp_path)
        converted_dir = make_gemini_converted_output(tmp_path)
        _write_realistic_gemini_settings_json(converted_dir)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="gemini 1.2.3")
            with patch.dict("os.environ", {"HOME": str(fake_home)}):
                with patch(
                    "samsara_cli.installer.install.Installer._run_convert",
                    return_value=converted_dir,
                ):
                    installer = Installer(platform="gemini-cli")
                    installer.install(
                        source_dir=source_dir,
                        scope="global",
                        cwd=project_dir,
                    )

        commands = _session_start_commands(fake_home / ".gemini" / "settings.json")
        assert "my-own-tool.sh" in commands, (
            "User's own relative hook command must be left untouched — only samsara's "
            "plugin-dir-prefixed commands get rewritten."
        )


# ---------------------------------------------------------------------------
# Update = re-convert + re-install
# ---------------------------------------------------------------------------


class TestInstallerUpdate:
    """Update: idempotent re-convert + re-install."""

    def test_update_project_scope_is_idempotent(self, tmp_path):
        """update() project scope produces same result as install()."""
        from samsara_cli.installer.install import Installer

        project_dir = tmp_path / "project"
        project_dir.mkdir()
        source_dir = make_minimal_source(tmp_path)
        converted_dir = make_converted_output(tmp_path)

        def run_update():
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0, stdout="codex 1.2.3")
                with patch(
                    "samsara_cli.installer.install.Installer._run_convert",
                    return_value=converted_dir,
                ):
                    installer = Installer(platform="codex")
                    installer.update(
                        source_dir=source_dir,
                        scope="project",
                        cwd=project_dir,
                    )

        run_update()
        target_after_first = list((project_dir / ".agents").rglob("*")) + list(
            (project_dir / ".codex").rglob("*")
        )
        run_update()
        target_after_second = list((project_dir / ".agents").rglob("*")) + list(
            (project_dir / ".codex").rglob("*")
        )

        assert len(target_after_first) == len(target_after_second), (
            "update() must be idempotent — same files after each run"
        )

    def test_update_calls_convert_then_install(self, tmp_path):
        """update() must run both convert and install."""
        from samsara_cli.installer.install import Installer

        project_dir = tmp_path / "project"
        project_dir.mkdir()
        source_dir = make_minimal_source(tmp_path)
        converted_dir = make_converted_output(tmp_path)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="codex 1.2.3")
            with patch(
                "samsara_cli.installer.install.Installer._run_convert",
                return_value=converted_dir,
            ) as mock_convert:
                installer = Installer(platform="codex")
                installer.update(
                    source_dir=source_dir,
                    scope="project",
                    cwd=project_dir,
                )
                assert mock_convert.called, "update() must call convert"


# ---------------------------------------------------------------------------
# _run_convert integration (source validation before converter)
# ---------------------------------------------------------------------------


class TestInstallerRunConvert:
    """Source validation happens before converter runs."""

    def test_run_convert_with_valid_source_returns_path(self, tmp_path):
        """_run_convert returns Path to converted output."""
        from samsara_cli.installer.install import Installer

        source_dir = make_minimal_source(tmp_path)
        output_dir = tmp_path / "output"

        # We need a real engine call here, so mock the engine
        with patch("samsara_cli.installer.install.ConversionEngine") as MockEngine:
            mock_engine = MagicMock()
            MockEngine.return_value = mock_engine
            mock_engine.run.return_value = None

            installer = Installer(platform="codex")
            result = installer._run_convert(
                source_dir=source_dir,
                output_dir=output_dir,
            )
            assert result == output_dir

    def test_run_convert_with_bad_source_raises(self, tmp_path):
        """_run_convert raises when source is not valid samsara structure."""
        from samsara_cli.installer.install import Installer, InstallerError

        bad_source = tmp_path / "not-samsara"
        bad_source.mkdir()
        output_dir = tmp_path / "output"

        installer = Installer(platform="codex")
        with pytest.raises((InstallerError, Exception)):
            installer._run_convert(
                source_dir=bad_source,
                output_dir=output_dir,
            )
