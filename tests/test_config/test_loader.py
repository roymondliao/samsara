"""
Unit tests for config loader — testing correct config loading behavior.
"""

import pytest

from samsara_cli.config.loader import load_platform_config
from samsara_cli.config.schema import PlatformConfig, TransformationRule


class TestLoadPlatformConfig:
    def test_load_codex_returns_platform_config(self):
        config = load_platform_config("codex")
        assert isinstance(config, PlatformConfig)

    def test_codex_platform_name(self):
        config = load_platform_config("codex")
        assert config.platform.name == "codex"

    def test_codex_platform_version_cmd(self):
        config = load_platform_config("codex")
        assert config.platform.version_cmd == "codex --version"

    def test_codex_paths_plugin_dir(self):
        config = load_platform_config("codex")
        assert config.paths is not None
        assert config.paths.plugin_dir == ".codex"

    def test_codex_paths_agents_dir(self):
        config = load_platform_config("codex")
        assert config.paths.agents_dir == ".codex/agents"

    def test_codex_install_project_target(self):
        config = load_platform_config("codex")
        assert config.install is not None
        assert config.install.project.target == "$CWD"

    def test_codex_install_global_config_path(self):
        config = load_platform_config("codex")
        assert config.install.global_.config_path == "~/.codex/config.toml"

    def test_codex_naming_skill_prefix(self):
        config = load_platform_config("codex")
        assert config.naming is not None
        assert config.naming.skill_prefix == "samsara"
        assert config.naming.separator == "-"

    def test_codex_transformations_are_list_of_rules(self):
        config = load_platform_config("codex")
        assert isinstance(config.transformations, list)
        for rule in config.transformations:
            assert isinstance(rule, TransformationRule)

    def test_codex_has_skill_invocation_rule(self):
        """The skill_invocation transformation rule must exist in codex config."""
        config = load_platform_config("codex")
        rule_ids = [r.id for r in config.transformations]
        assert "skill_invocation" in rule_ids, (
            f"Expected 'skill_invocation' rule, found: {rule_ids}"
        )

    def test_codex_has_tool_read_rule(self):
        config = load_platform_config("codex")
        rule_ids = [r.id for r in config.transformations]
        assert "tool_read" in rule_ids

    def test_codex_has_tool_bash_rule(self):
        config = load_platform_config("codex")
        rule_ids = [r.id for r in config.transformations]
        assert "tool_bash" in rule_ids

    def test_codex_permissions_sandbox_mode(self):
        config = load_platform_config("codex")
        assert config.permissions is not None
        assert config.permissions.sandbox_mode == "workspace-write"

    def test_codex_formats_agent_type(self):
        config = load_platform_config("codex")
        assert config.formats is not None
        assert config.formats.agent_format is not None
        assert config.formats.agent_format["type"] == "toml"

    def test_codex_source_config_present(self):
        """Source config (claude-plugin source paths) must be present in merged config."""
        config = load_platform_config("codex")
        assert config.source is not None
        assert config.source.plugin_dir == ".claude-plugin"

    def test_codex_regex_rules_have_valid_patterns(self):
        """All regex-type rules must have valid, compilable patterns.
        This verifies the Pydantic validator ran correctly end-to-end."""
        import re

        config = load_platform_config("codex")
        regex_rules = [r for r in config.transformations if r.type == "regex"]
        assert len(regex_rules) > 0, "Expected at least some regex rules"
        for rule in regex_rules:
            # Should not raise — validator already ran, but double-check
            try:
                re.compile(rule.match)
            except re.error as e:
                pytest.fail(f"Rule '{rule.id}' has invalid regex '{rule.match}': {e}")


class TestLoadGeminiCli:
    def test_load_gemini_cli_returns_platform_config(self):
        config = load_platform_config("gemini-cli")
        assert isinstance(config, PlatformConfig)

    def test_gemini_cli_platform_identity(self):
        config = load_platform_config("gemini-cli")
        assert config.platform.name == "gemini-cli"
        assert config.platform.version_cmd == "gemini --version"

    def test_gemini_cli_paths_are_native_gemini_paths(self):
        config = load_platform_config("gemini-cli")
        assert config.paths is not None
        assert config.paths.plugin_dir == ".gemini"
        assert config.paths.skills_dir == ".gemini/skills"
        assert config.paths.agents_dir == ".gemini/agents"
        assert config.paths.hooks_file == "settings.json"

    def test_gemini_cli_global_config_path(self):
        config = load_platform_config("gemini-cli")
        assert config.install is not None
        assert config.install.global_ is not None
        assert config.install.global_.config_path == "~/.gemini/settings.json"

    def test_gemini_cli_formats(self):
        config = load_platform_config("gemini-cli")
        assert config.formats is not None
        assert config.formats.agent_format is not None
        assert config.formats.agent_format["type"] == "markdown"
        assert config.formats.agent_format["template"] == "agent.md.j2"
        assert config.formats.hook_output is not None
        assert (
            config.formats.hook_output["context_injection_field"]
            == "hookSpecificOutput.additionalContext"
        )
        assert config.formats.hook_output["template"] == "settings.json.j2"

    def test_gemini_cli_uses_gemini_skills_not_agents_alias(self):
        config = load_platform_config("gemini-cli")
        assert config.paths is not None
        assert config.paths.skills_dir == ".gemini/skills"
        assert config.paths.skills_dir != ".agents/skills"


class TestLoadClaudeCode:
    def test_load_claude_code_returns_platform_config(self):
        """claude-code platform must be loadable."""
        config = load_platform_config("claude-code")
        assert isinstance(config, PlatformConfig)

    def test_claude_code_platform_name(self):
        config = load_platform_config("claude-code")
        assert config.platform.name == "claude-code"

    def test_claude_code_source_config(self):
        config = load_platform_config("claude-code")
        assert config.source is not None
        assert config.source.plugin_dir == ".claude-plugin"
