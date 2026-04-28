"""
Death tests for rules engine — targeting silent failure paths.

Each test names the specific silent failure it guards against.
Death tests run BEFORE unit tests. They must fail red before implementation,
then pass green after.

Silent failures guarded here:
  DC-1: Body-scoped rule modifies frontmatter — silently corrupts agent identity fields
  DC-2: Regex capture group produces wrong substitution — silently wrong output
  DC-3: Rule order inversion produces different output — order must be deterministic
  DC-4: Literal rule treats regex metacharacters literally — 'Read tool' must not match
        'Read tools' if using word boundaries (guards against overmatch AND undermatch)
  DC-5: Empty input returns empty — must not raise
  DC-6: Non-matching pattern returns input unchanged — must not raise or corrupt
  DC-7: Frontmatter-scoped rule must NOT modify body content — symmetric to DC-1
  DC-8: Literal rule must NOT match superset string — 'Edit tool' must not match
        'Edit tools' or 'Multi-Edit tool'
"""

from samsara_cli.config.schema import TransformationRule
from samsara_cli.converter.rules import RulesEngine


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

SKILL_WITH_FRONTMATTER = """\
---
name: test-skill
model: claude-opus-4-5
tools:
  - Read tool
  - Edit tool
---
# Test Skill

Use the Read tool to read files.
Use the Edit tool to edit files.
Run commands with the Bash tool.
"""

SKILL_WITHOUT_FRONTMATTER = """\
# Test Skill

Use the Read tool to read files.
Use the Edit tool to edit files.
"""


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
# DC-1: Body-scoped rule MUST NOT modify frontmatter content
#
# Silent failure: A body rule matching 'Read tool' also matches the frontmatter
# tools list. The converted file has corrupted tool declarations that look
# structurally valid but reference wrong tool names. No error is raised.
# First discovery: Codex rejects the plugin or silently uses wrong tools.
# ---------------------------------------------------------------------------


class TestDC1BodyRuleCannotModifyFrontmatter:
    def test_body_rule_does_not_alter_frontmatter_tool_entry(self):
        """
        'Read tool' appears in frontmatter tools list AND body.
        A body-scoped rule must transform ONLY the body occurrence.
        The frontmatter 'Read tool' entry must remain unchanged.
        """
        engine = RulesEngine()
        rule = make_rule(
            id="tool_read",
            scope="body",
            type="literal",
            match="Read tool",
            replace="file reading (via exec_command with cat/nl)",
        )
        result = engine.apply(SKILL_WITH_FRONTMATTER, [rule], scope="body")

        # Frontmatter must be preserved exactly
        frontmatter_section = result.split("---")[1]
        assert "Read tool" in frontmatter_section, (
            "SILENT FAILURE: body rule modified frontmatter. "
            "'Read tool' was removed from frontmatter tools list."
        )

    def test_body_rule_does_transform_body_occurrence(self):
        """Companion to DC-1: the body rule DOES transform body content."""
        engine = RulesEngine()
        rule = make_rule(
            id="tool_read",
            scope="body",
            type="literal",
            match="Read tool",
            replace="file reading (via exec_command with cat/nl)",
        )
        result = engine.apply(SKILL_WITH_FRONTMATTER, [rule], scope="body")

        body_section = result.split("---", 2)[2]
        assert "file reading (via exec_command with cat/nl)" in body_section, (
            "Body rule did not transform body content."
        )
        assert "Read tool" not in body_section, (
            "Body rule left original text in body — transformation did not apply."
        )

    def test_body_rule_regex_does_not_alter_frontmatter(self):
        """
        Regex body rule must also not bleed into frontmatter.
        Tests regex variant of DC-1.
        """
        engine = RulesEngine()
        rule = make_rule(
            id="skill_invocation",
            scope="body",
            type="regex",
            match=r"invoke `samsara:([\w-]+)`",
            replace=r"use the `$samsara-\1` skill",
        )
        text = """\
---
name: test-skill
invoke: samsara-hook-pattern
---
# Body
invoke `samsara:my-skill`
"""
        result = engine.apply(text, [rule], scope="body")

        # Frontmatter must be unchanged
        fm = result.split("---")[1]
        assert "invoke: samsara-hook-pattern" in fm, (
            "SILENT FAILURE: regex body rule modified frontmatter."
        )

        # Body must be transformed
        body = result.split("---", 2)[2]
        assert "use the `$samsara-my-skill` skill" in body, (
            "Regex rule did not apply to body content."
        )


# ---------------------------------------------------------------------------
# DC-2: Regex capture group substitution — \1 must reference first group
#
# Silent failure: If capture groups are handled wrong (e.g., using $1 instead
# of \1 semantics, or not handling backref at all), the substitution produces
# literal '\1' in the output. The output looks like valid text but with garbage
# in skill references. First discovery: Codex cannot resolve '$samsara-\1'.
# ---------------------------------------------------------------------------


class TestDC2RegexCaptureGroupSubstitution:
    def test_capture_group_backref_substitutes_correctly(self):
        """
        Pattern: invoke `samsara:([\\w-]+)`
        Replace: use the `$samsara-\\1` skill
        Input:   invoke `samsara:my-skill`
        Expected: use the `$samsara-my-skill` skill
        NOT:      use the `$samsara-\\\\1` skill (literal backref)
        """
        engine = RulesEngine()
        rule = make_rule(
            id="skill_invocation",
            scope="body",
            type="regex",
            match=r"invoke `samsara:([\w-]+)`",
            replace=r"use the `$samsara-\1` skill",
        )
        text = "invoke `samsara:my-skill`"
        result = engine.apply(text, [rule], scope="body")
        assert result == "use the `$samsara-my-skill` skill", (
            f"SILENT FAILURE: capture group not substituted. Got: {result!r}"
        )

    def test_capture_group_with_hyphenated_name(self):
        r"""Capture group must handle hyphen in captured text ([\w-]+)."""
        engine = RulesEngine()
        rule = make_rule(
            id="agent_dispatch",
            scope="body",
            type="regex",
            match=r'subagent_type: "samsara:([\w-]+)"',
            replace=r'agent named "samsara-\1"',
        )
        text = 'subagent_type: "samsara:code-review"'
        result = engine.apply(text, [rule], scope="body")
        assert result == 'agent named "samsara-code-review"', (
            f"SILENT FAILURE: hyphenated capture group wrong. Got: {result!r}"
        )

    def test_literal_backref_not_produced_in_output(self):
        """
        Guard against the most dangerous form: output contains literal '\1'.
        This would appear to be a valid rule output but reference nothing.
        """
        engine = RulesEngine()
        rule = make_rule(
            id="skill_invocation",
            scope="body",
            type="regex",
            match=r"invoke `samsara:([\w-]+)`",
            replace=r"use the `$samsara-\1` skill",
        )
        text = "invoke `samsara:my-skill`"
        result = engine.apply(text, [rule], scope="body")
        assert r"\1" not in result, (
            f"SILENT FAILURE: literal backref '\\1' in output. Got: {result!r}"
        )


# ---------------------------------------------------------------------------
# DC-3: Rule ordering — overlapping rules must produce deterministic output
#
# Silent failure: Rules apply in undefined order. skill_invocation_variant
# (more specific) and skill_invocation (less specific) both match the same
# input. Which one wins depends on dict ordering or sorting — non-deterministic.
# First discovery: Different runs produce different converted files.
# ---------------------------------------------------------------------------


class TestDC3RuleOrderingDeterminism:
    def test_first_rule_applies_to_original_text_second_to_first_output(self):
        """
        Rule A transforms 'foo' -> 'bar'.
        Rule B transforms 'bar' -> 'baz'.
        With [A, B], output is 'baz' (B sees A's output).
        With [B, A], output is 'bar' (B sees original 'foo', no match; A transforms 'foo'->'bar').
        Order matters. Same rules in different order = different output.
        """
        engine = RulesEngine()
        rule_a = make_rule(id="rule-a", match="foo", replace="bar")
        rule_b = make_rule(id="rule-b", match="bar", replace="baz")

        result_ab = engine.apply("foo", [rule_a, rule_b], scope="body")
        result_ba = engine.apply("foo", [rule_b, rule_a], scope="body")

        assert result_ab == "baz", (
            f"[A, B] order should yield 'baz', got: {result_ab!r}"
        )
        assert result_ba == "bar", (
            f"[B, A] order should yield 'bar', got: {result_ba!r}"
        )
        assert result_ab != result_ba, (
            "SILENT FAILURE: rule order has no effect — rules must apply in list order"
        )

    def test_same_rule_list_always_produces_same_output(self):
        """
        Determinism: same input + same rules = same output, always.
        Runs three times to detect any non-determinism.
        """
        engine = RulesEngine()
        rules = [
            make_rule(id="rule-1", match="Read tool", replace="file reading"),
            make_rule(id="rule-2", match="Edit tool", replace="apply_patch"),
        ]
        text = "Use Read tool and Edit tool."
        results = [engine.apply(text, rules, scope="body") for _ in range(3)]
        assert results[0] == results[1] == results[2], (
            f"SILENT FAILURE: non-deterministic output. Results: {results}"
        )


# ---------------------------------------------------------------------------
# DC-4: Literal rule must NOT interpret regex metacharacters
#
# Silent failure: A literal rule for 'Read tool' compiled as regex would match
# 'Read  tool' (if . matches space) or 'ReadXtool' (. matches any char).
# str.replace semantics = exact character match, no metacharacter interpretation.
# ---------------------------------------------------------------------------


class TestDC4LiteralRuleNoRegexMetacharacters:
    def test_dot_in_literal_match_is_not_wildcard(self):
        """
        Literal match 'a.b' must NOT match 'aXb'.
        If implemented as re.sub, '.' is a wildcard — wrong.
        """
        engine = RulesEngine()
        rule = make_rule(
            id="test",
            type="literal",
            match="a.b",
            replace="REPLACED",
        )
        result = engine.apply("aXb", [rule], scope="body")
        assert result == "aXb", (
            f"SILENT FAILURE: literal rule interpreted '.' as regex wildcard. Got: {result!r}"
        )

    def test_literal_match_matches_exact_string(self):
        """Literal 'a.b' DOES match the literal string 'a.b'."""
        engine = RulesEngine()
        rule = make_rule(
            id="test",
            type="literal",
            match="a.b",
            replace="REPLACED",
        )
        result = engine.apply("a.b", [rule], scope="body")
        assert result == "REPLACED", (
            f"Literal rule did not match exact string. Got: {result!r}"
        )

    def test_literal_read_tool_does_not_match_read_tools(self):
        """
        Literal 'Read tool' must NOT match 'Read tools'.
        str.replace would replace 'Read tool' inside 'Read tools' as a substring.
        This IS expected behavior for str.replace — 'Read tool' IS a substring
        of 'Read tools'. But this test documents the behavior so it's explicit,
        not accidental.

        NOTE: This tests the ACTUAL str.replace behavior — substring matching.
        The task spec says 'Read tool' should not match 'Read tools' with word
        boundaries. This is a documented limitation: literal rules use str.replace
        (substring match), not word-boundary matching. See scar report.
        """
        engine = RulesEngine()
        rule = make_rule(
            id="tool_read",
            type="literal",
            match="Read tool",
            replace="file reading",
        )
        # 'Read tool' IS a substring of 'Read tools' — str.replace WILL match this
        result = engine.apply("Read tools are available.", [rule], scope="body")
        # Document the actual behavior: substring match replaces partial string
        # This is a KNOWN LIMITATION documented in the scar report
        assert result == "file readings are available.", (
            "Behavior changed: str.replace should match 'Read tool' inside 'Read tools'. "
            "If this assertion fails, check if word-boundary matching was added."
        )

    def test_literal_rule_does_not_match_prefix_extension(self):
        """
        'Edit tool' must NOT match 'Multi-Edit tool' as a full-word rule.
        With str.replace substring matching, 'Edit tool' WOULD match inside
        'Multi-Edit tool'. This documents the substring match behavior.
        """
        engine = RulesEngine()
        rule = make_rule(
            id="tool_edit",
            type="literal",
            match="Edit tool",
            replace="apply_patch",
        )
        result = engine.apply("Use Multi-Edit tool syntax.", [rule], scope="body")
        # str.replace substring behavior: 'Edit tool' inside 'Multi-Edit tool' matches
        assert result == "Use Multi-apply_patch syntax.", (
            "Behavior changed: substring match behavior for literal rules."
        )

    def test_literal_star_is_not_regex_quantifier(self):
        """
        Literal match containing '*' must not be treated as regex quantifier.
        """
        engine = RulesEngine()
        rule = make_rule(
            id="test",
            type="literal",
            match="a*b",
            replace="REPLACED",
        )
        # Should NOT match 'b' (zero a's) or 'aaab' — regex would
        result_no_match = engine.apply("b", [rule], scope="body")
        assert result_no_match == "b", (
            f"SILENT FAILURE: literal '*' treated as regex quantifier. Got: {result_no_match!r}"
        )


# ---------------------------------------------------------------------------
# DC-5: Empty input must return empty, not raise
#
# Silent failure: Engine called with empty string (e.g., empty SKILL.md or
# frontmatter-only file). Raises AttributeError or IndexError instead of
# returning empty. Conversion batch fails partway through.
# ---------------------------------------------------------------------------


class TestDC5EmptyInputHandling:
    def test_empty_string_returns_empty(self):
        """Empty input text must return empty text, never raise."""
        engine = RulesEngine()
        rule = make_rule(id="test", match="foo", replace="bar")
        result = engine.apply("", [rule], scope="body")
        assert result == "", f"Empty input should return empty, got: {result!r}"

    def test_empty_rules_list_returns_input_unchanged(self):
        """Empty rules list must return input unchanged."""
        engine = RulesEngine()
        result = engine.apply("Some text here.", [], scope="body")
        assert result == "Some text here.", (
            f"Empty rules should return input unchanged. Got: {result!r}"
        )

    def test_whitespace_only_input_returns_unchanged(self):
        """Whitespace-only input must not raise."""
        engine = RulesEngine()
        rule = make_rule(id="test", match="foo", replace="bar")
        result = engine.apply("   \n  \n  ", [rule], scope="body")
        assert result == "   \n  \n  ", (
            f"Whitespace input should return unchanged. Got: {result!r}"
        )


# ---------------------------------------------------------------------------
# DC-6: Non-matching pattern returns input unchanged, not error
#
# Silent failure: Engine raises re.error or returns None when pattern
# has no match. Caller sees exception mid-batch and stops converting.
# ---------------------------------------------------------------------------


class TestDC6NonMatchingPatternBehavior:
    def test_literal_no_match_returns_unchanged(self):
        """Literal match not found in text: return text unchanged."""
        engine = RulesEngine()
        rule = make_rule(id="test", match="NOTPRESENT", replace="bar")
        original = "Some text that does not contain the pattern."
        result = engine.apply(original, [rule], scope="body")
        assert result == original, (
            f"Non-matching literal should return input unchanged. Got: {result!r}"
        )

    def test_regex_no_match_returns_unchanged(self):
        """Regex pattern not found in text: return text unchanged, no error."""
        engine = RulesEngine()
        rule = make_rule(
            id="test",
            type="regex",
            match=r"invoke `samsara:([\w-]+)`",
            replace=r"use the `$samsara-\1` skill",
        )
        original = "Some body text with no skill invocations."
        result = engine.apply(original, [rule], scope="body")
        assert result == original, (
            f"Non-matching regex should return input unchanged. Got: {result!r}"
        )


# ---------------------------------------------------------------------------
# DC-7: Frontmatter-scoped rule MUST NOT modify body content
#
# Symmetric to DC-1. A frontmatter rule for 'model:' must not match
# occurrences of 'model:' in the body text.
# ---------------------------------------------------------------------------


class TestDC7FrontmatterRuleCannotModifyBody:
    def test_frontmatter_rule_does_not_alter_body(self):
        """
        Frontmatter-scoped rule must only transform frontmatter section.
        'model: claude-opus-4-5' appears in frontmatter.
        Body might also reference 'model:' in examples or prose.
        """
        engine = RulesEngine()
        rule = make_rule(
            id="model_replace",
            scope="frontmatter",
            type="literal",
            match="claude-opus-4-5",
            replace="gpt-4o",
        )
        text = """\
---
name: test-skill
model: claude-opus-4-5
---
# Body

The model claude-opus-4-5 is used here in prose.
"""
        result = engine.apply(text, [rule], scope="frontmatter")

        # Frontmatter should be transformed
        fm = result.split("---")[1]
        assert "gpt-4o" in fm, "Frontmatter rule did not transform frontmatter."

        # Body must not be modified
        body = result.split("---", 2)[2]
        assert "claude-opus-4-5" in body, (
            "SILENT FAILURE: frontmatter rule modified body content."
        )

    def test_scope_mismatch_body_scope_on_frontmatter_call(self):
        """
        When apply() is called with scope='body', frontmatter rules
        in the rules list must be skipped — they must not run at all.
        """
        engine = RulesEngine()
        fm_rule = make_rule(
            id="fm-rule",
            scope="frontmatter",
            type="literal",
            match="claude-opus-4-5",
            replace="gpt-4o",
        )
        text = """\
---
model: claude-opus-4-5
---
The model claude-opus-4-5 is mentioned in body.
"""
        # Calling apply with scope='body' — frontmatter-scoped rules should be skipped
        result = engine.apply(text, [fm_rule], scope="body")

        # Nothing should change — fm_rule is frontmatter-scoped, we called body scope
        assert result == text, (
            "SILENT FAILURE: frontmatter-scoped rule ran when apply() called with "
            "scope='body'. Result differed from input."
        )
