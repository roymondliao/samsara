"""
Unit tests for HookConverter.

Tests cover correct behavior of each conversion operation:
- convert_script: renders hook.sh.j2 with correct template variables
- convert_hooks_json: renders hooks.json.j2 and returns a parsed dict

These tests assume DC tests above are passing — they focus on correct shape
and content of output, not on the death cases (wrong format, wrong matchers).
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
    return load_platform_config("codex")


@pytest.fixture
def codex_env():
    return get_template_env("codex")


@pytest.fixture
def converter():
    return HookConverter()


# ---------------------------------------------------------------------------
# convert_script unit tests
# ---------------------------------------------------------------------------


class TestConvertScript:
    """Unit tests for HookConverter.convert_script."""

    def test_returns_string(self, converter, codex_config, codex_env):
        """convert_script returns a string."""
        template = codex_env.get_template("hook.sh.j2")
        result = converter.convert_script(
            hook_name="session-start",
            event="session_start",
            platform_config=codex_config,
            template=template,
        )
        assert isinstance(result, str)

    def test_output_starts_with_shebang(self, converter, codex_config, codex_env):
        """Rendered hook script starts with bash shebang."""
        template = codex_env.get_template("hook.sh.j2")
        result = converter.convert_script(
            hook_name="session-start",
            event="session_start",
            platform_config=codex_config,
            template=template,
        )
        assert result.startswith("#!/usr/bin/env bash"), (
            "Hook script does not start with shebang — will fail to execute."
        )

    def test_hook_name_in_output(self, converter, codex_config, codex_env):
        """The hook_name is embedded in the rendered script."""
        template = codex_env.get_template("hook.sh.j2")
        result = converter.convert_script(
            hook_name="session-start",
            event="session_start",
            platform_config=codex_config,
            template=template,
        )
        assert "session-start" in result

    def test_event_in_output(self, converter, codex_config, codex_env):
        """The event name is embedded in the rendered script."""
        template = codex_env.get_template("hook.sh.j2")
        result = converter.convert_script(
            hook_name="session-start",
            event="session_start",
            platform_config=codex_config,
            template=template,
        )
        assert "session_start" in result

    def test_plugin_dir_from_config(self, converter, codex_config, codex_env):
        """PLUGIN_DIR in rendered script matches codex platform config."""
        template = codex_env.get_template("hook.sh.j2")
        result = converter.convert_script(
            hook_name="session-start",
            event="session_start",
            platform_config=codex_config,
            template=template,
        )
        # codex.yaml has paths.plugin_dir = ".codex-plugin"
        assert ".codex-plugin" in result

    def test_skills_dir_from_config(self, converter, codex_config, codex_env):
        """skills_dir path in rendered script matches codex platform config."""
        template = codex_env.get_template("hook.sh.j2")
        result = converter.convert_script(
            hook_name="session-start",
            event="session_start",
            platform_config=codex_config,
            template=template,
        )
        # codex.yaml has paths.skills_dir = "skills"
        assert "skills" in result

    def test_no_unfilled_template_variables(self, converter, codex_config, codex_env):
        """Rendered script has no unfilled Jinja2 placeholders."""
        template = codex_env.get_template("hook.sh.j2")
        result = converter.convert_script(
            hook_name="session-start",
            event="session_start",
            platform_config=codex_config,
            template=template,
        )
        assert "{{" not in result, "Unfilled template variable found in output."
        assert "}}" not in result, "Unfilled template variable found in output."

    def test_check_codebase_map_script(self, converter, codex_config, codex_env):
        """convert_script works for check-codebase-map hook name."""
        template = codex_env.get_template("hook.sh.j2")
        result = converter.convert_script(
            hook_name="check-codebase-map",
            event="session_start",
            platform_config=codex_config,
            template=template,
        )
        assert isinstance(result, str)
        assert "check-codebase-map" in result


# ---------------------------------------------------------------------------
# convert_hooks_json unit tests
# ---------------------------------------------------------------------------


class TestConvertHooksJson:
    """Unit tests for HookConverter.convert_hooks_json."""

    def test_returns_dict(self, converter, codex_config, codex_env):
        """convert_hooks_json returns a Python dict."""
        template = codex_env.get_template("hooks.json.j2")
        result = converter.convert_hooks_json(
            platform_config=codex_config,
            template=template,
        )
        assert isinstance(result, dict)

    def test_hooks_key_present(self, converter, codex_config, codex_env):
        """Result dict has 'hooks' key with non-empty list."""
        template = codex_env.get_template("hooks.json.j2")
        result = converter.convert_hooks_json(
            platform_config=codex_config,
            template=template,
        )
        assert "hooks" in result
        assert len(result["hooks"]) >= 1

    def test_hook_entry_has_required_fields(self, converter, codex_config, codex_env):
        """Each hook entry has name, event, matchers, command, systemMessage."""
        template = codex_env.get_template("hooks.json.j2")
        result = converter.convert_hooks_json(
            platform_config=codex_config,
            template=template,
        )
        entry = result["hooks"][0]
        required = {"name", "event", "matchers", "command", "systemMessage"}
        missing = required - set(entry.keys())
        assert not missing, f"Hook entry missing required fields: {missing}"

    def test_hook_name_is_samsara_session_start(
        self, converter, codex_config, codex_env
    ):
        """First hook entry name is 'samsara-session-start'."""
        template = codex_env.get_template("hooks.json.j2")
        result = converter.convert_hooks_json(
            platform_config=codex_config,
            template=template,
        )
        assert result["hooks"][0]["name"] == "samsara-session-start"

    def test_hook_event_is_session_start(self, converter, codex_config, codex_env):
        """First hook entry event is 'session_start'."""
        template = codex_env.get_template("hooks.json.j2")
        result = converter.convert_hooks_json(
            platform_config=codex_config,
            template=template,
        )
        assert result["hooks"][0]["event"] == "session_start"

    def test_command_path_contains_hook_script_name(
        self, converter, codex_config, codex_env
    ):
        """Command field references the samsara-session-start.sh script."""
        template = codex_env.get_template("hooks.json.j2")
        result = converter.convert_hooks_json(
            platform_config=codex_config,
            template=template,
        )
        command = result["hooks"][0]["command"]
        assert "samsara-session-start.sh" in command, (
            f"Command '{command}' does not reference samsara-session-start.sh"
        )

    def test_default_system_message_is_string(self, converter, codex_config, codex_env):
        """systemMessage field is a non-empty string when no custom message given."""
        template = codex_env.get_template("hooks.json.j2")
        result = converter.convert_hooks_json(
            platform_config=codex_config,
            template=template,
        )
        sm = result["hooks"][0]["systemMessage"]
        assert isinstance(sm, str), f"systemMessage must be str, got {type(sm)}"
        assert len(sm) > 0, "systemMessage must not be empty"

    def test_custom_system_message_used(self, converter, codex_config, codex_env):
        """If system_message is provided, it appears in the output."""
        template = codex_env.get_template("hooks.json.j2")
        custom = "Custom samsara bootstrap context."
        result = converter.convert_hooks_json(
            platform_config=codex_config,
            template=template,
            system_message=custom,
        )
        assert result["hooks"][0]["systemMessage"] == custom

    def test_output_is_json_serializable(self, converter, codex_config, codex_env):
        """Result dict can be serialized to JSON without error."""
        template = codex_env.get_template("hooks.json.j2")
        result = converter.convert_hooks_json(
            platform_config=codex_config,
            template=template,
        )
        # Should not raise
        json_str = json.dumps(result, indent=2)
        reparsed = json.loads(json_str)
        assert reparsed["hooks"][0]["name"] == result["hooks"][0]["name"]

    def test_hooks_dir_in_command_uses_codex_plugin_dir(
        self, converter, codex_config, codex_env
    ):
        """hooks_dir in command derives from Codex plugin_dir config."""
        template = codex_env.get_template("hooks.json.j2")
        result = converter.convert_hooks_json(
            platform_config=codex_config,
            template=template,
        )
        command = result["hooks"][0]["command"]
        # The codex plugin_dir is '.codex-plugin'
        assert ".codex-plugin" in command, (
            f"Command '{command}' does not use Codex plugin_dir '.codex-plugin'. "
            "hooks_dir must be derived from the target platform config, not source config."
        )


# ---------------------------------------------------------------------------
# convert_check_codebase_map_script unit tests
# ---------------------------------------------------------------------------


class TestConvertCheckCodebaseMapScript:
    """Unit tests for HookConverter.convert_check_codebase_map_script.

    This method exists because check-codebase-map has different source logic
    (CLAUDE_PROJECT_DIR check) that cannot be directly adapted for Codex without
    a verified Codex equivalent env var. A dedicated method makes the behavioral
    gap visible rather than silently using session-start logic for this hook.
    """

    def test_returns_string(self, converter, codex_config, codex_env):
        """convert_check_codebase_map_script returns a string."""
        template = codex_env.get_template("hook.sh.j2")
        result = converter.convert_check_codebase_map_script(
            event="session_start",
            platform_config=codex_config,
            template=template,
        )
        assert isinstance(result, str)

    def test_hook_name_is_check_codebase_map(self, converter, codex_config, codex_env):
        """Rendered script identifies as check-codebase-map hook."""
        template = codex_env.get_template("hook.sh.j2")
        result = converter.convert_check_codebase_map_script(
            event="session_start",
            platform_config=codex_config,
            template=template,
        )
        assert "check-codebase-map" in result

    def test_does_not_reference_claude_plugin_root(
        self, converter, codex_config, codex_env
    ):
        """Rendered script does not reference ${CLAUDE_PLUGIN_ROOT}."""
        template = codex_env.get_template("hook.sh.j2")
        result = converter.convert_check_codebase_map_script(
            event="session_start",
            platform_config=codex_config,
            template=template,
        )
        assert "CLAUDE_PLUGIN_ROOT" not in result

    def test_outputs_system_message_json(self, converter, codex_config, codex_env):
        """Rendered script outputs systemMessage (not hookSpecificOutput)."""
        template = codex_env.get_template("hook.sh.j2")
        result = converter.convert_check_codebase_map_script(
            event="session_start",
            platform_config=codex_config,
            template=template,
        )
        assert "systemMessage" in result
        assert "hookSpecificOutput" not in result


# ---------------------------------------------------------------------------
# HookConverter class structure tests
# ---------------------------------------------------------------------------


class TestHookConverterStructure:
    """Verify HookConverter exposes the required interface."""

    def test_has_convert_script_method(self):
        """HookConverter has convert_script method."""
        assert hasattr(HookConverter, "convert_script"), (
            "HookConverter missing convert_script method"
        )

    def test_has_convert_hooks_json_method(self):
        """HookConverter has convert_hooks_json method."""
        assert hasattr(HookConverter, "convert_hooks_json"), (
            "HookConverter missing convert_hooks_json method"
        )

    def test_converter_is_instantiable_without_args(self):
        """HookConverter() works without arguments."""
        converter = HookConverter()
        assert converter is not None


# ---------------------------------------------------------------------------
# Error handling tests
# ---------------------------------------------------------------------------


class TestHookConverterErrorHandling:
    """Verify HookConverter raises clearly on invalid input."""

    def test_missing_formats_hook_output_raises(self, codex_env):
        """If platform config has no formats.hook_output, raises ValueError."""
        from samsara_cli.config.schema import (
            FormatsConfig,
            PathsConfig,
            PlatformConfig,
            PlatformIdentity,
            SourceConfig,
        )

        # Build a minimal config with no formats
        config = PlatformConfig(
            platform=PlatformIdentity(name="test"),
            source=SourceConfig(
                plugin_dir=".claude-plugin",
                skills_dir="skills",
                agents_dir="agents",
                hooks_dir="hooks",
                references_dir="references",
            ),
            paths=PathsConfig(plugin_dir=".test-plugin"),
            formats=FormatsConfig(hook_output=None),
        )
        converter = HookConverter()
        template = codex_env.get_template("hooks.json.j2")

        with pytest.raises((ValueError, KeyError, TypeError)):
            converter.convert_hooks_json(
                platform_config=config,
                template=template,
            )

    def test_missing_paths_raises(self, codex_env):
        """If platform config has no paths, raises ValueError."""
        from samsara_cli.config.schema import (
            FormatsConfig,
            PlatformConfig,
            PlatformIdentity,
            SourceConfig,
        )

        config = PlatformConfig(
            platform=PlatformIdentity(name="test"),
            source=SourceConfig(
                plugin_dir=".claude-plugin",
                skills_dir="skills",
                agents_dir="agents",
                hooks_dir="hooks",
                references_dir="references",
            ),
            formats=FormatsConfig(
                hook_output={
                    "context_injection_field": "systemMessage",
                    "session_start_matchers": ["startup", "resume"],
                    "template": "hooks.json.j2",
                    "script_template": "hook.sh.j2",
                }
            ),
        )
        converter = HookConverter()
        template = codex_env.get_template("hooks.json.j2")

        with pytest.raises((ValueError, AttributeError, TypeError)):
            converter.convert_hooks_json(
                platform_config=config,
                template=template,
            )
