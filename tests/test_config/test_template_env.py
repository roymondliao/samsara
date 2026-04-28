"""
Tests for Jinja2 template environment — specifically StrictUndefined behavior.

Acceptance criteria: "Template rendering with missing field" must fail loudly.
"""

import pytest
from jinja2 import UndefinedError

from samsara_cli.config.template_env import get_template_env


class TestGetTemplateEnv:
    def test_codex_env_created_successfully(self):
        env = get_template_env("codex")
        assert env is not None

    def test_codex_env_has_correct_template_loader(self):
        env = get_template_env("codex")
        # Must be able to load at least one template
        template = env.get_template("agent.toml.j2")
        assert template is not None

    def test_nonexistent_platform_raises_file_not_found(self):
        """Missing template directory must raise FileNotFoundError — not return
        an environment that silently renders nothing."""
        with pytest.raises(FileNotFoundError) as exc_info:
            get_template_env("nonexistent_platform")
        assert "nonexistent_platform" in str(exc_info.value)


class TestStrictUndefined:
    """These tests guard against the silent-empty-template failure case.

    An agent with missing developer_instructions renders as empty string
    by default Jinja2. With StrictUndefined, it raises UndefinedError.
    """

    def test_missing_variable_raises_undefined_error(self):
        """The core acceptance criteria: missing template variable must raise,
        not silently render empty. This is the 'Template rendering with stale data'
        death case from the architecture context."""
        env = get_template_env("codex")
        # Create a simple inline template — don't render the full agent.toml.j2
        # which requires all its variables. Instead test StrictUndefined directly.
        template = env.from_string("{{ missing_variable }}")
        with pytest.raises(UndefinedError):
            template.render()

    def test_missing_variable_in_string_context_raises(self):
        """Accessing a missing variable in a string operation also raises."""
        env = get_template_env("codex")
        template = env.from_string("prefix-{{ undefined_var }}-suffix")
        with pytest.raises(UndefinedError):
            template.render(some_other_var="present")

    def test_present_variable_renders_correctly(self):
        """Sanity check: present variables must render correctly."""
        env = get_template_env("codex")
        template = env.from_string("hello {{ name }}")
        result = template.render(name="world")
        assert result == "hello world"

    def test_all_template_files_loadable(self):
        """All codex templates must be loadable without rendering errors."""
        env = get_template_env("codex")
        expected_templates = [
            "agent.toml.j2",
            "hooks.json.j2",
            "hook.sh.j2",
            "manifest.json.j2",
        ]
        for template_name in expected_templates:
            template = env.get_template(template_name)
            assert template is not None, f"Template {template_name} failed to load"
