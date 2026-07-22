from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from samsara_cli.installer.install import Installer, InstallerError


def _converted(root: Path, *, skill_name: str) -> Path:
    output = root / f"converted-{skill_name}"
    skill = output / ".agents/skills" / skill_name
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text(
        f"---\nname: {skill_name.removeprefix('samsara-')}\ndescription: test\n---\n"
    )
    codex = output / ".codex"
    (codex / "agents").mkdir(parents=True)
    (codex / "hooks").mkdir(parents=True)
    (codex / "config.toml").write_text("[features]\nhooks = true\n")
    (codex / "hooks.json").write_text('{"hooks": {}}\n')
    return output


def _install(installer: Installer, converted: Path, project: Path) -> str:
    with patch.object(installer._detector, "detect", return_value=True):
        return installer.install(
            source_dir=project,
            scope="project",
            cwd=project,
            converted_source_dir=converted,
        )


def test_project_install_writes_samsara_owned_manifest(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    converted = _converted(tmp_path, skill_name="samsara-research")

    _install(Installer("codex"), converted, project)

    manifest_path = project / ".samsara/install-manifest.codex.json"
    manifest = json.loads(manifest_path.read_text())
    assert manifest["platform"] == "codex"
    assert manifest["scope"] == "project"
    assert ".agents/skills/samsara-research/SKILL.md" in manifest["owned_paths"]
    assert ".codex/config.toml" not in manifest["owned_paths"]
    assert ".codex/hooks.json" not in manifest["owned_paths"]


def test_update_prunes_only_paths_owned_by_previous_manifest(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    installer = Installer("codex")
    first = _converted(tmp_path, skill_name="samsara-research")
    second = _converted(tmp_path, skill_name="samsara-planning")

    _install(installer, first, project)
    foreign = project / ".agents/skills/user-owned/SKILL.md"
    foreign.parent.mkdir(parents=True)
    foreign.write_text("user")
    _install(installer, second, project)

    assert not (project / ".agents/skills/samsara-research/SKILL.md").exists()
    assert (project / ".agents/skills/samsara-planning/SKILL.md").exists()
    assert foreign.read_text() == "user"


def test_project_install_rewrites_owned_hook_commands_to_absolute_paths(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    project.mkdir()
    converted = _converted(tmp_path, skill_name="samsara-research")
    hook = converted / ".codex/hooks/samsara-session-start.sh"
    hook.write_text("#!/usr/bin/env bash\nexit 0\n")
    hook.chmod(0o755)
    (converted / ".codex/hooks.json").write_text(
        json.dumps(
            {
                "hooks": {
                    "SessionStart": [
                        {
                            "matcher": "startup",
                            "hooks": [
                                {
                                    "type": "command",
                                    "command": ".codex/hooks/samsara-session-start.sh",
                                }
                            ],
                        }
                    ]
                }
            }
        )
    )

    _install(Installer("codex"), converted, project)

    installed = json.loads((project / ".codex/hooks.json").read_text())
    command = installed["hooks"]["SessionStart"][0]["hooks"][0]["command"]
    assert command == str(project / ".codex/hooks/samsara-session-start.sh")


def test_corrupt_manifest_blocks_update_before_installing_files(tmp_path: Path) -> None:
    project = tmp_path / "project"
    manifest = project / ".samsara/install-manifest.codex.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_text("not-json")
    converted = _converted(tmp_path, skill_name="samsara-research")

    with pytest.raises(InstallerError, match="ownership manifest"):
        _install(Installer("codex"), converted, project)

    assert not (project / ".agents/skills/samsara-research/SKILL.md").exists()


def test_project_install_discloses_existing_global_scope(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    home = tmp_path / "home"
    global_manifest = home / ".samsara/install-manifest.codex.json"
    global_manifest.parent.mkdir(parents=True)
    global_manifest.write_text("{}")
    converted = _converted(tmp_path, skill_name="samsara-research")

    with patch.dict("os.environ", {"HOME": str(home)}):
        instructions = _install(Installer("codex"), converted, project)

    assert "global Samsara install also exists" in instructions
    assert str(global_manifest) in instructions


def test_project_install_resolves_auto_gatekeeper_companion_path(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project with spaces"
    project.mkdir()
    converted = _converted(tmp_path, skill_name="samsara-research")
    agent = converted / ".codex/agents/samsara-auto-gatekeeper.toml"
    agent.write_text(
        'name = "samsara-auto-gatekeeper"\n'
        'description = "gatekeeper"\n'
        'developer_instructions = """Run '
        "<installed-auto-gatekeeper-companion-directory>/scripts/"
        'validate_auto_decisions.py."""\n'
    )
    companion = (
        converted / ".codex/agent-resources/samsara-auto-gatekeeper/scripts/"
        "validate_auto_decisions.py"
    )
    companion.parent.mkdir(parents=True)
    companion.write_text("print('ok')\n")

    _install(Installer("codex"), converted, project)

    installed = (project / ".codex/agents/samsara-auto-gatekeeper.toml").read_text()
    assert "<installed-auto-gatekeeper-companion-directory>" not in installed
    expected = project / ".codex/agent-resources/samsara-auto-gatekeeper"
    assert f"'{expected}'/scripts/validate_auto_decisions.py" in installed


def test_project_install_resolves_skill_companion_path(tmp_path: Path) -> None:
    project = tmp_path / "project with spaces"
    project.mkdir()
    converted = _converted(tmp_path, skill_name="samsara-research")
    skill = converted / ".agents/skills/samsara-research/SKILL.md"
    skill.write_text(
        "---\n"
        "name: research\n"
        "description: test\n"
        "---\n\n"
        "Run `samsara-cli run-companion "
        "<installed-research-skill-directory>/scripts/check.py`.\n"
    )
    companion = converted / ".agents/skills/samsara-research/scripts/check.py"
    companion.parent.mkdir(parents=True)
    companion.write_text("print('ok')\n")

    _install(Installer("codex"), converted, project)

    installed = (project / ".agents/skills/samsara-research/SKILL.md").read_text()
    assert "<installed-research-skill-directory>" not in installed
    expected = project / ".agents/skills/samsara-research"
    assert f"'{expected}'/scripts/check.py" in installed
