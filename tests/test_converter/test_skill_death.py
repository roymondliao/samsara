"""
Death tests for SkillConverter — targeting silent failure paths.

Each test names the specific silent failure it guards against.
Death tests run BEFORE unit tests. They must fail red before implementation,
then pass green after.

Silent failures guarded here:
  DC-SK-1: Transition statement (invoke `samsara:X`) not converted — unconverted
            source pattern in output is a hard error (dead chain link for Codex user)
  DC-SK-2: Companion file (e.g. problem-autopsy.md) does NOT have body rules applied —
            unconverted tool references in companion files break the chain silently
  DC-SK-3: SKILL.md frontmatter `name` field is corrupted by body rules — skill becomes
            unidentifiable. Frontmatter is for identity, not instructions
  DC-SK-4: SKILL.md frontmatter `description` field is rewritten by tool reference rules —
            description is for routing/matching, not execution; rewriting it changes
            skill discovery semantics
  DC-SK-5: Graphviz digraph blocks in body survive transformation — regex rules must not
            corrupt dot syntax (e.g., `->` arrows, node labels, `samsara:X` inside label
            strings must NOT be converted)
  DC-SK-6: YAML template files (.yaml) inside skills do NOT have rules applied —
            applying markdown body rules to YAML structure corrupts data files
  DC-SK-7: Target validator scan — if any source pattern remains in output, convert()
            must raise ConversionError rather than return silently wrong output
"""

from pathlib import Path

import pytest

from samsara_cli.config.schema import NamingConfig, TransformationRule
from samsara_cli.converter.skill import ConversionError, SkillConverter


# ---------------------------------------------------------------------------
# Fixtures and helpers
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


def make_naming(prefix: str = "samsara", separator: str = "-") -> NamingConfig:
    return NamingConfig(skill_prefix=prefix, separator=separator)


def make_transition_rule() -> TransformationRule:
    """The real codex rule for skill invocation transitions."""
    return TransformationRule(
        id="skill_invocation",
        scope="body",
        type="regex",
        match=r"invoke `samsara:([\w-]+)`",
        replace=r"use the `$samsara-\1` skill",
        priority="high",
    )


CODEX_RULES = [
    TransformationRule(
        id="skill_invocation",
        scope="body",
        type="regex",
        match=r"invoke `samsara:([\w-]+)`",
        replace=r"use the `$samsara-\1` skill",
        priority="high",
    ),
    TransformationRule(
        id="skill_invocation_variant",
        scope="body",
        type="regex",
        match=r"invoke `samsara:([\w-]+)` skill",
        replace=r"use the `$samsara-\1` skill",
        priority="high",
    ),
    TransformationRule(
        id="agent_dispatch_subagent_type",
        scope="body",
        type="regex",
        match=r'subagent_type: "samsara:([\w-]+)"',
        replace=r'agent named "samsara-\1"',
        priority="high",
    ),
    TransformationRule(
        id="agent_tool_reference",
        scope="body",
        type="regex",
        match=r"Agent tool:",
        replace="Subagent dispatch:",
        priority="high",
    ),
    TransformationRule(
        id="tool_read",
        scope="body",
        type="literal",
        match="Read tool",
        replace="file reading (via exec_command with cat/nl)",
        priority="medium",
    ),
    TransformationRule(
        id="tool_bash",
        scope="body",
        type="literal",
        match="Bash tool",
        replace="exec_command",
        priority="medium",
    ),
]


# ---------------------------------------------------------------------------
# DC-SK-1: Transition statement must be converted
#
# Silent failure: `invoke \`samsara:planning\`` not converted in SKILL.md body.
# Codex user follows the skill and hits a dead reference. The converted output
# LOOKS valid — no error is raised — but the chain is broken at runtime.
# Discovery: Codex user hits an unresolvable skill reference. By then all 11
# skills may have shipped with the same break.
# ---------------------------------------------------------------------------


class TestDCSK1TransitionStatementMustBeConverted:
    def test_skill_invocation_in_body_is_converted(self, tmp_path: Path):
        """
        A SKILL.md with the pattern 'invoke `samsara:planning`' in the body MUST have that
        transition converted by the skill_invocation rule.
        If this remains in output, the converter has a silent chain-break bug.
        """
        skill_dir = tmp_path / "research"
        skill_dir.mkdir()
        skill_md = skill_dir / "SKILL.md"
        skill_md.write_text(
            "---\n"
            "name: research\n"
            "description: Use when starting new work\n"
            "---\n"
            "\n"
            "# Research\n"
            "\n"
            "After completing research, invoke `samsara:planning` skill.\n"
        )

        converter = SkillConverter()
        result = converter.convert(skill_dir, [make_transition_rule()], make_naming())

        skill_content = result.skill_md_content
        assert "invoke `samsara:planning`" not in skill_content, (
            "SILENT FAILURE [DC-SK-1]: Source pattern 'invoke `samsara:planning`' "
            "remains in converted SKILL.md body. Chain is broken for Codex users."
        )
        assert "$samsara-planning" in skill_content, (
            "Expected converted reference '$samsara-planning' not found in body. "
            "Transition rule did not apply."
        )

    def test_multiple_transitions_all_converted(self, tmp_path: Path):
        """All transition statements in a body must be converted, not just the first."""
        skill_dir = tmp_path / "bootstrap"
        skill_dir.mkdir()
        skill_md = skill_dir / "SKILL.md"
        skill_md.write_text(
            "---\n"
            "name: samsara-bootstrap\n"
            "description: Boot skill\n"
            "---\n"
            "\n"
            "Use invoke `samsara:research` to start. Or invoke `samsara:debugging` for bugs.\n"
        )

        converter = SkillConverter()
        result = converter.convert(skill_dir, [make_transition_rule()], make_naming())

        content = result.skill_md_content
        # Neither unconverted pattern should remain
        assert "invoke `samsara:research`" not in content, (
            "DC-SK-1: First transition not converted"
        )
        assert "invoke `samsara:debugging`" not in content, (
            "DC-SK-1: Second transition not converted"
        )

    def test_unconverted_source_pattern_triggers_validation_error(self, tmp_path: Path):
        """
        If a source pattern remains in output after conversion, the converter
        MUST raise ConversionError — not return silently wrong output.
        This is the target validator guard from the architecture death cases.
        """
        skill_dir = tmp_path / "planning"
        skill_dir.mkdir()
        # Body contains transition that NO rule covers (different pattern)
        # We give zero rules — so the source pattern cannot be converted
        skill_md = skill_dir / "SKILL.md"
        skill_md.write_text(
            "---\n"
            "name: planning\n"
            "description: Planning skill\n"
            "---\n"
            "\n"
            "invoke `samsara:implement` here.\n"
        )

        converter = SkillConverter()
        # With no rules, the source pattern survives — validator must catch it
        with pytest.raises(ConversionError, match=r"samsara:"):
            converter.convert(skill_dir, [], make_naming())


# ---------------------------------------------------------------------------
# DC-SK-2: Companion files must also have body rules applied
#
# Silent failure: problem-autopsy.md or dispatch-template.md contains
# `invoke \`samsara:X\`` or `Agent tool:` references. Only SKILL.md is
# converted; companion files ship unchanged. Codex user reads the support
# doc and sees Claude Code syntax. First discovered by confused user.
# ---------------------------------------------------------------------------


class TestDCSK2CompanionFileMustHaveRulesApplied:
    def test_companion_md_file_has_body_rules_applied(self, tmp_path: Path):
        """
        A companion .md file (e.g. problem-autopsy.md) with tool references
        in its body MUST have body rules applied — not just SKILL.md.
        """
        skill_dir = tmp_path / "research"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: research\ndescription: Research skill\n---\n\n# Research body\n"
        )
        companion = skill_dir / "problem-autopsy.md"
        companion.write_text(
            "# Problem Autopsy\n"
            "\n"
            "Use the Read tool to read files.\n"
            "After research, invoke `samsara:planning`.\n"
        )

        rules = [
            make_rule(match="Read tool", replace="file reading"),
            make_transition_rule(),
        ]
        converter = SkillConverter()
        result = converter.convert(skill_dir, rules, make_naming())

        companion_content = result.companion_files["problem-autopsy.md"]
        assert "Read tool" not in companion_content, (
            "SILENT FAILURE [DC-SK-2]: 'Read tool' survived in companion file. "
            "Body rules must apply to companion .md files."
        )
        assert "invoke `samsara:planning`" not in companion_content, (
            "SILENT FAILURE [DC-SK-2]: Transition statement survived in companion file."
        )

    def test_dispatch_template_companion_has_agent_tool_converted(self, tmp_path: Path):
        """
        dispatch-template.md in implement skill contains literal 'Agent tool:'
        syntax. This companion file MUST have body rules applied.
        """
        skill_dir = tmp_path / "implement"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: implement\ndescription: Implement skill\n---\n\n# Implement\n"
        )
        dispatch = skill_dir / "dispatch-template.md"
        dispatch.write_text(
            "# Dispatch Template\n"
            "\n"
            "```\n"
            "Agent tool:\n"
            '  subagent_type: "samsara:implementer"\n'
            "```\n"
        )

        rules = [
            TransformationRule(
                id="agent_tool_reference",
                scope="body",
                type="regex",
                match="Agent tool:",
                replace="Subagent dispatch:",
                priority="high",
            ),
            TransformationRule(
                id="agent_dispatch_subagent_type",
                scope="body",
                type="regex",
                match=r'subagent_type: "samsara:([\w-]+)"',
                replace=r'agent named "samsara-\1"',
                priority="high",
            ),
        ]
        converter = SkillConverter()
        result = converter.convert(skill_dir, rules, make_naming())

        dispatch_content = result.companion_files["dispatch-template.md"]
        assert "Agent tool:" not in dispatch_content, (
            "SILENT FAILURE [DC-SK-2]: 'Agent tool:' survived in dispatch-template.md"
        )
        assert 'subagent_type: "samsara:implementer"' not in dispatch_content, (
            "SILENT FAILURE [DC-SK-2]: subagent_type survived in dispatch-template.md"
        )

    def test_yaml_template_files_are_not_processed_with_md_rules(self, tmp_path: Path):
        """
        YAML template files (e.g., templates/scar-schema.yaml) must NOT have
        markdown body rules applied. Applying 'Read tool' -> 'file reading'
        to a YAML file would corrupt data structure.
        This tests DC-SK-6 (YAML files should be copied as-is).
        """
        skill_dir = tmp_path / "implement"
        skill_dir.mkdir()
        templates_dir = skill_dir / "templates"
        templates_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: implement\ndescription: Implement skill\n---\n\n# Implement\n"
        )
        scar_yaml = templates_dir / "scar-schema.yaml"
        # YAML content that contains text that LOOKS like it could match rules
        scar_yaml.write_text(
            "# Scar schema\n"
            "read_tool_note: 'Use Read tool for reading'\n"
            "fields:\n"
            "  - name: read_tool\n"
        )

        rules = [make_rule(match="Read tool", replace="file reading")]
        converter = SkillConverter()
        result = converter.convert(skill_dir, rules, make_naming())

        yaml_content = result.companion_files["templates/scar-schema.yaml"]
        assert "Read tool" in yaml_content, (
            "SILENT FAILURE [DC-SK-6]: YAML template file had body rules applied. "
            "Rules must NOT modify .yaml files — they should be copied as-is."
        )


# ---------------------------------------------------------------------------
# DC-SK-3: Frontmatter `name` field must NOT be corrupted by body rules
#
# Silent failure: A body rule for 'samsara:X' accidentally matches the name
# field value. The skill becomes unidentifiable or mis-routed.
# Discovery: Codex cannot find skill by name; skill routing fails silently.
# ---------------------------------------------------------------------------


class TestDCSK3FrontmatterNamePreserved:
    def test_name_field_not_modified_by_body_rules(self, tmp_path: Path):
        """
        SKILL.md frontmatter 'name' field must retain its original value
        after conversion. Body rules (scope='body') must not touch frontmatter.
        """
        skill_dir = tmp_path / "research"
        skill_dir.mkdir()
        skill_md = skill_dir / "SKILL.md"
        skill_md.write_text(
            "---\n"
            "name: research\n"
            "description: Use when starting new work\n"
            "---\n"
            "\n"
            "# Research\n"
            "\n"
            "Use the Read tool to research.\n"
        )

        rules = [make_rule(match="Read tool", replace="file reading")]
        converter = SkillConverter()
        result = converter.convert(skill_dir, rules, make_naming())

        assert result.name == "research", (
            f"SILENT FAILURE [DC-SK-3]: name field was modified. Got: {result.name!r}"
        )

    def test_name_with_tool_reference_pattern_not_modified(self, tmp_path: Path):
        """
        If skill name contains text that could match a body rule (edge case),
        the name must still survive unchanged because rules scope to body only.
        """
        skill_dir = tmp_path / "read-tool-skill"
        skill_dir.mkdir()
        skill_md = skill_dir / "SKILL.md"
        # Hypothetical edge: name contains pattern that body rule would match
        skill_md.write_text(
            "---\n"
            "name: read-tool-skill\n"
            "description: A skill about reading tools\n"
            "---\n"
            "\n"
            "# Body\n"
            "\n"
            "Use the Read tool here.\n"
        )

        rules = [make_rule(match="Read tool", replace="file reading")]
        converter = SkillConverter()
        result = converter.convert(skill_dir, rules, make_naming())

        # name is from frontmatter — must be untouched
        assert result.name == "read-tool-skill", (
            f"DC-SK-3: Name field modified by body rule. Got: {result.name!r}"
        )


# ---------------------------------------------------------------------------
# DC-SK-4: Frontmatter `description` must NOT have tool references rewritten
#
# Silent failure: description field is used for skill routing/matching.
# Rewriting 'Read tool' in the description changes the semantic signal
# used for discovery. No error — skill simply matches differently.
# Discovery: User invokes wrong skill, or skill is never triggered.
# ---------------------------------------------------------------------------


class TestDCSK4FrontmatterDescriptionPreserved:
    def test_description_not_modified_by_body_rules(self, tmp_path: Path):
        """
        SKILL.md frontmatter 'description' must not have tool references rewritten.
        The description is used for matching, not for instructions.
        """
        skill_dir = tmp_path / "research"
        skill_dir.mkdir()
        original_description = (
            "Use when starting new feature work — requires Read tool access "
            "and invoke `samsara:planning` capability"
        )
        skill_md = skill_dir / "SKILL.md"
        skill_md.write_text(
            "---\n"
            f"name: research\n"
            f"description: {original_description}\n"
            "---\n"
            "\n"
            "# Research body\n"
            "\n"
            "Use Read tool to read. invoke `samsara:planning` when done.\n"
        )

        rules = [
            make_rule(match="Read tool", replace="file reading"),
            make_transition_rule(),
        ]
        converter = SkillConverter()
        result = converter.convert(skill_dir, rules, make_naming())

        assert result.description == original_description, (
            "SILENT FAILURE [DC-SK-4]: description field was modified by body rules. "
            f"Expected: {original_description!r}\n"
            f"Got: {result.description!r}"
        )

    def test_frontmatter_description_survives_in_output_text(self, tmp_path: Path):
        """
        The raw frontmatter text in the output SKILL.md must preserve description.
        """
        skill_dir = tmp_path / "implement"
        skill_dir.mkdir()
        skill_md = skill_dir / "SKILL.md"
        skill_md.write_text(
            "---\n"
            "name: implement\n"
            "description: Use when a plan exists and you need to execute — requires Read tool\n"
            "---\n"
            "\n"
            "Use the Read tool here.\n"
        )

        rules = [make_rule(match="Read tool", replace="file reading")]
        converter = SkillConverter()
        result = converter.convert(skill_dir, rules, make_naming())

        content = result.skill_md_content
        # description in frontmatter must be untouched
        assert "requires Read tool" in content, (
            "SILENT FAILURE [DC-SK-4]: description in frontmatter was corrupted. "
            "Tool reference in description should be preserved."
        )
        # but body should be converted
        assert "file reading" in content, "Body rule did not apply to body content."


# ---------------------------------------------------------------------------
# DC-SK-5: Graphviz digraph blocks must survive transformation
#
# Silent failure: A regex rule matching `samsara:X` pattern also matches
# inside dot syntax like `label="invoke samsara:planning"` or arrows `->`.
# Corrupted dot syntax causes rendering failures that look like content issues.
# Discovery: Engineer renders diagram; output is garbage. Blamed on graphviz.
#
# NOTE: The architecture specifies this is a known risk. The death test guards
# against the worst case — complete corruption of the dot block structure.
# The rules engine is code-block-unaware (task-2 scar), so this is a
# documented known limitation. The test verifies the specific case of the
# `->` arrow syntax not being corrupted.
# ---------------------------------------------------------------------------


class TestDCSK5GraphvizBlockSurvivesTransformation:
    def test_dot_arrow_syntax_not_corrupted(self, tmp_path: Path):
        """
        Graphviz digraph `->` arrow syntax must not be corrupted by rules.
        This is the most load-bearing structural element — if arrows are
        corrupted, the entire diagram is invalid.
        """
        skill_dir = tmp_path / "research"
        skill_dir.mkdir()
        skill_md = skill_dir / "SKILL.md"
        skill_md.write_text(
            "---\n"
            "name: research\n"
            "description: Research skill\n"
            "---\n"
            "\n"
            "# Research\n"
            "\n"
            "```dot\n"
            "digraph research {\n"
            "    node [shape=box];\n"
            "    start -> interrogate;\n"
            "    interrogate -> scope;\n"
            '    next [label="invoke samsara:planning" shape=doublecircle];\n'
            "}\n"
            "```\n"
            "\n"
            "After research, invoke `samsara:planning`.\n"
        )

        rules = [make_transition_rule()]
        converter = SkillConverter()
        result = converter.convert(skill_dir, rules, make_naming())

        content = result.skill_md_content
        # Arrow syntax must survive (not converted or mangled)
        assert "start -> interrogate;" in content, (
            "SILENT FAILURE [DC-SK-5]: Graphviz '->'' arrow syntax was corrupted. "
            "Dot block structural elements must not be modified."
        )
        assert "interrogate -> scope;" in content, (
            "SILENT FAILURE [DC-SK-5]: Second arrow syntax corrupted."
        )

    def test_dot_block_digraph_keyword_survives(self, tmp_path: Path):
        """The 'digraph' keyword and braces must survive intact."""
        skill_dir = tmp_path / "planning"
        skill_dir.mkdir()
        skill_md = skill_dir / "SKILL.md"
        skill_md.write_text(
            "---\n"
            "name: planning\n"
            "description: Planning skill\n"
            "---\n"
            "\n"
            "```dot\n"
            "digraph planning {\n"
            "    node [shape=box];\n"
            "    a -> b;\n"
            "}\n"
            "```\n"
            "\n"
            "invoke `samsara:implement` to proceed.\n"
        )

        rules = [make_transition_rule()]
        converter = SkillConverter()
        result = converter.convert(skill_dir, rules, make_naming())

        content = result.skill_md_content
        assert "digraph planning {" in content, (
            "DC-SK-5: 'digraph' block header was corrupted."
        )
        assert "node [shape=box];" in content, (
            "DC-SK-5: Node attribute line was corrupted."
        )
