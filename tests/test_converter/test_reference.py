"""
Unit tests for ReferenceConverter.

Tests normal-path behavior after death tests establish the error boundaries.
"""

import pytest

from samsara_cli.config.schema import TransformationRule


def make_rule(**kwargs) -> TransformationRule:
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


class TestReferenceConverterTextConversion:
    def test_single_rule_applied_to_plain_prose(self):
        """Single literal rule transforms matching text."""
        from samsara_cli.converter.reference import ReferenceConverter

        text = "Use the Read tool to read files."
        rule = make_rule(match="Read tool", replace="file reading")
        converter = ReferenceConverter()
        result = converter.convert_text(text, rules=[rule])
        assert result == "Use the file reading to read files."

    def test_multiple_rules_applied_in_order(self):
        """Multiple rules applied sequentially, each sees previous output."""
        from samsara_cli.converter.reference import ReferenceConverter

        text = "Use Read tool, then Edit tool."
        rules = [
            make_rule(id="r1", match="Read tool", replace="file reading"),
            make_rule(id="r2", match="Edit tool", replace="apply_patch"),
        ]
        converter = ReferenceConverter()
        result = converter.convert_text(text, rules=rules)
        assert result == "Use file reading, then apply_patch."

    def test_regex_rule_applied_to_prose(self):
        """Regex-type rule applies to prose correctly."""
        from samsara_cli.converter.reference import ReferenceConverter

        text = "invoke `samsara:my-skill` here"
        rule = make_rule(
            id="skill",
            type="regex",
            match=r"invoke `samsara:([\w-]+)`",
            replace=r"use the `$samsara-\1` skill",
        )
        converter = ReferenceConverter()
        result = converter.convert_text(text, rules=[rule])
        assert result == "use the `$samsara-my-skill` skill here"

    def test_empty_rules_list_returns_text_unchanged(self):
        """No rules means no transformation."""
        from samsara_cli.converter.reference import ReferenceConverter

        text = "Use the Read tool here."
        converter = ReferenceConverter()
        result = converter.convert_text(text, rules=[])
        assert result == text

    def test_rules_with_no_match_return_text_unchanged(self):
        """Rules that don't match leave text unchanged."""
        from samsara_cli.converter.reference import ReferenceConverter

        text = "No tool references here."
        rule = make_rule(match="Read tool", replace="file reading")
        converter = ReferenceConverter()
        result = converter.convert_text(text, rules=[rule])
        assert result == text


class TestReferenceConverterCodeBlockProtection:
    def test_fenced_code_block_passes_through_unchanged(self):
        """Triple-backtick fenced block content is preserved."""
        from samsara_cli.converter.reference import ReferenceConverter

        text = "```\nRead tool example\n```"
        rule = make_rule(match="Read tool", replace="file reading")
        converter = ReferenceConverter()
        result = converter.convert_text(text, rules=[rule])
        assert "Read tool example" in result

    def test_language_tagged_code_block_preserved(self):
        """Code block with language tag (```yaml) is also protected."""
        from samsara_cli.converter.reference import ReferenceConverter

        text = "```yaml\ntool: Read tool\n```"
        rule = make_rule(match="Read tool", replace="file reading")
        converter = ReferenceConverter()
        result = converter.convert_text(text, rules=[rule])
        assert "tool: Read tool" in result

    def test_prose_between_code_blocks_transformed(self):
        """Text between two code blocks is prose and gets rules applied."""
        from samsara_cli.converter.reference import ReferenceConverter

        text = "```\nblock1\n```\n\nUse Read tool here.\n\n```\nblock2\n```"
        rule = make_rule(match="Read tool", replace="file reading")
        converter = ReferenceConverter()
        result = converter.convert_text(text, rules=[rule])
        assert "file reading here" in result
        assert "block1" in result
        assert "block2" in result


class TestReferenceConverterFileConversion:
    def test_convert_file_reads_source_and_applies_rules(self, tmp_path):
        """convert() reads a source file and returns transformed text."""
        from samsara_cli.converter.reference import ReferenceConverter

        source = tmp_path / "reference.md"
        source.write_text("Use the Read tool to read files.")
        rule = make_rule(match="Read tool", replace="file reading")
        converter = ReferenceConverter()
        result = converter.convert(source, rules=[rule])
        assert isinstance(result, str)
        assert "file reading" in result

    def test_convert_file_returns_string(self, tmp_path):
        """convert() returns str, not bytes or Path."""
        from samsara_cli.converter.reference import ReferenceConverter

        source = tmp_path / "reference.md"
        source.write_text("# Reference\n\nContent here.")
        converter = ReferenceConverter()
        result = converter.convert(source, rules=[])
        assert isinstance(result, str)

    def test_convert_nonexistent_file_raises(self, tmp_path):
        """Missing source file raises FileNotFoundError."""
        from samsara_cli.converter.reference import ReferenceConverter

        converter = ReferenceConverter()
        with pytest.raises(FileNotFoundError):
            converter.convert(tmp_path / "does_not_exist.md", rules=[])

    def test_convert_does_not_modify_source_file(self, tmp_path):
        """convert() must not write to the source file."""
        from samsara_cli.converter.reference import ReferenceConverter

        original_text = "Use the Read tool here."
        source = tmp_path / "reference.md"
        source.write_text(original_text)
        rule = make_rule(match="Read tool", replace="file reading")
        converter = ReferenceConverter()
        converter.convert(source, rules=[rule])
        assert source.read_text() == original_text, "convert() mutated the source file."


class TestReferenceConverterWithActualRules:
    def test_codex_tool_rules_transform_prose_not_code_blocks(self):
        """
        Integration test with realistic codex transformation rules.
        Verifies tool name replacement in prose while preserving code blocks.
        """
        from samsara_cli.converter.reference import ReferenceConverter

        text = """\
# Reference

Use the Read tool to examine files.
Use the Grep tool to search.

```yaml
tool: Read tool
action: read_file
```

Use the Edit tool to make changes.
"""
        rules = [
            make_rule(
                id="r1",
                match="Read tool",
                replace="file reading (via exec_command with cat/nl)",
            ),
            make_rule(id="r2", match="Grep tool", replace="exec_command with rg"),
            make_rule(id="r3", match="Edit tool", replace="apply_patch"),
        ]
        converter = ReferenceConverter()
        result = converter.convert_text(text, rules=rules)

        # Prose transformed
        assert "file reading (via exec_command with cat/nl) to examine files" in result
        assert "exec_command with rg to search" in result
        assert "apply_patch to make changes" in result
        # Code block preserved
        assert "tool: Read tool" in result

    def test_body_scoped_rules_used_not_frontmatter_scoped(self):
        """
        Reference converter must use scope='body' rules only.
        Frontmatter-scoped rules in the list must be skipped.
        """
        from samsara_cli.converter.reference import ReferenceConverter

        text = "Use the Read tool here."
        body_rule = make_rule(
            id="body-rule",
            scope="body",
            match="Read tool",
            replace="file reading",
        )
        fm_rule = make_rule(
            id="fm-rule",
            scope="frontmatter",
            match="Read tool",
            replace="SHOULD_NOT_APPEAR",
        )
        converter = ReferenceConverter()
        result = converter.convert_text(text, rules=[body_rule, fm_rule])
        assert "file reading" in result
        assert "SHOULD_NOT_APPEAR" not in result
