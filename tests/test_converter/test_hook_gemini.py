"""
Gemini hook conversion tests.

Gemini hooks are configured in settings.json and hook scripts must speak JSON
stdin/stdout. Plain text on stdout silently breaks hook execution.
"""

import json
import subprocess
from pathlib import Path

from samsara_cli.config.loader import load_platform_config
from samsara_cli.config.template_env import get_template_env
from samsara_cli.converter.hook import HookConverter


def _render_gemini_hook_script() -> str:
    config = load_platform_config("gemini-cli")
    template = get_template_env("gemini-cli").get_template("hook.sh.j2")
    return HookConverter().convert_script(
        hook_name="session-start",
        event="session_start",
        platform_config=config,
        template=template,
    )


def _run_hook(script_path: Path, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(script_path)],
        input=json.dumps({"hookEventName": "SessionStart"}),
        capture_output=True,
        text=True,
        cwd=cwd,
        timeout=10,
        check=False,
    )


class TestGeminiHookScript:
    def test_hook_stdout_is_valid_json_only_when_bootstrap_exists(self, tmp_path: Path):
        skill_dir = tmp_path / ".gemini" / "skills" / "samsara-samsara-bootstrap"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Bootstrap\n\nUse samsara.\n")
        script_path = tmp_path / "samsara-session-start.sh"
        script_path.write_text(_render_gemini_hook_script())

        result = _run_hook(script_path, tmp_path)

        assert result.returncode == 0
        payload = json.loads(result.stdout)
        assert result.stdout.strip().startswith("{")
        assert result.stdout.strip().endswith("}")
        assert payload["hookSpecificOutput"]["additionalContext"]
        assert "Bootstrap" in payload["hookSpecificOutput"]["additionalContext"]

    def test_hook_uses_additional_context_not_system_message_only(self, tmp_path: Path):
        skill_dir = tmp_path / ".gemini" / "skills" / "samsara-samsara-bootstrap"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Bootstrap\n")
        script_path = tmp_path / "samsara-session-start.sh"
        script_path.write_text(_render_gemini_hook_script())

        result = _run_hook(script_path, tmp_path)
        payload = json.loads(result.stdout)

        assert "hookSpecificOutput" in payload
        assert "additionalContext" in payload["hookSpecificOutput"]
        assert payload.get("systemMessage") is None

    def test_hook_missing_bootstrap_outputs_degraded_valid_json(self, tmp_path: Path):
        script_path = tmp_path / "samsara-session-start.sh"
        script_path.write_text(_render_gemini_hook_script())

        result = _run_hook(script_path, tmp_path)

        assert result.returncode == 0
        payload = json.loads(result.stdout)
        context = payload["hookSpecificOutput"]["additionalContext"]
        assert "degraded" in context.lower()
        assert "not found" in context.lower()
        assert "No such file" not in result.stdout


class TestGeminiSettingsRendering:
    def test_settings_json_contains_session_start_hook(self):
        config = load_platform_config("gemini-cli")
        template = get_template_env("gemini-cli").get_template("settings.json.j2")

        settings = HookConverter().convert_hooks_json(
            platform_config=config,
            template=template,
        )

        assert "hooks" in settings
        assert "SessionStart" in settings["hooks"]
        entry = settings["hooks"]["SessionStart"][0]
        assert entry["hooks"][0]["command"] == ".gemini/hooks/samsara-session-start.sh"
