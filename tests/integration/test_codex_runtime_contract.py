"""Codex runtime-contract tests for the live Samsara conversion.

These tests validate resolvable identities and executable seams. They do not
assert prose layout or wording.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tomllib
from pathlib import Path
from unittest.mock import patch

import yaml

from samsara_cli.converter.engine import ConversionEngine
from samsara_cli.installer.install import Installer


REPO_ROOT = Path(__file__).resolve().parents[2]
_SKILL_REF_RE = re.compile(r"\$([a-z][a-z0-9-]*)")


def _durable_test_runtime(root: Path) -> Path:
    runtime = root / "tool-bin" / "samsara-cli"
    runtime.parent.mkdir(parents=True)
    runtime.write_text(
        f"#!{sys.executable}\n"
        "import subprocess\n"
        "import sys\n"
        "import runpy\n"
        "if len(sys.argv) >= 3 and sys.argv[1] == 'run-companion':\n"
        "    result = subprocess.run([sys.executable, *sys.argv[2:]], check=False)\n"
        "    raise SystemExit(result.returncode)\n"
        "if len(sys.argv) == 3 and sys.argv[1] == 'check-companion':\n"
        "    runpy.run_path(sys.argv[2], run_name='__samsara_companion_check__')\n"
        "    raise SystemExit(0)\n"
        "if len(sys.argv) == 2 and sys.argv[1] == 'version':\n"
        "    print('samsara-cli test-runtime')\n"
        "    raise SystemExit(0)\n"
        "raise SystemExit(2)\n"
    )
    runtime.chmod(0o755)
    return runtime


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


def test_death__converted_companion_commands_forbid_runtime_fallback(
    tmp_path: Path,
) -> None:
    output = _convert_live(tmp_path)
    consumers = []
    for path in output.rglob("*"):
        if not path.is_file() or path.suffix not in {".md", ".toml", ".txt"}:
            continue
        content = path.read_text(encoding="utf-8")
        if "samsara-cli run-companion" not in content:
            continue
        consumers.append(path)
        assert "CANNOT VALIDATE" in content
        assert "python3" in content
        assert "uv" in content

    assert consumers, "Live Codex conversion must contain companion consumers"


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


def test_death__global_companion_runs_from_foreign_cwd_with_clean_path(
    tmp_path: Path,
) -> None:
    converted = _convert_live(tmp_path)
    runtime = _durable_test_runtime(tmp_path / "runtime outside source")
    home = tmp_path / "isolated home"
    home.mkdir()
    foreign_cwd = tmp_path / "foreign project"
    foreign_cwd.mkdir()
    installer = Installer("codex", runtime_command=runtime)

    with (
        patch.object(installer._detector, "detect", return_value=True),
        patch.dict(
            os.environ,
            {"HOME": str(home), "PATH": "/usr/bin:/bin"},
            clear=False,
        ),
    ):
        installer.install(
            source_dir=REPO_ROOT,
            converted_source_dir=converted,
            scope="global",
            cwd=foreign_cwd,
        )

    manifest = json.loads((home / ".samsara/install-manifest.codex.json").read_text())
    assert manifest["schema_version"] == 2
    assert manifest["runtime"]["command"] == str(runtime.resolve())
    installed_skill = (home / ".agents/skills/samsara-codebase-map/SKILL.md").read_text(
        encoding="utf-8"
    )
    assert str(runtime.resolve()) in installed_skill
    assert " run-companion" in installed_skill
    assert str(REPO_ROOT / ".venv") not in installed_skill
    validator = (
        home / ".agents/skills/samsara-codebase-map/scripts/validate_codebase_map.py"
    )
    result = subprocess.run(
        [manifest["runtime"]["command"], "run-companion", str(validator), "--help"],
        cwd=foreign_cwd,
        env={"HOME": str(home), "PATH": "/usr/bin:/bin"},
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "--candidate" in result.stdout
    assert "--expected-commit" in result.stdout


def test_documented_codex_install_uses_durable_runtime() -> None:
    for readme in (REPO_ROOT / "README.md", REPO_ROOT / "README.zh-TW.md"):
        content = readme.read_text(encoding="utf-8")
        assert "uv tool install --force /path/to/samsara" in content
        assert "samsara-cli install codex --scope global" in content
        assert "uv run samsara-cli install codex" not in content
