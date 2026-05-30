# Unit tests for agent.py -- AgentConverter.
#
# Tests per-agent conversion of the real samsara agents, description extraction,
# frontmatter parsing, and the full pipeline integration.

import tomllib

import pytest
from pathlib import Path

from samsara_cli.config.schema import TransformationRule, NamingConfig
from samsara_cli.converter.agent import AgentConverter, ConvertedAgent


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

AGENTS_DIR = Path(__file__).resolve().parents[2] / "agents"

SAMSARA_AGENTS = [
    "auto-gatekeeper",
    "code-quality-reviewer",
    "code-reviewer",
    "implementer",
    "infra-explorer",
    "structure-explorer",
    "yin-explorer",
]


def make_naming(prefix: str = "samsara", sep: str = "-") -> NamingConfig:
    return NamingConfig(skill_prefix=prefix, separator=sep)


def make_rule(
    id: str,
    match: str,
    replace: str,
    scope: str = "body",
    type: str = "literal",
    priority: str = "high",
) -> TransformationRule:
    return TransformationRule(
        id=id, scope=scope, type=type, match=match, replace=replace, priority=priority
    )


def get_codex_template():
    from samsara_cli.config.template_env import get_template_env

    env = get_template_env("codex")
    return env.get_template("agent.toml.j2")


def strip_frontmatter(text: str) -> str:
    # Strip YAML frontmatter and return body only.
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].rstrip("\r\n") != "---":
        return text
    for i in range(1, len(lines)):
        if lines[i].rstrip("\r\n") == "---":
            return "".join(lines[i + 1 :])
    return text


# ---------------------------------------------------------------------------
# ConvertedAgent dataclass / namedtuple shape tests
# ---------------------------------------------------------------------------


class TestConvertedAgentShape:
    def test_converted_agent_has_required_fields(self):
        # ConvertedAgent must expose agent_name, toml_content, transformed_body.
        converter = AgentConverter()
        template = get_codex_template()
        naming = make_naming()

        result = converter.convert(
            body="You are a simple agent.",
            source_path=Path("/fake/agent/simple-agent.md"),
            rules=[],
            naming=naming,
            template=template,
        )

        assert isinstance(result, ConvertedAgent)
        assert hasattr(result, "agent_name")
        assert hasattr(result, "toml_content")
        assert hasattr(result, "transformed_body")

    def test_converted_agent_toml_content_is_string(self):
        converter = AgentConverter()
        template = get_codex_template()
        naming = make_naming()

        result = converter.convert(
            body="Agent instructions.",
            source_path=Path("/fake/agent/str-agent.md"),
            rules=[],
            naming=naming,
            template=template,
        )

        assert isinstance(result.toml_content, str)
        assert len(result.toml_content) > 0


# ---------------------------------------------------------------------------
# Agent name generation tests
# ---------------------------------------------------------------------------


class TestAgentNameGeneration:
    def test_simple_stem_generates_expected_name(self):
        converter = AgentConverter()
        template = get_codex_template()
        naming = make_naming(prefix="samsara", sep="-")

        result = converter.convert(
            body="Body.",
            source_path=Path("/fake/agent/implementer.md"),
            rules=[],
            naming=naming,
            template=template,
        )
        assert result.agent_name == "samsara-implementer"

    def test_hyphenated_stem_generates_expected_name(self):
        converter = AgentConverter()
        template = get_codex_template()
        naming = make_naming(prefix="samsara", sep="-")

        result = converter.convert(
            body="Body.",
            source_path=Path("/fake/agent/code-quality-reviewer.md"),
            rules=[],
            naming=naming,
            template=template,
        )
        assert result.agent_name == "samsara-code-quality-reviewer"

    def test_name_appears_in_toml_section(self):
        converter = AgentConverter()
        template = get_codex_template()
        naming = make_naming()

        result = converter.convert(
            body="Body.",
            source_path=Path("/fake/agent/yin-explorer.md"),
            rules=[],
            naming=naming,
            template=template,
        )

        parsed = tomllib.loads(result.toml_content)
        assert parsed["name"] == "samsara-yin-explorer"

    def test_agent_toml_uses_codex_top_level_schema(self):
        converter = AgentConverter()
        template = get_codex_template()
        naming = make_naming()

        result = converter.convert(
            body="# Yin Explorer\n\nBody.",
            source_path=Path("/fake/agent/yin-explorer.md"),
            rules=[],
            naming=naming,
            template=template,
        )

        parsed = tomllib.loads(result.toml_content)
        assert "agent" not in parsed, "Codex subagent TOML must not use [agent]."
        assert parsed["name"] == "samsara-yin-explorer"
        assert parsed["description"] == "Yin Explorer"
        assert "Body." in parsed["developer_instructions"]


# ---------------------------------------------------------------------------
# Description extraction tests
# ---------------------------------------------------------------------------


class TestDescriptionExtraction:
    def test_body_starting_with_h1_heading_extracts_description(self):
        # First H1 heading becomes the description.
        converter = AgentConverter()
        template = get_codex_template()
        naming = make_naming()

        body = "# My Agent Title\n\nBody content follows.\n"

        result = converter.convert(
            body=body,
            source_path=Path("/fake/agent/heading-agent.md"),
            rules=[],
            naming=naming,
            template=template,
        )

        assert result.description is not None
        assert "My Agent Title" in result.description

    def test_body_starting_with_prose_extracts_first_line(self):
        # If no heading, first non-empty line becomes description.
        converter = AgentConverter()
        template = get_codex_template()
        naming = make_naming()

        body = "You are a coding agent that does things.\n\nMore instructions follow.\n"

        result = converter.convert(
            body=body,
            source_path=Path("/fake/agent/prose-agent.md"),
            rules=[],
            naming=naming,
            template=template,
        )

        assert result.description is not None
        assert len(result.description) > 0

    def test_description_is_single_line_not_multiline(self):
        # Description must be a single line (no embedded newlines).
        converter = AgentConverter()
        template = get_codex_template()
        naming = make_naming()

        body = "# Title Line\n\nParagraph content.\n"

        result = converter.convert(
            body=body,
            source_path=Path("/fake/agent/single-line-agent.md"),
            rules=[],
            naming=naming,
            template=template,
        )

        assert "\n" not in result.description, "Description must not contain newlines"


# ---------------------------------------------------------------------------
# Frontmatter parsing tests
# ---------------------------------------------------------------------------


class TestFrontmatterHandling:
    def test_agent_with_frontmatter_uses_body_only(self):
        # When source has frontmatter, only body content appears in instructions.
        converter = AgentConverter()
        template = get_codex_template()
        naming = make_naming()

        source_with_frontmatter = (
            "---\n"
            "name: test-agent\n"
            "description: A test agent\n"
            "---\n"
            "\n"
            "# Test Agent\n"
            "You are a test agent.\n"
        )

        result = converter.convert_from_text(
            source_text=source_with_frontmatter,
            source_path=Path("/fake/agent/frontmatter-agent.md"),
            rules=[],
            naming=naming,
            template=template,
        )

        # Frontmatter fields must not appear verbatim in developer_instructions
        parsed = tomllib.loads(result.toml_content)
        instructions = parsed["developer_instructions"]
        assert "name: test-agent" not in instructions, (
            "Frontmatter leaked into developer_instructions"
        )
        assert "You are a test agent" in instructions

    def test_agent_without_frontmatter_uses_entire_body(self):
        # No frontmatter means the entire text is the body.
        converter = AgentConverter()
        template = get_codex_template()
        naming = make_naming()

        body_only = "You are a no-frontmatter agent.\n\nDo things carefully.\n"

        result = converter.convert_from_text(
            source_text=body_only,
            source_path=Path("/fake/agent/no-fm-agent.md"),
            rules=[],
            naming=naming,
            template=template,
        )

        parsed = tomllib.loads(result.toml_content)
        instructions = parsed["developer_instructions"]
        assert "no-frontmatter agent" in instructions


# ---------------------------------------------------------------------------
# Full pipeline: each real samsara agent
# ---------------------------------------------------------------------------


class TestRealAgentConversion:
    @pytest.mark.parametrize("agent_name", SAMSARA_AGENTS)
    def test_real_agent_converts_to_valid_toml(self, agent_name):
        # Each real agent .md must produce valid, parseable TOML.
        agent_path = AGENTS_DIR / f"{agent_name}.md"
        if not agent_path.exists():
            pytest.skip(f"Agent file not found: {agent_path}")

        converter = AgentConverter()
        template = get_codex_template()
        naming = make_naming()

        full_text = agent_path.read_text(encoding="utf-8")

        result = converter.convert_from_text(
            source_text=full_text,
            source_path=agent_path,
            rules=[],
            naming=naming,
            template=template,
        )

        # Must parse as valid TOML
        try:
            parsed = tomllib.loads(result.toml_content)
        except Exception as e:
            pytest.fail(f"Agent '{agent_name}' produced invalid TOML: {e}")

        # Must have expected name
        assert parsed["name"] == f"samsara-{agent_name}"

        # developer_instructions must be present and non-empty
        instructions = parsed["developer_instructions"]
        assert len(instructions.strip()) > 0, (
            f"Agent '{agent_name}' produced empty developer_instructions"
        )

    @pytest.mark.parametrize("agent_name", SAMSARA_AGENTS)
    def test_real_agent_name_matches_dispatch_format(self, agent_name):
        # Agent name must match format: samsara-{stem}
        agent_path = AGENTS_DIR / f"{agent_name}.md"
        if not agent_path.exists():
            pytest.skip(f"Agent file not found: {agent_path}")

        converter = AgentConverter()
        template = get_codex_template()
        naming = make_naming()

        full_text = agent_path.read_text(encoding="utf-8")

        result = converter.convert_from_text(
            source_text=full_text,
            source_path=agent_path,
            rules=[],
            naming=naming,
            template=template,
        )

        expected_name = f"samsara-{agent_name}"
        assert result.agent_name == expected_name, (
            f"Dispatch name mismatch for '{agent_name}': "
            f"expected '{expected_name}', got '{result.agent_name}'"
        )


# ---------------------------------------------------------------------------
# Transformation rule application tests
# ---------------------------------------------------------------------------


class TestRuleApplication:
    def test_body_rules_applied_before_template_render(self):
        # Rules must transform body before it is embedded in TOML.
        converter = AgentConverter()
        template = get_codex_template()
        naming = make_naming()
        rules = [
            make_rule("dispatch-rule", match="invoke samsara:", replace="use agent "),
        ]

        body = "When needed, invoke samsara:code-reviewer for review."
        source_path = Path("/fake/agent/dispatch-agent.md")

        result = converter.convert(
            body=body,
            source_path=source_path,
            rules=rules,
            naming=naming,
            template=template,
        )

        assert "invoke samsara:" not in result.transformed_body, (
            "Dispatch syntax was not transformed"
        )
        assert "use agent " in result.transformed_body

    def test_transformed_body_appears_in_toml(self):
        # Transformed body (post-rules) must be what appears in developer_instructions.
        converter = AgentConverter()
        template = get_codex_template()
        naming = make_naming()
        rules = [
            make_rule("marker", match="BEFORE", replace="AFTER"),
        ]

        body = "Text with BEFORE marker."
        source_path = Path("/fake/agent/marker-agent.md")

        result = converter.convert(
            body=body,
            source_path=source_path,
            rules=rules,
            naming=naming,
            template=template,
        )

        parsed = tomllib.loads(result.toml_content)
        instructions = parsed["developer_instructions"]
        assert "AFTER" in instructions, "Transformed body not used in TOML"
        assert "BEFORE" not in instructions, "Pre-transformation body leaked into TOML"

    def test_frontmatter_rules_not_applied_to_body(self):
        # A frontmatter-scoped rule must NOT alter body content.
        converter = AgentConverter()
        template = get_codex_template()
        naming = make_naming()
        rules = [
            make_rule(
                "fm-rule",
                match="model: sonnet",
                replace="model: gpt",
                scope="frontmatter",
            ),
        ]

        body = "This body mentions model: sonnet in its text."
        source_path = Path("/fake/agent/scope-agent.md")

        result = converter.convert(
            body=body,
            source_path=source_path,
            rules=rules,
            naming=naming,
            template=template,
        )

        # Frontmatter rule must not have changed the body
        assert "model: sonnet" in result.transformed_body, (
            "Frontmatter-scoped rule modified the body -- scope isolation broken"
        )


# ---------------------------------------------------------------------------
# Source path tests
# ---------------------------------------------------------------------------


class TestSourcePathInOutput:
    def test_source_path_appears_in_toml_comment(self):
        # The source path should appear in the TOML header comment.
        converter = AgentConverter()
        template = get_codex_template()
        naming = make_naming()

        source_path = Path("/fake/agent/path-agent.md")
        body = "Body content."

        result = converter.convert(
            body=body,
            source_path=source_path,
            rules=[],
            naming=naming,
            template=template,
        )

        assert str(source_path) in result.toml_content, (
            "source_path not present in TOML output"
        )
