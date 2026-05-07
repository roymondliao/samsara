# Death tests for agent.py -- AgentConverter.
#
# These tests target silent failure paths first:
# - TOML triple-quote escaping: body containing triple-double-quotes breaks TOML parse
# - Tool reference transformation: rules not applied means wrong tool names in output
# - TOML parseability: string concatenation can produce syntactically invalid TOML
# - Agent name dispatch mismatch: name in TOML does not match skill dispatch reference
# - Large body (>8KB): no truncation or silent clipping
#
# A death test passes only if the implementation prevents the named failure.
# If the failure is not prevented, the test must catch it (red = implementation needed).
#
# Death case sources:
# - Task 4 spec: TOML triple-quote escaping, tool reference application, TOML parse
#   validation, name convention matching, large body
# - Architecture Context death case 2: unconverted tool reference breaks dispatch chain
# - Architecture Context death case 3: agent name mismatch breaks skill dispatch

import tomllib

import pytest
from pathlib import Path
from jinja2 import Template

from samsara_cli.config.schema import TransformationRule, NamingConfig
from samsara_cli.converter.agent import AgentConverter


# ---------------------------------------------------------------------------
# Helpers -- minimal rule and naming config for tests
# ---------------------------------------------------------------------------


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


def get_codex_template() -> Template:
    from samsara_cli.config.template_env import get_template_env

    env = get_template_env("codex")
    return env.get_template("agent.toml.j2")


# ---------------------------------------------------------------------------
# DEATH TEST 1: Body containing triple-double-quotes must not break TOML parsing
#
# If the body contains a triple-double-quote sequence, it terminates the TOML
# multiline string prematurely. The resulting TOML is syntactically invalid.
# tomllib.loads() will raise a TOMLDecodeError.
#
# Without proper escaping in AgentConverter, this silently produces a broken
# .toml file. The first human to discover it is whoever runs Codex and sees
# the agent fail to load -- after deployment.
# ---------------------------------------------------------------------------


class TestTripleQuoteEscaping:
    def test_body_with_triple_quotes_produces_parseable_toml(self):
        # Body containing triple-double-quotes must be escaped so output TOML parses correctly.
        converter = AgentConverter()
        template = get_codex_template()
        naming = make_naming()

        source_path = Path("/fake/agent/triple-quote-agent.md")
        # Construct body containing triple-double-quote literal
        tq = '"""'
        body_with_triple_quotes = (
            "You are an agent.\n"
            "```python\nresult = f" + tq + "hello {name}" + tq + "\n```\n"
            "This demonstrates the issue."
        )

        result = converter.convert(
            body=body_with_triple_quotes,
            source_path=source_path,
            rules=[],
            naming=naming,
            template=template,
        )

        # The output MUST parse as valid TOML -- this is the critical assertion
        try:
            parsed = tomllib.loads(result.toml_content)
        except Exception as e:
            pytest.fail(
                "TOML parse failed after conversion -- triple-quote escaping not applied. "
                f"Error: {e}"
            )

        # The instructions must be present (not empty due to truncation)
        agent_section = parsed
        assert "developer_instructions" in agent_section, (
            "developer_instructions missing from parsed TOML -- body was truncated at triple-quote"
        )
        # The content after the triple quote should survive
        assert "demonstrates the issue" in agent_section["developer_instructions"], (
            "Body content after triple-quote was silently truncated"
        )

    def test_body_with_multiple_triple_quote_sequences(self):
        # Body with multiple triple-double-quote occurrences -- all must be escaped.
        converter = AgentConverter()
        template = get_codex_template()
        naming = make_naming()

        source_path = Path("/fake/agent/multi-triple-agent.md")
        tq = '"""'
        body = "First " + tq + "\nsecond " + tq + "\nthird " + tq

        result = converter.convert(
            body=body,
            source_path=source_path,
            rules=[],
            naming=naming,
            template=template,
        )

        try:
            parsed = tomllib.loads(result.toml_content)
        except Exception as e:
            pytest.fail(f"TOML parse failed with multiple triple-quotes: {e}")

        instructions = parsed["developer_instructions"]
        # Content must survive (not be silently dropped)
        assert "First" in instructions, "Content before first triple-quote was lost"
        assert "second" in instructions, "Content around second triple-quote was lost"
        assert "third" in instructions, "Content around third triple-quote was lost"


# ---------------------------------------------------------------------------
# DEATH TEST 2: Tool references must have rules applied -- not copied verbatim
#
# If rules are not applied to the body, agent instructions will contain
# Claude Code-specific tool names (Read, Grep, Glob, Bash) that do not exist
# in Codex. The agent will fail at runtime when it tries to invoke these tools.
# The failure is silent at conversion time -- the .toml file looks fine.
# ---------------------------------------------------------------------------


class TestToolReferenceTransformation:
    def test_tool_reference_is_transformed_when_rule_matches(self):
        # A body-scoped rule targeting "Read tool" must transform it in the output.
        converter = AgentConverter()
        template = get_codex_template()
        naming = make_naming()
        rules = [
            make_rule("read-tool", match="Read tool", replace="file_read tool"),
        ]

        source_path = Path("/fake/agent/tool-agent.md")
        body = "Use the Read tool to access files."

        result = converter.convert(
            body=body,
            source_path=source_path,
            rules=rules,
            naming=naming,
            template=template,
        )

        assert "file_read tool" in result.toml_content, (
            "Tool reference rule was not applied -- 'Read tool' still verbatim in output"
        )
        # Verify the original did NOT survive unreplaced in the transformed body
        assert "Read tool" not in result.transformed_body, (
            "Original tool reference still present in transformed body -- rule was not applied"
        )

    def test_no_rule_means_body_is_copied_verbatim(self):
        # Without rules, body passes through unchanged -- this is the baseline.
        converter = AgentConverter()
        template = get_codex_template()
        naming = make_naming()

        source_path = Path("/fake/agent/verbatim-agent.md")
        body = "Use the Read tool to access files."

        result = converter.convert(
            body=body,
            source_path=source_path,
            rules=[],
            naming=naming,
            template=template,
        )

        # Without rules, original content should survive in transformed body
        assert "Read tool" in result.transformed_body, (
            "Body was altered without any rules -- transformation should be a no-op with empty rules"
        )

    def test_multiple_tool_references_all_transformed(self):
        # When multiple tool rules exist, all must fire -- partial conversion is dangerous.
        converter = AgentConverter()
        template = get_codex_template()
        naming = make_naming()
        rules = [
            make_rule("read-tool", match="Read", replace="file_read"),
            make_rule("grep-tool", match="Grep", replace="search"),
        ]

        body = "Use Read and Grep and Bash."
        source_path = Path("/fake/agent/multi-tool-agent.md")

        result = converter.convert(
            body=body,
            source_path=source_path,
            rules=rules,
            naming=naming,
            template=template,
        )

        # Both rules must have fired
        assert "file_read" in result.transformed_body, "Read rule did not fire"
        assert "search" in result.transformed_body, "Grep rule did not fire"
        # Bash was not in any rule -- must survive unchanged
        assert "Bash" in result.transformed_body, "Bash was unexpectedly transformed"


# ---------------------------------------------------------------------------
# DEATH TEST 3: Generated .toml must parse with a TOML parser
#
# String concatenation approaches can produce TOML that looks correct to the
# eye but fails to parse (e.g., unbalanced quotes, wrong section nesting).
# The only way to verify structural correctness is to actually parse the output.
# A broken .toml deployed to Codex causes silent agent loading failures.
# ---------------------------------------------------------------------------


class TestTOMLParseability:
    def test_basic_agent_output_parses_as_valid_toml(self):
        # Minimal conversion must produce parseable TOML.
        converter = AgentConverter()
        template = get_codex_template()
        naming = make_naming()

        source_path = Path("/fake/agent/basic-agent.md")
        body = "You are a basic agent."

        result = converter.convert(
            body=body,
            source_path=source_path,
            rules=[],
            naming=naming,
            template=template,
        )

        try:
            parsed = tomllib.loads(result.toml_content)
        except Exception as e:
            pytest.fail(f"Basic agent output is not valid TOML: {e}")

        assert "agent" not in parsed
        assert "name" in parsed
        assert "description" in parsed
        assert "developer_instructions" in parsed

    def test_multiline_body_with_special_chars_parses_as_toml(self):
        # Body with special chars (backslashes, single quotes, mixed) must parse.
        converter = AgentConverter()
        template = get_codex_template()
        naming = make_naming()

        source_path = Path("/fake/agent/special-agent.md")
        body = (
            "Line with backslash: C:\\Users\\agent\n"
            "Line with single quotes: 'important'\n"
            "Line with brackets: [section]\n"
            "Line with equals: key=value\n"
            "Line with hash: # comment marker\n"
        )

        result = converter.convert(
            body=body,
            source_path=source_path,
            rules=[],
            naming=naming,
            template=template,
        )

        try:
            tomllib.loads(result.toml_content)
        except Exception as e:
            pytest.fail(f"TOML parse failed with special chars in body: {e}")

    def test_agent_name_is_present_in_parsed_toml(self):
        # The agent name must be accessible via TOML parser -- not just a string match.
        converter = AgentConverter()
        template = get_codex_template()
        naming = make_naming(prefix="samsara", sep="-")

        source_path = Path("/fake/agent/my-agent.md")
        body = "You are my agent."

        result = converter.convert(
            body=body,
            source_path=source_path,
            rules=[],
            naming=naming,
            template=template,
        )

        parsed = tomllib.loads(result.toml_content)
        assert parsed["name"] == "samsara-my-agent", (
            f"Agent name in TOML does not match expected 'samsara-my-agent'. "
            f"Got: {parsed['agent'].get('name')!r}"
        )


# ---------------------------------------------------------------------------
# DEATH TEST 4: Agent name must match naming convention used in skill dispatch
#
# If the agent name in the .toml does not match the name a skill uses when
# dispatching (e.g., "invoke samsara:code-reviewer"), the agent is
# unreachable. The skill runs, finds no matching agent, and fails or falls
# back silently.
# ---------------------------------------------------------------------------


class TestAgentNameDispatchConsistency:
    def test_agent_name_follows_prefix_separator_convention(self):
        # Generated name must be: {prefix}{separator}{filename-stem}
        converter = AgentConverter()
        template = get_codex_template()
        naming = make_naming(prefix="samsara", sep="-")

        source_path = Path("/fake/agent/code-reviewer.md")
        body = "You are a reviewer."

        result = converter.convert(
            body=body,
            source_path=source_path,
            rules=[],
            naming=naming,
            template=template,
        )

        assert result.agent_name == "samsara-code-reviewer", (
            f"Agent name does not follow convention. Expected 'samsara-code-reviewer', "
            f"got {result.agent_name!r}"
        )

    def test_all_six_samsara_agents_produce_expected_names(self):
        # All 6 agent filenames must generate names matching their expected dispatch names.
        converter = AgentConverter()
        template = get_codex_template()
        naming = make_naming(prefix="samsara", sep="-")

        expected_names = {
            "code-quality-reviewer": "samsara-code-quality-reviewer",
            "code-reviewer": "samsara-code-reviewer",
            "implementer": "samsara-implementer",
            "infra-explorer": "samsara-infra-explorer",
            "structure-explorer": "samsara-structure-explorer",
            "yin-explorer": "samsara-yin-explorer",
        }

        body = "You are an agent."
        for stem, expected in expected_names.items():
            source_path = Path(f"/fake/agent/{stem}.md")
            result = converter.convert(
                body=body,
                source_path=source_path,
                rules=[],
                naming=naming,
                template=template,
            )
            assert result.agent_name == expected, (
                f"Name mismatch for {stem}: expected {expected!r}, got {result.agent_name!r}"
            )
            # Confirm the name is in the TOML too
            parsed = tomllib.loads(result.toml_content)
            assert parsed["name"] == expected, f"Name in TOML does not match for {stem}"

    def test_custom_separator_is_applied(self):
        # Naming config separator must be used -- changing separator changes all dispatch names.
        converter = AgentConverter()
        template = get_codex_template()
        naming = make_naming(prefix="samsara", sep="_")  # underscore separator

        source_path = Path("/fake/agent/my-agent.md")
        body = "Body text."

        result = converter.convert(
            body=body,
            source_path=source_path,
            rules=[],
            naming=naming,
            template=template,
        )

        # With separator="_", name should be "samsara_my-agent" (prefix sep stem)
        assert result.agent_name == "samsara_my-agent", (
            f"Custom separator not applied. Expected 'samsara_my-agent', got {result.agent_name!r}"
        )


# ---------------------------------------------------------------------------
# DEATH TEST 5: Large body (>8KB) must be handled without truncation
#
# Some samsara agents are large (code-quality-reviewer.md is ~16KB).
# A naive implementation might truncate at a buffer boundary, produce a
# corrupted TOML string, or silently clip instructions. The agent would
# appear to convert but would have incomplete instructions.
# The damage: the deployed agent is missing half its instructions with no error.
# ---------------------------------------------------------------------------


class TestLargeBodyHandling:
    def test_body_exceeding_8kb_is_fully_preserved(self):
        # A body >8KB must be preserved in full -- no truncation at TOML output.
        converter = AgentConverter()
        template = get_codex_template()
        naming = make_naming()

        source_path = Path("/fake/agent/large-agent.md")
        # Generate a deterministic body larger than 8KB
        # Include distinctive markers at beginning, middle, and end
        section = "A" * 500 + " -- marker\n"
        body_parts = ["START_MARKER\n"]
        for i in range(20):
            body_parts.append(f"Section {i}: {section}")
        body_parts.append("END_MARKER\n")
        body = "".join(body_parts)

        assert len(body.encode("utf-8")) > 8192, (
            "Test precondition: body must exceed 8KB"
        )

        result = converter.convert(
            body=body,
            source_path=source_path,
            rules=[],
            naming=naming,
            template=template,
        )

        # Verify TOML parses
        try:
            parsed = tomllib.loads(result.toml_content)
        except Exception as e:
            pytest.fail(f"Large body produced invalid TOML: {e}")

        instructions = parsed["developer_instructions"]

        # Both start and end markers must survive
        assert "START_MARKER" in instructions, (
            "START_MARKER was lost -- body truncated at beginning"
        )
        assert "END_MARKER" in instructions, (
            "END_MARKER was lost -- body truncated at end"
        )

        # All 20 section markers must survive
        for i in range(20):
            assert f"Section {i}:" in instructions, (
                f"Section {i} was lost -- body truncated mid-content"
            )

    def test_code_quality_reviewer_real_file_converts_without_truncation(self):
        # The real code-quality-reviewer.md (>8KB) must convert cleanly.
        real_path = Path(
            "/Users/yuyu_liao/personal/samsara/.claude/worktrees/multi-platform-support"
            "/agents/code-quality-reviewer.md"
        )
        if not real_path.exists():
            pytest.skip("Real agent file not available in this environment")

        converter = AgentConverter()
        template = get_codex_template()
        naming = make_naming()

        full_text = real_path.read_text(encoding="utf-8")
        # Parse out body (strip frontmatter)
        body = _strip_frontmatter(full_text)

        assert len(body.encode("utf-8")) > 8192, (
            "Test precondition: code-quality-reviewer body must exceed 8KB"
        )

        result = converter.convert(
            body=body,
            source_path=real_path,
            rules=[],
            naming=naming,
            template=template,
        )

        try:
            parsed = tomllib.loads(result.toml_content)
        except Exception as e:
            pytest.fail(f"Real large agent produced invalid TOML: {e}")

        instructions = parsed["developer_instructions"]
        # The file must not be empty
        assert len(instructions) > 1000, (
            f"instructions suspiciously short ({len(instructions)} chars) -- possible truncation"
        )


def _strip_frontmatter(text: str) -> str:
    # Helper: strip YAML frontmatter from agent markdown file.
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].rstrip("\r\n") != "---":
        return text
    for i in range(1, len(lines)):
        if lines[i].rstrip("\r\n") == "---":
            return "".join(lines[i + 1 :])
    return text


# ---------------------------------------------------------------------------
# DEATH TEST 6: Missing required template variable must raise, not silently render empty
#
# StrictUndefined is configured in template_env.py. If the converter fails to
# pass a required variable (e.g., name, developer_instructions, source_path),
# Jinja2 must raise UndefinedError -- not silently render an empty string.
# An agent with empty developer_instructions is silently broken.
# ---------------------------------------------------------------------------


class TestMissingTemplateVariableRaises:
    def test_convert_raises_on_empty_body(self):
        # Empty body should raise -- not produce an agent with empty instructions.
        converter = AgentConverter()
        template = get_codex_template()
        naming = make_naming()
        source_path = Path("/fake/agent/empty-agent.md")

        with pytest.raises((ValueError, Exception)):
            converter.convert(
                body="",
                source_path=source_path,
                rules=[],
                naming=naming,
                template=template,
            )
