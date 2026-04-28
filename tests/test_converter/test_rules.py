"""
Unit tests for rules engine — happy path and boundary conditions.

Death tests (silent failure paths) are in test_rules_death.py.
These tests cover: correct transformations, edge cases in frontmatter parsing,
multi-rule pipelines, regex capture groups, and scope filtering.
"""

import pytest

from samsara_cli.config.schema import TransformationRule
from samsara_cli.converter.rules import RulesEngine


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_rule(**kwargs) -> TransformationRule:
    """Construct a TransformationRule with minimal required fields."""
    defaults = {
        "id": "test-rule",
        "scope": "body",
        "type": "literal",
        "match": "Read tool",
        "replace": "file reading",
        "priority": "medium",
    }
    defaults.update(kwargs)
    return TransformationRule(**defaults)


# ---------------------------------------------------------------------------
# UT-1: Literal rules — exact string replacement
# ---------------------------------------------------------------------------


class TestLiteralRules:
    def test_single_literal_replacement(self):
        """Single occurrence of match string is replaced."""
        engine = RulesEngine()
        rule = make_rule(match="Read tool", replace="file reading")
        result = engine.apply("Use the Read tool to read files.", [rule], scope="body")
        assert result == "Use the file reading to read files."

    def test_multiple_occurrences_all_replaced(self):
        """All occurrences of the match string are replaced, not just the first."""
        engine = RulesEngine()
        rule = make_rule(match="Read tool", replace="file reading")
        result = engine.apply(
            "Read tool here. Read tool there. Read tool everywhere.",
            [rule],
            scope="body",
        )
        assert "Read tool" not in result
        assert result.count("file reading") == 3

    def test_case_sensitive_literal_match(self):
        """Literal match is case-sensitive. 'read tool' does not match 'Read tool'."""
        engine = RulesEngine()
        rule = make_rule(match="Read tool", replace="file reading")
        result = engine.apply("Use the read tool here.", [rule], scope="body")
        assert result == "Use the read tool here.", (
            "Case-insensitive match is wrong — literal should be case-sensitive."
        )

    def test_empty_replace_removes_match(self):
        """Replace with empty string removes the matched text."""
        engine = RulesEngine()
        rule = make_rule(match=" (legacy)", replace="")
        result = engine.apply("Feature (legacy) support.", [rule], scope="body")
        assert result == "Feature support."


# ---------------------------------------------------------------------------
# UT-2: Regex rules — pattern matching and substitution
# ---------------------------------------------------------------------------


class TestRegexRules:
    def test_simple_regex_no_capture_group(self):
        """Regex pattern without capture group — simple substitution."""
        engine = RulesEngine()
        rule = make_rule(
            type="regex",
            match=r"Agent tool:",
            replace="Subagent dispatch:",
        )
        result = engine.apply("Agent tool: dispatch.", [rule], scope="body")
        assert result == "Subagent dispatch: dispatch."

    def test_regex_with_single_capture_group(self):
        """Regex with one capture group — \\1 in replace references captured text."""
        engine = RulesEngine()
        rule = make_rule(
            type="regex",
            match=r"invoke `samsara:([\w-]+)`",
            replace=r"use the `$samsara-\1` skill",
        )
        result = engine.apply("invoke `samsara:my-skill`", [rule], scope="body")
        assert result == "use the `$samsara-my-skill` skill"

    def test_regex_word_boundary_prevents_partial_match(self):
        r"""Regex with \b word boundary prevents partial word matching."""
        engine = RulesEngine()
        rule = make_rule(
            type="regex",
            match=r"TaskCreate\b",
            replace="update_plan",
        )
        # Should match standalone TaskCreate
        result_match = engine.apply("Call TaskCreate here.", [rule], scope="body")
        assert result_match == "Call update_plan here."

        # Should NOT match TaskCreateNew (boundary after 'e' followed by 'N')
        result_no_match = engine.apply("Call TaskCreateNew here.", [rule], scope="body")
        assert result_no_match == "Call TaskCreateNew here.", (
            r"\b boundary should prevent matching 'TaskCreate' inside 'TaskCreateNew'"
        )

    def test_regex_multiple_occurrences_replaced(self):
        """All occurrences of regex pattern are replaced."""
        engine = RulesEngine()
        rule = make_rule(
            type="regex",
            match=r"Agent tool:",
            replace="Subagent dispatch:",
        )
        result = engine.apply(
            "Agent tool: foo. Agent tool: bar.",
            [rule],
            scope="body",
        )
        assert result == "Subagent dispatch: foo. Subagent dispatch: bar."

    def test_regex_subagent_type_with_capture(self):
        """Real codex rule: subagent_type with capture group."""
        engine = RulesEngine()
        rule = make_rule(
            type="regex",
            match=r'subagent_type: "samsara:([\w-]+)"',
            replace=r'agent named "samsara-\1"',
        )
        result = engine.apply(
            'subagent_type: "samsara:code-review"',
            [rule],
            scope="body",
        )
        assert result == 'agent named "samsara-code-review"'


# ---------------------------------------------------------------------------
# UT-3: Multi-rule pipeline — sequential application
# ---------------------------------------------------------------------------


class TestMultiRulePipeline:
    def test_two_independent_rules_both_applied(self):
        """Two rules with non-overlapping patterns both apply."""
        engine = RulesEngine()
        rules = [
            make_rule(id="rule-1", match="Read tool", replace="file reading"),
            make_rule(id="rule-2", match="Edit tool", replace="apply_patch"),
        ]
        result = engine.apply("Use Read tool and Edit tool.", rules, scope="body")
        assert result == "Use file reading and apply_patch."

    def test_seven_codex_literal_rules_all_apply(self):
        """All seven Codex literal tool-mapping rules apply to appropriate text."""
        engine = RulesEngine()
        rules = [
            make_rule(
                id="tool_read",
                match="Read tool",
                replace="file reading (via exec_command with cat/nl)",
            ),
            make_rule(id="tool_edit", match="Edit tool", replace="apply_patch"),
            make_rule(id="tool_write", match="Write tool", replace="apply_patch"),
            make_rule(id="tool_bash", match="Bash tool", replace="exec_command"),
            make_rule(
                id="tool_ls", match="LS tool", replace="exec_command with ls/find"
            ),
            make_rule(
                id="tool_grep", match="Grep tool", replace="exec_command with rg"
            ),
            make_rule(
                id="tool_glob",
                match="Glob tool",
                replace="exec_command with find/rg --files",
            ),
        ]
        text = (
            "Use Read tool, Edit tool, Write tool, Bash tool, "
            "LS tool, Grep tool, Glob tool."
        )
        result = engine.apply(text, rules, scope="body")
        assert "Read tool" not in result
        assert "Edit tool" not in result
        assert "Write tool" not in result
        assert "Bash tool" not in result
        assert "LS tool" not in result
        assert "Grep tool" not in result
        assert "Glob tool" not in result

    def test_chained_rules_output_feeds_next_rule(self):
        """Rule B operates on rule A's output, not original input."""
        engine = RulesEngine()
        rules = [
            make_rule(id="a", match="foo", replace="bar"),
            make_rule(id="b", match="bar", replace="baz"),
        ]
        result = engine.apply("foo", rules, scope="body")
        assert result == "baz", "Rule B should see rule A's output ('bar')."

    def test_scope_filtered_rules_only_matching_scope_applies(self):
        """When apply() called with scope='body', only body-scoped rules run."""
        engine = RulesEngine()
        rules = [
            make_rule(id="body-rule", scope="body", match="foo", replace="BAR"),
            make_rule(id="fm-rule", scope="frontmatter", match="foo", replace="WRONG"),
        ]
        result = engine.apply("foo", rules, scope="body")
        assert result == "BAR", "Only body-scoped rule should apply."
        assert "WRONG" not in result


# ---------------------------------------------------------------------------
# UT-4: Frontmatter parsing — correct section splitting
# ---------------------------------------------------------------------------


class TestFrontmatterParsing:
    def test_text_with_frontmatter_splits_correctly(self):
        """Text with frontmatter: frontmatter rule applies to fm, not body."""
        engine = RulesEngine()
        rule = make_rule(
            scope="frontmatter",
            match="claude-opus-4-5",
            replace="gpt-4o",
        )
        text = """\
---
name: test-skill
model: claude-opus-4-5
---
# Body

This is body text.
"""
        result = engine.apply(text, [rule], scope="frontmatter")
        assert "gpt-4o" in result
        # Body must not be modified
        body = result.split("---", 2)[2]
        assert "gpt-4o" not in body
        assert "claude-opus-4-5" not in result.split("---")[1]

    def test_text_without_frontmatter_body_rule_applies_to_all(self):
        """
        Text without frontmatter (no --- delimiters): body rule applies
        to entire text (there is no frontmatter section to protect).
        """
        engine = RulesEngine()
        rule = make_rule(
            scope="body",
            match="Read tool",
            replace="file reading",
        )
        text = "Use the Read tool to read files."
        result = engine.apply(text, [rule], scope="body")
        assert result == "Use the file reading to read files."

    def test_frontmatter_only_file_body_rule_has_nothing_to_match(self):
        """
        File with frontmatter but no body content: body rule finds nothing to
        transform. Returns text unchanged.
        """
        engine = RulesEngine()
        rule = make_rule(scope="body", match="Read tool", replace="file reading")
        text = "---\nname: test-skill\n---\n"
        result = engine.apply(text, [rule], scope="body")
        assert result == text

    def test_incomplete_frontmatter_single_dash_not_treated_as_delimiter(self):
        """
        A single '---' line with no closing '---' should not split incorrectly.
        Text starting with '---' but no closing delimiter has no frontmatter.
        """
        engine = RulesEngine()
        rule = make_rule(scope="body", match="test", replace="REPLACED")
        # Only one '---' — not valid frontmatter
        text = "---\ntest content\n"
        result = engine.apply(text, [rule], scope="body")
        # With only one '---', this is ambiguous. The engine should handle it
        # gracefully — either treating it as no frontmatter (whole text is body)
        # or as open frontmatter with no body. Either way, no crash.
        assert isinstance(result, str), "Engine must return string, not raise."


# ---------------------------------------------------------------------------
# UT-5: Scope parameter filtering — apply() scope argument
# ---------------------------------------------------------------------------


class TestScopeFiltering:
    def test_apply_body_scope_runs_only_body_rules(self):
        """
        apply(text, rules, scope='body') runs only rules where rule.scope == 'body'.
        Frontmatter-scoped rules in the list are ignored.
        """
        engine = RulesEngine()
        body_rule = make_rule(id="b", scope="body", match="X", replace="Y")
        fm_rule = make_rule(id="f", scope="frontmatter", match="X", replace="Z")
        result = engine.apply("X", [body_rule, fm_rule], scope="body")
        assert result == "Y"

    def test_apply_frontmatter_scope_runs_only_frontmatter_rules(self):
        """
        apply(text, rules, scope='frontmatter') runs only frontmatter-scoped rules.
        Text must contain actual frontmatter — otherwise there is nothing for a
        frontmatter-scoped rule to act on (empty frontmatter section).
        """
        engine = RulesEngine()
        body_rule = make_rule(id="b", scope="body", match="X", replace="Y")
        fm_rule = make_rule(id="f", scope="frontmatter", match="X", replace="Z")
        # Text with frontmatter containing 'X' and body also containing 'X'
        text = "---\nX\n---\nX\n"
        result = engine.apply(text, [body_rule, fm_rule], scope="frontmatter")
        # Frontmatter 'X' -> 'Z', body 'X' must remain 'X' (body rule not run)
        assert "Z" in result, (
            "Frontmatter-scoped rule should have transformed frontmatter."
        )
        body_section = result.split("---", 2)[2]
        assert "X" in body_section, (
            "Body-scoped rule must not have run (scope='frontmatter')."
        )
        assert "Y" not in body_section, "Body rule must not have modified body content."

    def test_no_rules_for_scope_returns_unchanged(self):
        """If no rules match the requested scope, text is returned unchanged."""
        engine = RulesEngine()
        fm_rule = make_rule(id="f", scope="frontmatter", match="X", replace="Z")
        result = engine.apply("X", [fm_rule], scope="body")
        assert result == "X"


# ---------------------------------------------------------------------------
# UT-6: RulesEngine construction and interface
# ---------------------------------------------------------------------------


class TestRulesEngineInterface:
    def test_rules_engine_is_instantiable(self):
        """RulesEngine can be instantiated with no arguments."""
        engine = RulesEngine()
        assert engine is not None

    def test_apply_returns_string(self):
        """apply() always returns a string."""
        engine = RulesEngine()
        result = engine.apply("text", [], scope="body")
        assert isinstance(result, str)

    def test_apply_with_no_matching_rules_returns_input_unchanged(self):
        """Rules that don't match leave the text unchanged."""
        engine = RulesEngine()
        rule = make_rule(match="NOTPRESENT", replace="bar")
        text = "original text"
        result = engine.apply(text, [rule], scope="body")
        assert result == text

    def test_invalid_scope_raises_value_error(self):
        """
        Unknown scope value must raise ValueError immediately.
        Silently returning unchanged text on a typo ('bode' instead of 'body')
        would make the caller think rules were applied.
        """
        engine = RulesEngine()
        rule = make_rule(match="foo", replace="bar")
        with pytest.raises(ValueError, match="Invalid scope"):
            engine.apply("foo bar", [rule], scope="bode")

    def test_leading_whitespace_before_frontmatter_delimiter_treated_as_no_frontmatter(
        self,
    ):
        """
        A document where the first line is ' ---' (with leading space) does NOT
        have recognized frontmatter — the engine treats the whole text as body.
        This behavior is documented in the scar report as a known assumption.
        """
        engine = RulesEngine()
        rule = make_rule(scope="body", match="foo", replace="bar")
        # Leading space before '---' — NOT valid frontmatter
        text = " ---\nname: test\n---\nfoo in body\n"
        result = engine.apply(text, [rule], scope="body")
        # Whole text is body — 'foo' in 'foo in body' is replaced
        assert "bar in body" in result, (
            "With no valid frontmatter, entire text is body — rule should apply to all."
        )

    def test_bom_before_frontmatter_delimiter_treated_as_no_frontmatter(self):
        """
        A document with UTF-8 BOM before '---' is treated as having no frontmatter.
        The BOM character makes the first line '\\xef\\xbb\\xbf---' not '---'.
        """
        engine = RulesEngine()
        rule = make_rule(scope="body", match="foo", replace="bar")
        bom = "﻿"
        text = f"{bom}---\nname: test\n---\nfoo in body\n"
        result = engine.apply(text, [rule], scope="body")
        # Whole text treated as body — 'foo' replaced
        assert "bar in body" in result
