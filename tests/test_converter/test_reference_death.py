"""
Death tests for ReferenceConverter — targeting silent failure paths.

Each test names the specific silent failure it guards against.
Death tests run BEFORE unit tests. They must fail red before implementation,
then pass green after.

Silent failures guarded here:
  DRD-1: Tool references inside fenced code blocks get converted — code
         examples become wrong, misleading users who copy from them.
  DRD-2: Rules are NOT applied to prose — tool references in body text
         survive unconverted, agent uses wrong tool names at runtime.
  DRD-3: Partial code block extraction — an unclosed or nested code block
         causes prose to be treated as code or vice versa.
  DRD-4: Empty file silently produces empty output with no error — caller
         cannot distinguish "empty source" from "conversion failed silently".
"""

from samsara_cli.config.schema import TransformationRule


def make_rule(**kwargs) -> TransformationRule:
    """Construct a TransformationRule with minimal required fields."""
    defaults = {
        "id": "test-rule",
        "scope": "body",
        "type": "literal",
        "match": "Read tool",
        "replace": "file reading (via exec_command with cat/nl)",
        "priority": "medium",
    }
    defaults.update(kwargs)
    return TransformationRule(**defaults)


# ---------------------------------------------------------------------------
# DRD-1: Tool names inside fenced code blocks must NOT be transformed
#
# Silent failure: RulesEngine called on full text applies literal rule
# 'Read tool' → replacement inside ``` yaml\n  tool: Read\n``` block.
# The YAML code example in the reference becomes wrong. Any agent or human
# reading it sees the Codex-specific replacement instead of the source tool name.
# First discovery: someone copies code from the reference, runs it on Claude Code,
# and finds it uses Codex syntax instead of Claude Code syntax.
# ---------------------------------------------------------------------------


class TestDRD1CodeBlocksProtected:
    def test_tool_name_in_fenced_code_block_not_transformed(self):
        """
        'Read tool' inside a fenced code block must survive conversion.
        Guard: ReferenceConverter must extract blocks before applying rules.
        """
        from samsara_cli.converter.reference import ReferenceConverter

        text = """\
# Reference

Use the Read tool to read files.

```yaml
  tool: Read tool
  action: read
```

More prose after the block.
"""
        rule = make_rule(
            id="tool_read",
            match="Read tool",
            replace="file reading (via exec_command with cat/nl)",
        )
        converter = ReferenceConverter()
        result = converter.convert_text(text, rules=[rule])

        # Code block content must be preserved
        assert "Read tool" in result, (
            "SILENT FAILURE: 'Read tool' inside fenced code block was transformed. "
            "Code blocks must be protected from rule application."
        )

    def test_code_block_tool_reference_exact_preservation(self):
        """
        The exact content between fences must be identical in output.
        Not just that 'Read tool' survives — the entire block must be byte-identical.
        """
        from samsara_cli.converter.reference import ReferenceConverter

        code_block_content = "```yaml\n  tool: Read tool\n  other: Edit tool\n```"
        text = f"Prose before.\n\n{code_block_content}\n\nProse after."

        rules = [
            make_rule(id="r1", match="Read tool", replace="file reading"),
            make_rule(id="r2", match="Edit tool", replace="apply_patch"),
        ]
        converter = ReferenceConverter()
        result = converter.convert_text(text, rules=rules)

        assert code_block_content in result, (
            "SILENT FAILURE: code block content was modified. "
            "Expected block to appear verbatim in output."
        )

    def test_multiple_code_blocks_all_protected(self):
        """
        When multiple fenced code blocks exist, ALL of them must be protected.
        Guard: protection must not stop after the first block.
        """
        from samsara_cli.converter.reference import ReferenceConverter

        text = """\
# Reference

Use the Read tool here.

```python
# Read tool example
x = read_file("path")
```

Use the Edit tool here.

```yaml
- Edit tool
- Write tool
```

Final prose with Read tool mention.
"""
        rules = [
            make_rule(id="r1", match="Read tool", replace="file reading"),
            make_rule(id="r2", match="Edit tool", replace="apply_patch"),
            make_rule(id="r3", match="Write tool", replace="apply_patch"),
        ]
        converter = ReferenceConverter()
        result = converter.convert_text(text, rules=rules)

        # Both code blocks must be preserved exactly
        assert "# Read tool example" in result, (
            "SILENT FAILURE: first code block content was transformed."
        )
        assert "- Edit tool\n- Write tool" in result, (
            "SILENT FAILURE: second code block content was transformed."
        )

    def test_inline_backtick_code_spans_distinguished_from_fenced_blocks(self):
        """
        Inline `code spans` are NOT fenced code blocks.
        The requirement only protects fenced blocks (triple backtick).
        Inline spans should still receive rule application if they match.
        This documents the boundary of protection.

        Note: this test documents expected behavior — inline spans are prose,
        fenced blocks are protected. The implementation may or may not protect
        inline spans; this test captures the minimal requirement.
        """
        from samsara_cli.converter.reference import ReferenceConverter

        # Clear structure: inline span in prose before a proper fenced block
        text = (
            "Use `Read tool` inline — this is prose, not a code block.\n"
            "\n"
            "```\n"
            "Read tool in block\n"
            "```\n"
        )
        rule = make_rule(id="r1", match="Read tool", replace="file reading")
        converter = ReferenceConverter()
        result = converter.convert_text(text, rules=[rule])

        # The fenced block content must be protected
        assert "Read tool in block" in result, (
            "SILENT FAILURE: Read tool in fenced block was transformed."
        )
        # The inline span in prose must be transformed (prose rule applies)
        assert "file reading" in result, (
            "Prose containing inline span was not transformed."
        )


# ---------------------------------------------------------------------------
# DRD-2: Rules MUST be applied to prose sections
#
# Silent failure: Code block protection implementation accidentally protects
# ALL text (bug in prose extraction). Tool references in body text survive
# unconverted. Agent on Codex platform receives wrong tool names and fails
# silently or noisily at runtime.
# First discovery: agent tries to use "Read tool" on Codex, which has no
# such tool, and gets an unknown tool error.
# ---------------------------------------------------------------------------


class TestDRD2ProseSectionsTransformed:
    def test_tool_reference_in_prose_is_transformed(self):
        """
        'Read tool' in plain prose must be transformed.
        Guard against over-protection that treats all text as code.
        """
        from samsara_cli.converter.reference import ReferenceConverter

        text = "Use the Read tool to read files."
        rule = make_rule(
            id="tool_read",
            match="Read tool",
            replace="file reading (via exec_command with cat/nl)",
        )
        converter = ReferenceConverter()
        result = converter.convert_text(text, rules=[rule])

        assert "file reading (via exec_command with cat/nl)" in result, (
            "SILENT FAILURE: prose tool reference was not transformed. "
            "Rules must apply to body text outside code blocks."
        )
        assert "Read tool" not in result, (
            "Original tool name survived in prose — rules did not apply."
        )

    def test_prose_before_and_after_code_block_both_transformed(self):
        """
        Prose before a code block AND prose after must both be transformed.
        Guard: implementation must not stop transforming prose after the first block.
        """
        from samsara_cli.converter.reference import ReferenceConverter

        text = """\
Use the Read tool before the block.

```yaml
Read tool: preserved
```

Use the Edit tool after the block.
"""
        rules = [
            make_rule(id="r1", match="Read tool", replace="file reading"),
            make_rule(id="r2", match="Edit tool", replace="apply_patch"),
        ]
        converter = ReferenceConverter()
        result = converter.convert_text(text, rules=rules)

        assert "file reading before the block" in result, (
            "SILENT FAILURE: prose before code block was not transformed."
        )
        assert "apply_patch after the block" in result, (
            "SILENT FAILURE: prose after code block was not transformed."
        )
        # Code block preserved
        assert "Read tool: preserved" in result, (
            "SILENT FAILURE: code block was transformed (prose protection bleeds)."
        )

    def test_multiple_tool_references_in_prose_all_transformed(self):
        """
        Multiple different tool references in prose must all be transformed.
        Guard: rule application must not stop after the first match.
        """
        from samsara_cli.converter.reference import ReferenceConverter

        text = (
            "First use the Read tool. Then use the Edit tool. "
            "Finally use the Grep tool."
        )
        rules = [
            make_rule(id="r1", match="Read tool", replace="file reading"),
            make_rule(id="r2", match="Edit tool", replace="apply_patch"),
            make_rule(id="r3", match="Grep tool", replace="exec_command with rg"),
        ]
        converter = ReferenceConverter()
        result = converter.convert_text(text, rules=rules)

        assert "Read tool" not in result
        assert "Edit tool" not in result
        assert "Grep tool" not in result
        assert "file reading" in result
        assert "apply_patch" in result
        assert "exec_command with rg" in result


# ---------------------------------------------------------------------------
# DRD-3: Unclosed or edge-case code blocks must not corrupt output
#
# Silent failure: A code block that opens but never closes causes all text
# after the opening fence to be treated as code — all rules silently skip it.
# Or a closing fence inside a code block causes premature block end, leaking
# remaining content as prose and converting code block content.
# First discovery: whoever reviews the converted file and finds tool names
# in unexpected places (code block content transformed, or prose not transformed).
# ---------------------------------------------------------------------------


class TestDRD3EdgeCaseCodeBlocks:
    def test_unclosed_code_block_does_not_swallow_entire_rest_of_file(self):
        """
        An unclosed ``` block must not cause ALL following text to be protected.
        This tests the most dangerous partial-failure: converter silently skips
        transforming the entire second half of a file.

        Acceptable behaviors:
        - Treat unclosed block as prose (apply rules to it)
        - Raise an explicit error about unclosed block
        NOT acceptable: silently protect all subsequent prose from rules.
        """
        from samsara_cli.converter.reference import ReferenceConverter

        text = """\
Use the Read tool here — must be transformed.

```yaml
this block is unclosed

Use the Edit tool here — behavior is implementation-defined, but
the prose BEFORE this block must still be transformed.
"""
        rule = make_rule(id="r1", match="Read tool", replace="file reading")
        converter = ReferenceConverter()
        result = converter.convert_text(text, rules=[rule])

        # The prose BEFORE the unclosed block must be transformed
        assert "file reading here — must be transformed" in result, (
            "SILENT FAILURE: unclosed code block caused prose before it to be skipped. "
            "At minimum, prose before the first unclosed block must be transformed."
        )

    def test_empty_code_block_does_not_corrupt_output(self):
        """
        An empty code block (``` immediately followed by ```) must not corrupt output.
        """
        from samsara_cli.converter.reference import ReferenceConverter

        text = "Use the Read tool.\n\n```\n```\n\nUse the Edit tool."
        rules = [
            make_rule(id="r1", match="Read tool", replace="file reading"),
            make_rule(id="r2", match="Edit tool", replace="apply_patch"),
        ]
        converter = ReferenceConverter()
        result = converter.convert_text(text, rules=rules)

        assert "file reading" in result
        assert "apply_patch" in result

    def test_code_block_at_start_of_file(self):
        """
        File starting with a code block must protect that block and transform prose after.
        """
        from samsara_cli.converter.reference import ReferenceConverter

        text = "```\nRead tool\n```\n\nUse the Read tool here."
        rule = make_rule(id="r1", match="Read tool", replace="file reading")
        converter = ReferenceConverter()
        result = converter.convert_text(text, rules=[rule])

        # Block preserved
        lines = result.split("\n")
        # The block content "Read tool" line must be preserved
        assert any("Read tool" in line for line in lines[:4]), (
            "Code block at file start was not protected."
        )
        # Prose after must be transformed
        assert "file reading here" in result, (
            "Prose after opening code block was not transformed."
        )

    def test_code_block_at_end_of_file_no_trailing_newline(self):
        """
        Code block at end of file without trailing newline must be protected.
        Guard: fence detection must not require trailing newline after closing ```.
        """
        from samsara_cli.converter.reference import ReferenceConverter

        text = "Use the Read tool.\n\n```\nRead tool\n```"
        rule = make_rule(id="r1", match="Read tool", replace="file reading")
        converter = ReferenceConverter()
        result = converter.convert_text(text, rules=[rule])

        assert "file reading." in result, "Prose was not transformed."
        assert "Read tool\n```" in result or "```\nRead tool\n```" in result, (
            "Code block at end of file without trailing newline was corrupted."
        )


# ---------------------------------------------------------------------------
# DRD-4: Empty or whitespace-only file must not silently produce wrong output
#
# Silent failure: Empty source reference file produces empty target, and caller
# cannot distinguish this from a conversion failure. The reference file slot
# exists in the platform output but contains nothing — agent has no reference.
# ---------------------------------------------------------------------------


class TestDRD4EmptyFileHandling:
    def test_empty_text_returns_empty_string(self):
        """
        Empty input must return empty string, not raise.
        Caller must be able to detect empty output and decide whether to error.
        """
        from samsara_cli.converter.reference import ReferenceConverter

        converter = ReferenceConverter()
        rule = make_rule(id="r1", match="Read tool", replace="file reading")
        result = converter.convert_text("", rules=[rule])
        assert result == "", f"Empty input should return empty string, got: {result!r}"

    def test_whitespace_only_text_returns_unchanged(self):
        """
        Whitespace-only input must return unchanged, not raise.
        """
        from samsara_cli.converter.reference import ReferenceConverter

        converter = ReferenceConverter()
        rule = make_rule(id="r1", match="Read tool", replace="file reading")
        result = converter.convert_text("   \n  \n  ", rules=[rule])
        assert result == "   \n  \n  ", (
            f"Whitespace input should return unchanged. Got: {result!r}"
        )

    def test_text_with_no_matching_rules_returns_unchanged(self):
        """
        Text with no rule matches must return unchanged — not empty, not None.
        Guard: rules engine returning None or empty on no-match.
        """
        from samsara_cli.converter.reference import ReferenceConverter

        original = "# Reference\n\nNo tool references in this file."
        rule = make_rule(id="r1", match="Read tool", replace="file reading")
        converter = ReferenceConverter()
        result = converter.convert_text(original, rules=[rule])
        assert result == original, (
            f"No-match text should return unchanged. Got: {result!r}"
        )
