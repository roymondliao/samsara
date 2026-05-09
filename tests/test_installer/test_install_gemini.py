"""
Gemini installer tests.

Gemini uses settings.json for hooks, so install must merge JSON instead of
overwriting user/project settings.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


def make_source(tmp_path: Path) -> Path:
    source = tmp_path / "source"
    (source / ".claude-plugin").mkdir(parents=True)
    (source / ".claude-plugin" / "plugin.json").write_text(
        json.dumps({"name": "samsara", "version": "0.8.0"})
    )
    (source / "skills" / "research").mkdir(parents=True)
    (source / "skills" / "research" / "SKILL.md").write_text(
        "---\nname: research\ndescription: Research\n---\n\n# Research\n"
    )
    (source / "agents").mkdir()
    (source / "agents" / "implementer.md").write_text("# Implementer\n")
    (source / "hooks").mkdir()
    (source / "hooks" / "hooks.json").write_text("{}")
    (source / "references").mkdir()
    return source


def make_gemini_converted_output(tmp_path: Path) -> Path:
    output = tmp_path / "dist" / "gemini-cli"
    skill_dir = output / ".gemini" / "skills" / "samsara-research"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# Research\n")
    agents_dir = output / ".gemini" / "agents"
    agents_dir.mkdir(parents=True)
    (agents_dir / "samsara-implementer.md").write_text(
        "---\nname: samsara-implementer\ndescription: Implementer\n---\nBody\n"
    )
    hooks_dir = output / ".gemini" / "hooks"
    hooks_dir.mkdir(parents=True)
    (hooks_dir / "samsara-session-start.sh").write_text("#!/usr/bin/env bash\n")
    (output / ".gemini" / "settings.json").write_text(
        json.dumps(
            {
                "hooks": {
                    "SessionStart": [
                        {
                            "matcher": "startup",
                            "hooks": [
                                {
                                    "type": "command",
                                    "command": ".gemini/hooks/samsara-session-start.sh",
                                }
                            ],
                        }
                    ]
                }
            }
        )
    )
    return output


class TestGeminiProjectInstall:
    def test_project_install_merges_existing_settings(self, tmp_path: Path):
        from samsara_cli.installer.install import Installer

        project = tmp_path / "project"
        settings_dir = project / ".gemini"
        settings_dir.mkdir(parents=True)
        (settings_dir / "settings.json").write_text(
            json.dumps(
                {
                    "theme": "dark",
                    "hooks": {
                        "SessionStart": [
                            {
                                "matcher": "manual",
                                "hooks": [{"type": "command", "command": "custom"}],
                            }
                        ]
                    },
                }
            )
        )

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="gemini 1.0")
            Installer("gemini-cli").install(
                source_dir=make_source(tmp_path),
                scope="project",
                cwd=project,
                converted_source_dir=make_gemini_converted_output(tmp_path),
            )

        settings = json.loads((settings_dir / "settings.json").read_text())
        assert settings["theme"] == "dark"
        commands = [
            hook["command"]
            for entry in settings["hooks"]["SessionStart"]
            for hook in entry["hooks"]
        ]
        assert "custom" in commands
        assert ".gemini/hooks/samsara-session-start.sh" in commands

    def test_project_install_is_idempotent_for_settings(self, tmp_path: Path):
        from samsara_cli.installer.install import Installer

        project = tmp_path / "project"
        project.mkdir()
        source = make_source(tmp_path)
        converted = make_gemini_converted_output(tmp_path)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="gemini 1.0")
            installer = Installer("gemini-cli")
            installer.install(
                source, "project", cwd=project, converted_source_dir=converted
            )
            installer.install(
                source, "project", cwd=project, converted_source_dir=converted
            )

        settings = json.loads((project / ".gemini" / "settings.json").read_text())
        entries = settings["hooks"]["SessionStart"]
        samsara_entries = [
            entry
            for entry in entries
            if any(
                hook.get("command") == ".gemini/hooks/samsara-session-start.sh"
                for hook in entry.get("hooks", [])
            )
        ]
        assert len(samsara_entries) == 1

    def test_project_install_invalid_existing_settings_aborts(self, tmp_path: Path):
        from samsara_cli.installer.install import Installer, InstallerError

        project = tmp_path / "project"
        settings_dir = project / ".gemini"
        settings_dir.mkdir(parents=True)
        (settings_dir / "settings.json").write_text("{not json")

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="gemini 1.0")
            with pytest.raises(InstallerError):
                Installer("gemini-cli").install(
                    source_dir=make_source(tmp_path),
                    scope="project",
                    cwd=project,
                    converted_source_dir=make_gemini_converted_output(tmp_path),
                )

        assert (settings_dir / "settings.json").read_text() == "{not json"


class TestGeminiGlobalInstall:
    def test_global_install_backs_up_settings_and_uses_patched_home(
        self, tmp_path: Path
    ):
        from samsara_cli.installer.install import Installer

        fake_home = tmp_path / "home"
        settings_dir = fake_home / ".gemini"
        settings_dir.mkdir(parents=True)
        (settings_dir / "settings.json").write_text(json.dumps({"ui": "compact"}))

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="gemini 1.0")
            with patch.dict("os.environ", {"HOME": str(fake_home)}):
                Installer("gemini-cli").install(
                    source_dir=make_source(tmp_path),
                    scope="global",
                    cwd=tmp_path / "project",
                    converted_source_dir=make_gemini_converted_output(tmp_path),
                )

        assert (settings_dir / "settings.json.bak").exists()
        settings = json.loads((settings_dir / "settings.json").read_text())
        assert settings["ui"] == "compact"
        assert settings["hooks"]["SessionStart"]
