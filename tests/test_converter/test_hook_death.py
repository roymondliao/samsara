"""
Death tests for HookConverter.

These tests target SILENT FAILURE paths — cases where a wrong conversion
produces output that looks valid but is semantically broken, with no error raised.

Death case taxonomy:
  DC-1: Hook script outputs UI-only systemMessage instead of model-visible
        hookSpecificOutput.additionalContext.
  DC-2: hooks.json matchers drift from the platform lifecycle contract.
  DC-3: Hook script references Claude-only runtime env vars — these don't exist
        in Codex, causing a bash no-such-variable error (with set -u) or an empty
        path (without set -u), silently breaking native layout lookups.
  DC-4: Special characters in bootstrap content (quotes, newlines, backslashes) —
        naive string interpolation produces invalid JSON that Codex silently ignores.
"""

import json

import pytest

from samsara_cli.config.loader import load_platform_config
from samsara_cli.config.template_env import get_template_env
from samsara_cli.converter.hook import HookConverter


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def codex_config():
    """Load the codex platform config once per test."""
    return load_platform_config("codex")


@pytest.fixture
def codex_env():
    """Get the Jinja2 environment for codex templates."""
    return get_template_env("codex")


@pytest.fixture
def converter():
    return HookConverter()


# ---------------------------------------------------------------------------
# DC-1: Hook script output field name
# ---------------------------------------------------------------------------


class TestDC1WrongOutputFormat:
    """DC-1: Converted hooks must emit model-visible SessionStart context."""

    def test_converted_script_contains_hookspecificoutput(
        self, converter, codex_config, codex_env
    ):
        """The session-start script uses Codex's model-context output field."""
        template = codex_env.get_template("hook.sh.j2")
        result = converter.convert_script(
            hook_name="session-start",
            event="session_start",
            platform_config=codex_config,
            template=template,
        )
        assert "hookSpecificOutput" in result
        assert "additionalContext" in result

    def test_converted_script_does_not_output_system_message(
        self, converter, codex_config, codex_env
    ):
        """UI-only systemMessage must not replace model-visible context."""
        template = codex_env.get_template("hook.sh.j2")
        result = converter.convert_script(
            hook_name="session-start",
            event="session_start",
            platform_config=codex_config,
            template=template,
        )
        assert '"systemMessage"' not in result

    def test_converted_hooks_json_uses_command_hook_schema(
        self, converter, codex_config, codex_env
    ):
        """The rendered hooks.json must use official Codex command hook schema."""
        template = codex_env.get_template("hooks.json.j2")
        result = converter.convert_hooks_json(
            platform_config=codex_config,
            template=template,
        )
        command_hook = result["hooks"]["SessionStart"][0]["hooks"][0]
        assert command_hook["type"] == "command"
        assert "command" in command_hook
        assert "additionalContext" not in json.dumps(result)
        assert "hookSpecificOutput" not in json.dumps(result)


# ---------------------------------------------------------------------------
# DC-2: Incorrect matcher values in hooks.json
# ---------------------------------------------------------------------------


class TestDC2IncorrectMatchers:
    """DC-2: Rendered matchers must equal the Codex platform contract."""

    def test_converted_hooks_json_contains_all_configured_matchers(
        self, converter, codex_config, codex_env
    ):
        """Lifecycle coverage includes startup, resume, clear, and compact."""
        template = codex_env.get_template("hooks.json.j2")
        result = converter.convert_hooks_json(
            platform_config=codex_config,
            template=template,
        )
        matcher = result["hooks"]["SessionStart"][0]["matcher"]
        assert set(matcher.split("|")) == {"startup", "resume", "clear", "compact"}

    def test_converted_hooks_json_uses_codex_matchers(
        self, converter, codex_config, codex_env
    ):
        """hooks.json must include Codex's startup session matcher."""
        template = codex_env.get_template("hooks.json.j2")
        result = converter.convert_hooks_json(
            platform_config=codex_config,
            template=template,
        )
        matcher = result["hooks"]["SessionStart"][0]["matcher"]
        assert "startup" in matcher, (
            "Converted hooks.json missing 'startup' matcher. "
            "Codex uses 'startup' as the session start event name."
        )
        assert "resume" in matcher, (
            "Converted hooks.json missing 'resume' matcher. "
            "Codex uses 'resume' for session resume events."
        )

    def test_matchers_source_is_platform_config_not_source_file(
        self, converter, codex_config, codex_env
    ):
        """Matchers must come from platform config, not be hardcoded or from source."""
        # Verify the platform config's matchers are what end up in the output
        expected_matchers = codex_config.formats.hook_output["session_start_matchers"]
        template = codex_env.get_template("hooks.json.j2")
        result = converter.convert_hooks_json(
            platform_config=codex_config,
            template=template,
        )
        actual_matcher = result["hooks"]["SessionStart"][0]["matcher"]
        expected_matcher = "|".join(expected_matchers)
        assert actual_matcher == expected_matcher, (
            f"Matcher in output {actual_matcher!r} does not match platform config "
            f"{expected_matchers!r}. Matchers must come from platform config, "
            "not be hardcoded or read from the source hooks.json."
        )


# ---------------------------------------------------------------------------
# DC-3: Env var adaptation
# ---------------------------------------------------------------------------


class TestDC3EnvVarAdaptation:
    """DC-3: ${CLAUDE_PLUGIN_ROOT} must not appear in converted scripts.

    Rationale: Claude Code sets CLAUDE_PLUGIN_ROOT automatically. Codex does not.
    A converted hook script referencing ${CLAUDE_PLUGIN_ROOT} will fail with
    'unbound variable' (set -u is active in the template) or produce an empty
    PLUGIN_DIR — causing silent failures when sourcing skill env.sh files.

    This is especially insidious: if SKILLS_DIR resolves to '/skills' (no plugin
    prefix), the for-loop finds no files and exits 0 silently.
    """

    def test_converted_script_does_not_reference_claude_plugin_root(
        self, converter, codex_config, codex_env
    ):
        """Converted script must not contain ${CLAUDE_PLUGIN_ROOT}."""
        template = codex_env.get_template("hook.sh.j2")
        result = converter.convert_script(
            hook_name="session-start",
            event="session_start",
            platform_config=codex_config,
            template=template,
        )
        assert "CLAUDE_PLUGIN_ROOT" not in result, (
            "Converted script references ${CLAUDE_PLUGIN_ROOT} — this env var is "
            "set by Claude Code but NOT by Codex. With set -euo pipefail, this "
            "causes an 'unbound variable' error and silent hook failure."
        )

    def test_converted_script_uses_codex_skills_dir(
        self, converter, codex_config, codex_env
    ):
        """Converted script must reference the Codex native skills directory."""
        template = codex_env.get_template("hook.sh.j2")
        result = converter.convert_script(
            hook_name="session-start",
            event="session_start",
            platform_config=codex_config,
            template=template,
        )
        expected_skills_dir = codex_config.paths.skills_dir
        assert expected_skills_dir in result, (
            f"Converted script does not reference Codex skills dir '{expected_skills_dir}'. "
            "The script will not find skills."
        )


class TestDC4HooksJsonShape:
    def test_convert_hooks_json_output_is_valid_json_dict(
        self, converter, codex_config, codex_env
    ):
        """convert_hooks_json must return a Python dict (parseable JSON structure).

        This guards against the converter returning a raw string that happens to
        look like JSON — callers must be able to inspect result['hooks'] reliably.
        """
        template = codex_env.get_template("hooks.json.j2")
        result = converter.convert_hooks_json(
            platform_config=codex_config,
            template=template,
        )
        assert isinstance(result, dict), (
            f"convert_hooks_json returned {type(result).__name__}, expected dict. "
            "The caller needs a dict to write to hooks.json — a string would require "
            "re-parsing and could silently produce wrong output."
        )
        assert "hooks" in result, "Result dict missing 'hooks' key."
        assert isinstance(result["hooks"], dict), "'hooks' must be a map."
        assert len(result["hooks"]) > 0, "'hooks' map must not be empty."
