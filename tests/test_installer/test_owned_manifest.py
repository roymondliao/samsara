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


def _runtime_command(root: Path, *, exit_code: int = 0) -> Path:
    runtime = root / "bin" / "samsara-cli"
    runtime.parent.mkdir(parents=True, exist_ok=True)
    runtime.write_text(f"#!/bin/sh\nexit {exit_code}\n")
    runtime.chmod(0o755)
    return runtime


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


def test_global_install_rejects_source_venv_runtime_before_writing(
    tmp_path: Path,
) -> None:
    source = tmp_path / "samsara-source"
    source.mkdir()
    runtime = _runtime_command(source / ".venv")
    converted = _converted(tmp_path, skill_name="samsara-research")
    home = tmp_path / "home"
    home.mkdir()
    installer = Installer("codex", runtime_command=runtime)

    with (
        patch.object(installer._detector, "detect", return_value=True),
        patch.dict("os.environ", {"HOME": str(home)}),
        pytest.raises(InstallerError, match="uv tool install"),
    ):
        installer.install(
            source_dir=source,
            scope="global",
            cwd=tmp_path,
            converted_source_dir=converted,
        )

    assert not (home / ".codex").exists()
    assert not (home / ".samsara").exists()


def test_schema_one_manifest_migrates_and_materializes_runtime_command(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    source.mkdir()
    project = tmp_path / "project with spaces"
    project.mkdir()
    runtime = _runtime_command(tmp_path / "durable runtime")
    converted = _converted(tmp_path, skill_name="samsara-research")
    skill = converted / ".agents/skills/samsara-research/SKILL.md"
    skill.write_text(
        "---\nname: research\ndescription: test\n---\n\n"
        "Run `samsara-cli run-companion "
        "<installed-research-skill-directory>/scripts/check.py`.\n"
    )
    script = converted / ".agents/skills/samsara-research/scripts/check.py"
    script.parent.mkdir(parents=True)
    script.write_text("print('ok')\n")
    manifest_path = project / ".samsara/install-manifest.codex.json"
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "platform": "codex",
                "scope": "project",
                "samsara_version": "1.0.0",
                "owned_paths": [],
                "hook_commands": [],
                "shared_paths": [".codex/config.toml", ".codex/hooks.json"],
            }
        )
    )
    installer = Installer("codex", runtime_command=runtime)

    with patch.object(installer._detector, "detect", return_value=True):
        installer.install(
            source_dir=source,
            scope="project",
            cwd=project,
            converted_source_dir=converted,
        )

    manifest = json.loads(manifest_path.read_text())
    assert manifest["schema_version"] == 2
    assert manifest["runtime"]["command"] == str(runtime.resolve())
    installed = (project / ".agents/skills/samsara-research/SKILL.md").read_text()
    assert f"'{runtime.resolve()}' run-companion" in installed


def test_companion_smoke_failure_leaves_target_untouched(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    project = tmp_path / "project"
    project.mkdir()
    runtime = _runtime_command(tmp_path / "broken runtime", exit_code=7)
    converted = _converted(tmp_path, skill_name="samsara-research")
    script = converted / ".agents/skills/samsara-research/scripts/check.py"
    script.parent.mkdir(parents=True)
    script.write_text("print('ok')\n")
    installer = Installer("codex", runtime_command=runtime)

    with (
        patch.object(installer._detector, "detect", return_value=True),
        pytest.raises(InstallerError, match="[Cc]ompanion smoke check"),
    ):
        installer.install(
            source_dir=source,
            scope="project",
            cwd=project,
            converted_source_dir=converted,
        )

    assert list(project.iterdir()) == []


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
