"""Codex runtime-contract tests for the live Samsara conversion.

These tests validate resolvable identities and executable seams. They do not
assert prose layout or wording.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import tomllib
from pathlib import Path
from unittest.mock import patch

import yaml

from samsara_cli.converter.engine import ConversionEngine
from samsara_cli.installer.install import Installer


REPO_ROOT = Path(__file__).resolve().parents[2]
_SKILL_REF_RE = re.compile(r"\$([a-z][a-z0-9-]*)")


def _convert_live(tmp_path: Path) -> Path:
    output = tmp_path / "codex"
    ConversionEngine("codex").run(REPO_ROOT, output)
    return output


def test_death__every_internal_skill_ref_resolves_to_frontmatter_name(
    tmp_path: Path,
) -> None:
    output = _convert_live(tmp_path)
    skill_root = output / ".agents" / "skills"
    known: set[str] = set()
    for skill_md in skill_root.glob("*/SKILL.md"):
        frontmatter = yaml.safe_load(skill_md.read_text().split("---", 2)[1])
        known.add(frontmatter["name"])

    refs: set[str] = set()
    for path in output.rglob("*"):
        if not path.is_file() or path.suffix not in {".md", ".toml"}:
            continue
        refs.update(_SKILL_REF_RE.findall(path.read_text(encoding="utf-8")))

    refs.discard("skill-name")
    assert refs <= known, f"Unresolved Codex skill IDs: {sorted(refs - known)}"


def test_death__auto_gatekeeper_companion_is_shipped(tmp_path: Path) -> None:
    output = _convert_live(tmp_path)
    companion = (
        output
        / ".codex"
        / "agent-resources"
        / "samsara-auto-gatekeeper"
        / "scripts"
        / "validate_auto_decisions.py"
    )
    assert companion.is_file()
    gatekeeper = tomllib.loads(
        (output / ".codex/agents/samsara-auto-gatekeeper.toml").read_text()
    )
    assert "validate_auto_decisions.py" in gatekeeper["developer_instructions"]


def test_death__codex_session_start_hooks_are_model_context_producers(
    tmp_path: Path,
) -> None:
    output = _convert_live(tmp_path)
    hooks_path = output / ".codex/hooks.json"
    hooks = json.loads(hooks_path.read_text())["hooks"]["SessionStart"]
    assert set(hooks[0]["matcher"].split("|")) == {
        "startup",
        "resume",
        "clear",
        "compact",
    }

    commands = [hook["command"] for hook in hooks[0]["hooks"]]
    assert len(commands) == 2
    assert any("samsara-session-start.sh" in command for command in commands)
    assert any("check-codebase-map.sh" in command for command in commands)

    for command in commands:
        script = output / command
        result = subprocess.run(
            [str(script)],
            input=json.dumps({"cwd": str(output), "hook_event_name": "SessionStart"}),
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr
        payload = json.loads(result.stdout)
        assert "systemMessage" not in payload
        hook_output = payload["hookSpecificOutput"]
        assert hook_output["hookEventName"] == "SessionStart"
        assert hook_output["additionalContext"]


def test_death__agent_authority_metadata_survives_conversion(tmp_path: Path) -> None:
    output = _convert_live(tmp_path)
    agents = output / ".codex/agents"

    reviewer = tomllib.loads((agents / "samsara-code-reviewer.toml").read_text())
    assert reviewer["description"].startswith("Yin-side code review agent")
    assert reviewer["sandbox_mode"] == "read-only"
    assert reviewer["model_reasoning_effort"] == "high"

    gatekeeper = tomllib.loads((agents / "samsara-auto-gatekeeper.toml").read_text())
    assert gatekeeper["description"].startswith(
        "Staff-level workflow decision authority"
    )
    assert gatekeeper["sandbox_mode"] == "workspace-write"
    assert gatekeeper["model_reasoning_effort"] == "high"

    explorer = tomllib.loads((agents / "samsara-structure-explorer.toml").read_text())
    assert explorer["sandbox_mode"] == "read-only"
    assert "model" not in explorer

    for agent_file in agents.glob("*.toml"):
        assert str(REPO_ROOT) not in agent_file.read_text()


def test_converted_hook_commands_are_scope_agnostic_relative_paths(
    tmp_path: Path,
) -> None:
    output = _convert_live(tmp_path)
    # The installer owns scope-specific absolute-path rewriting.
    hooks = json.loads((output / ".codex/hooks.json").read_text())
    for entry in hooks["hooks"]["SessionStart"]:
        for hook in entry["hooks"]:
            assert not os.path.isabs(hook["command"])


def test_death__live_conversion_installs_without_unresolved_companions(
    tmp_path: Path,
) -> None:
    converted = _convert_live(tmp_path)
    project = tmp_path / "installed project with spaces"
    project.mkdir()
    installer = Installer("codex")

    with patch.object(installer._detector, "detect", return_value=True):
        installer.install(
            source_dir=REPO_ROOT,
            converted_source_dir=converted,
            scope="project",
            cwd=project,
        )

    for path in project.rglob("*"):
        if not path.is_file() or path.suffix not in {".md", ".toml", ".txt"}:
            continue
        assert "<installed-" not in path.read_text(encoding="utf-8")

    manifest = json.loads(
        (project / ".samsara/install-manifest.codex.json").read_text()
    )
    companion = (
        ".codex/agent-resources/samsara-auto-gatekeeper/scripts/"
        "validate_auto_decisions.py"
    )
    assert companion in manifest["owned_paths"]
