"""
Gemini agent converter tests.

Gemini CLI subagents are Markdown files with YAML frontmatter. These tests guard
against silently reusing Codex TOML output for Gemini.
"""

from pathlib import Path

import pytest

from samsara_cli.config.loader import load_platform_config
from samsara_cli.config.template_env import get_template_env
from samsara_cli.converter.agent import AgentConverter


def _gemini_inputs():
    config = load_platform_config("gemini-cli")
    env = get_template_env("gemini-cli")
    return config, env.get_template("agent.md.j2")


class TestGeminiAgentMarkdownConversion:
    def test_gemini_agent_conversion_outputs_markdown_frontmatter(self, tmp_path: Path):
        config, template = _gemini_inputs()
        converter = AgentConverter()
        source_path = tmp_path / "implementer.md"
        source_path.write_text("# Implementer\n\nUse the Read tool.\n")

        converted = converter.convert_markdown_from_text(
            source_text=source_path.read_text(),
            source_path=source_path,
            rules=config.transformations,
            naming=config.naming,
            template=template,
        )

        assert converted.agent_name == "samsara-implementer"
        assert converted.output_extension == ".md"
        assert converted.rendered_content.startswith("---\n")
        assert '---\nname: "samsara-implementer"' in converted.rendered_content
        assert 'description: "Implementer"' in converted.rendered_content
        assert "read_file tool" in converted.rendered_content
        assert "developer_instructions" not in converted.rendered_content
        assert f"Source: {source_path.name}" in converted.rendered_content
        assert str(tmp_path) not in converted.rendered_content

    def test_gemini_agent_conversion_rejects_empty_body(self, tmp_path: Path):
        config, template = _gemini_inputs()
        converter = AgentConverter()
        source_path = tmp_path / "empty.md"

        with pytest.raises(ValueError, match="empty"):
            converter.convert_markdown(
                body="   \n",
                source_path=source_path,
                rules=config.transformations,
                naming=config.naming,
                template=template,
            )

    def test_gemini_agent_conversion_strips_source_frontmatter(self, tmp_path: Path):
        config, template = _gemini_inputs()
        converter = AgentConverter()
        source_path = tmp_path / "reviewer.md"
        source_text = (
            "---\nname: source-name\ndescription: source desc\n---\n"
            "# Reviewer\n\nBody.\n"
        )

        converted = converter.convert_markdown_from_text(
            source_text=source_text,
            source_path=source_path,
            rules=config.transformations,
            naming=config.naming,
            template=template,
        )

        assert "source-name" not in converted.rendered_content
        assert converted.rendered_content.count("---") == 2
        assert 'name: "samsara-reviewer"' in converted.rendered_content

    def test_gemini_agent_conversion_removes_subagent_type_pattern(
        self, tmp_path: Path
    ):
        config, template = _gemini_inputs()
        converter = AgentConverter()
        source_path = tmp_path / "coordinator.md"
        source_text = '# Coordinator\n\nUse subagent_type: "samsara:code-reviewer".\n'

        converted = converter.convert_markdown_from_text(
            source_text=source_text,
            source_path=source_path,
            rules=config.transformations,
            naming=config.naming,
            template=template,
        )

        assert "subagent_type:" not in converted.rendered_content
        assert 'subagent named "samsara-code-reviewer"' in converted.rendered_content
