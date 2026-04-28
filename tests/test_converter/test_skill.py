"""
Unit tests for SkillConverter — happy path and behavioral contract tests.

Death tests (silent failure paths) are in test_skill_death.py.
These tests cover: naming convention, skill conversion pipeline, companion file
handling, ConvertedSkill result structure, and all 11 skill transformation targets.
"""

from pathlib import Path

import pytest

from samsara_cli.config.schema import NamingConfig, TransformationRule
from samsara_cli.converter.skill import ConversionError, ConvertedSkill, SkillConverter


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


def make_naming(prefix: str = "samsara", separator: str = "-") -> NamingConfig:
    return NamingConfig(skill_prefix=prefix, separator=separator)


def make_skill_dir(tmp_path: Path, name: str, description: str, body: str) -> Path:
    """Create a minimal skill directory with SKILL.md."""
    skill_dir = tmp_path / name
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: {description}\n---\n\n{body}\n"
    )
    return skill_dir


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
        id="task_create",
        scope="body",
        type="regex",
        match=r"TaskCreate\b",
        replace="update_plan",
        priority="medium",
    ),
    TransformationRule(
        id="task_update",
        scope="body",
        type="regex",
        match=r"TaskUpdate\b",
        replace="update_plan",
        priority="medium",
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
        id="tool_edit",
        scope="body",
        type="literal",
        match="Edit tool",
        replace="apply_patch",
        priority="medium",
    ),
    TransformationRule(
        id="tool_write",
        scope="body",
        type="literal",
        match="Write tool",
        replace="apply_patch",
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
    TransformationRule(
        id="tool_ls",
        scope="body",
        type="literal",
        match="LS tool",
        replace="exec_command with ls/find",
        priority="medium",
    ),
    TransformationRule(
        id="tool_grep",
        scope="body",
        type="literal",
        match="Grep tool",
        replace="exec_command with rg",
        priority="medium",
    ),
    TransformationRule(
        id="tool_glob",
        scope="body",
        type="literal",
        match="Glob tool",
        replace="exec_command with find/rg --files",
        priority="medium",
    ),
]


# ---------------------------------------------------------------------------
# UT-SK-1: SkillConverter construction and basic interface
# ---------------------------------------------------------------------------


class TestSkillConverterInterface:
    def test_skill_converter_is_instantiable(self):
        """SkillConverter can be instantiated with no arguments."""
        converter = SkillConverter()
        assert converter is not None

    def test_convert_returns_converted_skill(self, tmp_path: Path):
        """convert() returns a ConvertedSkill instance."""
        skill_dir = make_skill_dir(tmp_path, "research", "Research skill", "# Body\n")
        converter = SkillConverter()
        result = converter.convert(skill_dir, [], make_naming())
        assert isinstance(result, ConvertedSkill)

    def test_converted_skill_has_expected_fields(self, tmp_path: Path):
        """ConvertedSkill exposes: name, description, skill_md_content, output_dir_name, companion_files."""
        skill_dir = make_skill_dir(
            tmp_path, "planning", "Planning skill", "# Planning body\n"
        )
        converter = SkillConverter()
        result = converter.convert(skill_dir, [], make_naming())

        assert hasattr(result, "name")
        assert hasattr(result, "description")
        assert hasattr(result, "skill_md_content")
        assert hasattr(result, "output_dir_name")
        assert hasattr(result, "companion_files")


# ---------------------------------------------------------------------------
# UT-SK-2: Naming convention — colon to hyphen
# ---------------------------------------------------------------------------


class TestNamingConvention:
    def test_output_dir_name_uses_separator_not_colon(self, tmp_path: Path):
        """
        Source skill directory 'research' with prefix='samsara' separator='-'
        produces output_dir_name 'samsara-research'.
        """
        skill_dir = make_skill_dir(tmp_path, "research", "Research skill", "# Body\n")
        converter = SkillConverter()
        result = converter.convert(skill_dir, [], make_naming())

        assert result.output_dir_name == "samsara-research", (
            f"Expected 'samsara-research', got: {result.output_dir_name!r}"
        )

    def test_naming_with_hyphenated_skill_name(self, tmp_path: Path):
        """Skill with hyphenated name: 'security-privacy-review' -> 'samsara-security-privacy-review'."""
        skill_dir = make_skill_dir(
            tmp_path, "security-privacy-review", "Security review", "# Body\n"
        )
        converter = SkillConverter()
        result = converter.convert(skill_dir, [], make_naming())

        assert result.output_dir_name == "samsara-security-privacy-review", (
            f"Got: {result.output_dir_name!r}"
        )

    def test_naming_uses_skill_md_name_field_not_dir_name(self, tmp_path: Path):
        """
        output_dir_name is derived from the skill's SKILL.md frontmatter `name` field,
        not the source directory name. If they differ, frontmatter wins.
        """
        skill_dir = tmp_path / "some-dir-name"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: research\ndescription: Research skill\n---\n\n# Research\n"
        )
        converter = SkillConverter()
        result = converter.convert(skill_dir, [], make_naming())

        # output_dir_name uses name from frontmatter, not dir name
        assert result.output_dir_name == "samsara-research", (
            f"output_dir_name should use frontmatter name 'research'. Got: {result.output_dir_name!r}"
        )

    def test_naming_config_separator_is_respected(self, tmp_path: Path):
        """Custom separator in NamingConfig is used in output_dir_name."""
        skill_dir = make_skill_dir(tmp_path, "research", "Research skill", "# Body\n")
        converter = SkillConverter()
        # Use underscore separator
        result = converter.convert(skill_dir, [], make_naming(separator="_"))

        assert result.output_dir_name == "samsara_research", (
            f"Custom separator '_' not used. Got: {result.output_dir_name!r}"
        )


# ---------------------------------------------------------------------------
# UT-SK-3: Body transformation
# ---------------------------------------------------------------------------


class TestBodyTransformation:
    def test_body_rule_applied_to_skill_body(self, tmp_path: Path):
        """Body-scoped rule transforms body content in SKILL.md."""
        skill_dir = make_skill_dir(
            tmp_path, "research", "Research skill", "Use the Read tool to read files.\n"
        )
        rules = [make_rule(match="Read tool", replace="file reading")]
        converter = SkillConverter()
        result = converter.convert(skill_dir, rules, make_naming())

        assert "file reading" in result.skill_md_content
        assert "Read tool" not in result.skill_md_content.split("---", 2)[2], (
            "Read tool should be converted in body section"
        )

    def test_skill_invocation_rule_converts_transition(self, tmp_path: Path):
        """The skill_invocation regex rule converts transition statements in body."""
        skill_dir = make_skill_dir(
            tmp_path,
            "research",
            "Research skill",
            "After work, invoke `samsara:planning` to plan.\n",
        )
        rules = [
            TransformationRule(
                id="skill_invocation",
                scope="body",
                type="regex",
                match=r"invoke `samsara:([\w-]+)`",
                replace=r"use the `$samsara-\1` skill",
                priority="high",
            )
        ]
        converter = SkillConverter()
        result = converter.convert(skill_dir, rules, make_naming())

        body = result.skill_md_content.split("---", 2)[2]
        assert "use the `$samsara-planning` skill" in body
        assert "invoke `samsara:planning`" not in body

    def test_agent_dispatch_rule_converts_subagent_type(self, tmp_path: Path):
        """agent_dispatch_subagent_type rule converts subagent_type field."""
        skill_dir = make_skill_dir(
            tmp_path,
            "implement",
            "Implement skill",
            'Use subagent_type: "samsara:implementer" for dispatch.\n',
        )
        rules = [
            TransformationRule(
                id="agent_dispatch_subagent_type",
                scope="body",
                type="regex",
                match=r'subagent_type: "samsara:([\w-]+)"',
                replace=r'agent named "samsara-\1"',
                priority="high",
            )
        ]
        converter = SkillConverter()
        result = converter.convert(skill_dir, rules, make_naming())

        body = result.skill_md_content.split("---", 2)[2]
        assert 'agent named "samsara-implementer"' in body
        assert 'subagent_type: "samsara:implementer"' not in body

    def test_task_create_rule_converts_to_update_plan(self, tmp_path: Path):
        """TaskCreate rule converts to update_plan."""
        skill_dir = make_skill_dir(
            tmp_path,
            "implement",
            "Implement skill",
            "Use TaskCreate to create tasks and TaskUpdate to update them.\n",
        )
        rules = [
            TransformationRule(
                id="task_create",
                scope="body",
                type="regex",
                match=r"TaskCreate\b",
                replace="update_plan",
                priority="medium",
            ),
            TransformationRule(
                id="task_update",
                scope="body",
                type="regex",
                match=r"TaskUpdate\b",
                replace="update_plan",
                priority="medium",
            ),
        ]
        converter = SkillConverter()
        result = converter.convert(skill_dir, rules, make_naming())

        body = result.skill_md_content.split("---", 2)[2]
        assert "TaskCreate" not in body
        assert "TaskUpdate" not in body
        assert body.count("update_plan") == 2

    def test_all_tool_rules_apply_to_body(self, tmp_path: Path):
        """All 7 tool-name rules apply correctly to body content."""
        skill_dir = make_skill_dir(
            tmp_path,
            "implement",
            "Implement skill",
            "Use Read tool, Edit tool, Write tool, Bash tool, LS tool, Grep tool, Glob tool.\n",
        )
        converter = SkillConverter()
        result = converter.convert(skill_dir, CODEX_RULES, make_naming())

        body = result.skill_md_content.split("---", 2)[2]
        for tool_name in [
            "Read tool",
            "Edit tool",
            "Write tool",
            "Bash tool",
            "LS tool",
            "Grep tool",
            "Glob tool",
        ]:
            assert tool_name not in body, f"{tool_name!r} not converted in body"


# ---------------------------------------------------------------------------
# UT-SK-4: Frontmatter parsing and preservation
# ---------------------------------------------------------------------------


class TestFrontmatterParsing:
    def test_name_extracted_from_frontmatter(self, tmp_path: Path):
        """name field is correctly extracted from SKILL.md frontmatter."""
        skill_dir = make_skill_dir(
            tmp_path, "research", "Use when starting new work", "# Body\n"
        )
        converter = SkillConverter()
        result = converter.convert(skill_dir, [], make_naming())

        assert result.name == "research"

    def test_description_extracted_from_frontmatter(self, tmp_path: Path):
        """description field is correctly extracted from SKILL.md frontmatter."""
        skill_dir = make_skill_dir(
            tmp_path, "research", "Use when starting new feature work", "# Body\n"
        )
        converter = SkillConverter()
        result = converter.convert(skill_dir, [], make_naming())

        assert result.description == "Use when starting new feature work"

    def test_frontmatter_preserved_in_output_content(self, tmp_path: Path):
        """Output SKILL.md content retains frontmatter delimiters and fields."""
        skill_dir = make_skill_dir(
            tmp_path, "planning", "Planning skill", "# Planning body\n"
        )
        converter = SkillConverter()
        result = converter.convert(skill_dir, [], make_naming())

        content = result.skill_md_content
        assert content.startswith("---\n"), (
            "Output must start with frontmatter delimiter"
        )
        assert "name: planning" in content
        assert "description: Planning skill" in content

    def test_body_rules_do_not_bleed_into_frontmatter(self, tmp_path: Path):
        """
        Body rules that match text appearing in both frontmatter and body
        must only transform the body section.
        """
        skill_dir = tmp_path / "research"
        skill_dir.mkdir()
        # frontmatter description contains 'Read tool' — body rule must NOT touch it
        (skill_dir / "SKILL.md").write_text(
            "---\n"
            "name: research\n"
            "description: Use for Read tool investigations\n"
            "---\n"
            "\n"
            "Use the Read tool to read files.\n"
        )

        rules = [make_rule(match="Read tool", replace="file reading")]
        converter = SkillConverter()
        result = converter.convert(skill_dir, rules, make_naming())

        # frontmatter description must be unchanged
        assert result.description == "Use for Read tool investigations", (
            f"Frontmatter description was modified. Got: {result.description!r}"
        )
        # body must be transformed
        body = result.skill_md_content.split("---", 2)[2]
        assert "file reading" in body
        assert "Read tool" not in body


# ---------------------------------------------------------------------------
# UT-SK-5: Companion file handling
# ---------------------------------------------------------------------------


class TestCompanionFileHandling:
    def test_companion_md_included_in_results(self, tmp_path: Path):
        """Companion .md files in skill dir appear in companion_files dict."""
        skill_dir = make_skill_dir(tmp_path, "research", "Research", "# Body\n")
        (skill_dir / "problem-autopsy.md").write_text("# Autopsy\n\nSome content.\n")

        converter = SkillConverter()
        result = converter.convert(skill_dir, [], make_naming())

        assert "problem-autopsy.md" in result.companion_files

    def test_companion_md_has_body_rules_applied(self, tmp_path: Path):
        """Companion .md files have body rules applied to their content."""
        skill_dir = make_skill_dir(tmp_path, "research", "Research", "# Body\n")
        (skill_dir / "problem-autopsy.md").write_text(
            "# Autopsy\n\nUse the Read tool here.\n"
        )

        rules = [make_rule(match="Read tool", replace="file reading")]
        converter = SkillConverter()
        result = converter.convert(skill_dir, rules, make_naming())

        autopsy_content = result.companion_files["problem-autopsy.md"]
        assert "file reading" in autopsy_content
        assert "Read tool" not in autopsy_content

    def test_yaml_files_copied_without_rule_application(self, tmp_path: Path):
        """YAML companion files (.yaml) are copied as-is — no rules applied."""
        skill_dir = make_skill_dir(tmp_path, "implement", "Implement", "# Body\n")
        templates_dir = skill_dir / "templates"
        templates_dir.mkdir()
        original_content = (
            "# Schema\nread_tool: Read tool reference\nfields:\n  - name: read_tool\n"
        )
        (templates_dir / "scar-schema.yaml").write_text(original_content)

        rules = [make_rule(match="Read tool", replace="file reading")]
        converter = SkillConverter()
        result = converter.convert(skill_dir, rules, make_naming())

        yaml_content = result.companion_files["templates/scar-schema.yaml"]
        assert yaml_content == original_content, (
            "YAML file content was modified — should be copied as-is"
        )

    def test_nested_companion_md_in_templates_has_rules_applied(self, tmp_path: Path):
        """Nested .md files in templates/ subdirectory have rules applied."""
        skill_dir = make_skill_dir(tmp_path, "research", "Research", "# Body\n")
        templates_dir = skill_dir / "templates"
        templates_dir.mkdir()
        (templates_dir / "kickoff.md").write_text(
            "# Kickoff Template\n\nUse Read tool to start.\n"
        )

        rules = [make_rule(match="Read tool", replace="file reading")]
        converter = SkillConverter()
        result = converter.convert(skill_dir, rules, make_naming())

        kickoff_content = result.companion_files["templates/kickoff.md"]
        assert "file reading" in kickoff_content
        assert "Read tool" not in kickoff_content

    def test_skill_md_not_in_companion_files(self, tmp_path: Path):
        """SKILL.md itself must not appear in companion_files — it has its own field."""
        skill_dir = make_skill_dir(tmp_path, "research", "Research", "# Body\n")

        converter = SkillConverter()
        result = converter.convert(skill_dir, [], make_naming())

        assert "SKILL.md" not in result.companion_files

    def test_skill_dir_with_no_companions_has_empty_companion_files(
        self, tmp_path: Path
    ):
        """Skill directory with only SKILL.md produces empty companion_files dict."""
        skill_dir = make_skill_dir(tmp_path, "fast-track", "Fast track", "# Body\n")

        converter = SkillConverter()
        result = converter.convert(skill_dir, [], make_naming())

        assert result.companion_files == {}

    def test_non_md_non_yaml_files_copied_as_is(self, tmp_path: Path):
        """Non-.md, non-.yaml files (images, etc.) are included without modification."""
        skill_dir = make_skill_dir(tmp_path, "research", "Research", "# Body\n")
        # Hypothetical binary-like file
        (skill_dir / "diagram.png.txt").write_text("binary-like-content")

        converter = SkillConverter()
        result = converter.convert(skill_dir, [], make_naming())

        assert "diagram.png.txt" in result.companion_files
        assert result.companion_files["diagram.png.txt"] == "binary-like-content"


# ---------------------------------------------------------------------------
# UT-SK-6: All 11 skills — key transformation points
# ---------------------------------------------------------------------------


class TestAllElevenSkills:
    """
    Verify key transformation points for each of the 11 actual samsara skills.
    These tests use minimal synthetic SKILL.md content that mirrors the real
    patterns found in each skill (verified by reading the actual files).
    """

    def test_samsara_bootstrap_routing_transitions_converted(self, tmp_path: Path):
        """samsara-bootstrap: routing transitions like invoke `samsara:research` are converted."""
        skill_dir = make_skill_dir(
            tmp_path,
            "samsara-bootstrap",
            "Boot skill",
            "invoke `samsara:research` for new work.\n"
            "invoke `samsara:debugging` for bugs.\n",
        )
        rules = [
            TransformationRule(
                id="skill_invocation",
                scope="body",
                type="regex",
                match=r"invoke `samsara:([\w-]+)`",
                replace=r"use the `$samsara-\1` skill",
                priority="high",
            )
        ]
        converter = SkillConverter()
        result = converter.convert(skill_dir, rules, make_naming())

        body = result.skill_md_content.split("---", 2)[2]
        assert "invoke `samsara:research`" not in body
        assert "invoke `samsara:debugging`" not in body
        assert "use the `$samsara-research` skill" in body
        assert "use the `$samsara-debugging` skill" in body

    def test_research_transitions_converted(self, tmp_path: Path):
        """research: invoke `samsara:planning` transition converted."""
        skill_dir = make_skill_dir(
            tmp_path,
            "research",
            "Research skill",
            "使用者確認後，invoke `samsara:planning` skill。\n",
        )
        # skill_invocation_variant matches 'invoke `samsara:X` skill'
        rules = [
            TransformationRule(
                id="skill_invocation",
                scope="body",
                type="regex",
                match=r"invoke `samsara:([\w-]+)`",
                replace=r"use the `$samsara-\1` skill",
                priority="high",
            ),
        ]
        converter = SkillConverter()
        result = converter.convert(skill_dir, rules, make_naming())

        body = result.skill_md_content.split("---", 2)[2]
        assert "invoke `samsara:planning`" not in body

    def test_planning_transitions_converted(self, tmp_path: Path):
        """planning: invoke `samsara:implement` transition converted."""
        skill_dir = make_skill_dir(
            tmp_path,
            "planning",
            "Planning skill",
            "使用者確認後，invoke `samsara:implement` skill。\n",
        )
        rules = [
            TransformationRule(
                id="skill_invocation",
                scope="body",
                type="regex",
                match=r"invoke `samsara:([\w-]+)`",
                replace=r"use the `$samsara-\1` skill",
                priority="high",
            )
        ]
        converter = SkillConverter()
        result = converter.convert(skill_dir, rules, make_naming())

        body = result.skill_md_content.split("---", 2)[2]
        assert "invoke `samsara:implement`" not in body

    def test_implement_subagent_type_converted(self, tmp_path: Path):
        """implement: subagent_type and Agent tool references converted."""
        skill_dir = make_skill_dir(
            tmp_path,
            "implement",
            "Implement skill",
            'Use subagent_type: "samsara:implementer" dispatch.\n'
            "Create tasks with TaskCreate and update with TaskUpdate.\n",
        )
        converter = SkillConverter()
        result = converter.convert(skill_dir, CODEX_RULES, make_naming())

        body = result.skill_md_content.split("---", 2)[2]
        assert 'subagent_type: "samsara:implementer"' not in body
        assert 'agent named "samsara-implementer"' in body
        assert "TaskCreate" not in body
        assert "TaskUpdate" not in body
        assert "update_plan" in body

    def test_iteration_transitions_converted(self, tmp_path: Path):
        """iteration: invoke `samsara:security-privacy-review` converted."""
        skill_dir = make_skill_dir(
            tmp_path,
            "iteration",
            "Iteration skill",
            "After iteration, invoke `samsara:security-privacy-review`.\n",
        )
        rules = [
            TransformationRule(
                id="skill_invocation",
                scope="body",
                type="regex",
                match=r"invoke `samsara:([\w-]+)`",
                replace=r"use the `$samsara-\1` skill",
                priority="high",
            )
        ]
        converter = SkillConverter()
        result = converter.convert(skill_dir, rules, make_naming())

        body = result.skill_md_content.split("---", 2)[2]
        assert "invoke `samsara:security-privacy-review`" not in body
        assert "use the `$samsara-security-privacy-review` skill" in body

    def test_security_privacy_review_tool_refs_converted(self, tmp_path: Path):
        """security-privacy-review: tool references in body converted."""
        skill_dir = make_skill_dir(
            tmp_path,
            "security-privacy-review",
            "Security review",
            "Use Read tool for audit. Use Bash tool for checks.\n",
        )
        converter = SkillConverter()
        result = converter.convert(skill_dir, CODEX_RULES, make_naming())

        body = result.skill_md_content.split("---", 2)[2]
        assert "Read tool" not in body
        assert "Bash tool" not in body

    def test_validate_and_ship_transition_converted(self, tmp_path: Path):
        """validate-and-ship: any transition invocations are converted."""
        skill_dir = make_skill_dir(
            tmp_path,
            "validate-and-ship",
            "Validate skill",
            "invoke `samsara:iteration` if iteration needed.\n",
        )
        rules = [
            TransformationRule(
                id="skill_invocation",
                scope="body",
                type="regex",
                match=r"invoke `samsara:([\w-]+)`",
                replace=r"use the `$samsara-\1` skill",
                priority="high",
            )
        ]
        converter = SkillConverter()
        result = converter.convert(skill_dir, rules, make_naming())

        body = result.skill_md_content.split("---", 2)[2]
        assert "invoke `samsara:iteration`" not in body

    def test_fast_track_tool_refs_converted(self, tmp_path: Path):
        """fast-track: tool references in body converted."""
        skill_dir = make_skill_dir(
            tmp_path,
            "fast-track",
            "Fast track skill",
            "Run tests with Bash tool. Read files with Read tool.\n",
        )
        converter = SkillConverter()
        result = converter.convert(skill_dir, CODEX_RULES, make_naming())

        body = result.skill_md_content.split("---", 2)[2]
        assert "Bash tool" not in body
        assert "Read tool" not in body
        assert "exec_command" in body

    def test_debugging_tool_refs_converted(self, tmp_path: Path):
        """debugging: all tool references converted."""
        skill_dir = make_skill_dir(
            tmp_path,
            "debugging",
            "Debugging skill",
            "Use Read tool, Bash tool, Grep tool, Glob tool.\n",
        )
        converter = SkillConverter()
        result = converter.convert(skill_dir, CODEX_RULES, make_naming())

        body = result.skill_md_content.split("---", 2)[2]
        for tool in ["Read tool", "Bash tool", "Grep tool", "Glob tool"]:
            assert tool not in body

    def test_codebase_map_tool_refs_converted(self, tmp_path: Path):
        """codebase-map: tool references in body converted."""
        skill_dir = make_skill_dir(
            tmp_path,
            "codebase-map",
            "Codebase map skill",
            "Use Glob tool to find files. Read files with Read tool.\n",
        )
        converter = SkillConverter()
        result = converter.convert(skill_dir, CODEX_RULES, make_naming())

        body = result.skill_md_content.split("---", 2)[2]
        assert "Glob tool" not in body
        assert "Read tool" not in body

    def test_writing_skills_references_converted(self, tmp_path: Path):
        """writing-skills: any skill invocations or tool refs converted."""
        skill_dir = make_skill_dir(
            tmp_path,
            "writing-skills",
            "Writing skills",
            "Use Write tool to produce output.\n",
        )
        converter = SkillConverter()
        result = converter.convert(skill_dir, CODEX_RULES, make_naming())

        body = result.skill_md_content.split("---", 2)[2]
        assert "Write tool" not in body
        assert "apply_patch" in body


# ---------------------------------------------------------------------------
# UT-SK-7: Error handling
# ---------------------------------------------------------------------------


class TestErrorHandling:
    def test_missing_skill_md_raises_error(self, tmp_path: Path):
        """Skill directory without SKILL.md raises ConversionError."""
        skill_dir = tmp_path / "bad-skill"
        skill_dir.mkdir()
        # No SKILL.md

        converter = SkillConverter()
        with pytest.raises((ConversionError, FileNotFoundError)):
            converter.convert(skill_dir, [], make_naming())

    def test_skill_md_without_frontmatter_raises_error(self, tmp_path: Path):
        """SKILL.md without frontmatter (no --- delimiters) raises ConversionError."""
        skill_dir = tmp_path / "bad-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "# No frontmatter here\n\nJust body content.\n"
        )

        converter = SkillConverter()
        with pytest.raises(ConversionError, match=r"frontmatter"):
            converter.convert(skill_dir, [], make_naming())

    def test_skill_md_with_missing_name_raises_error(self, tmp_path: Path):
        """SKILL.md frontmatter missing 'name' field raises ConversionError."""
        skill_dir = tmp_path / "bad-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\ndescription: A skill\n---\n\n# Body\n"
        )

        converter = SkillConverter()
        with pytest.raises(ConversionError, match=r"name"):
            converter.convert(skill_dir, [], make_naming())

    def test_skill_dir_not_existing_raises_error(self, tmp_path: Path):
        """Non-existent skill directory raises ConversionError or FileNotFoundError."""
        nonexistent = tmp_path / "does-not-exist"

        converter = SkillConverter()
        with pytest.raises((ConversionError, FileNotFoundError)):
            converter.convert(nonexistent, [], make_naming())


# ---------------------------------------------------------------------------
# UT-SK-8: ConvertedSkill structure
# ---------------------------------------------------------------------------


class TestConvertedSkillStructure:
    def test_skill_md_content_is_complete_document(self, tmp_path: Path):
        """skill_md_content is the complete transformed SKILL.md text, not just body."""
        skill_dir = make_skill_dir(
            tmp_path, "research", "Research skill", "# Research body\n"
        )
        converter = SkillConverter()
        result = converter.convert(skill_dir, [], make_naming())

        # Must contain frontmatter and body
        assert "---" in result.skill_md_content
        assert "# Research body" in result.skill_md_content

    def test_companion_files_keys_are_relative_paths(self, tmp_path: Path):
        """companion_files dict keys are relative paths from skill dir root."""
        skill_dir = make_skill_dir(tmp_path, "research", "Research", "# Body\n")
        templates_dir = skill_dir / "templates"
        templates_dir.mkdir()
        (templates_dir / "kickoff.md").write_text("# Kickoff\n")
        (skill_dir / "problem-autopsy.md").write_text("# Autopsy\n")

        converter = SkillConverter()
        result = converter.convert(skill_dir, [], make_naming())

        # Keys must be relative to skill dir root
        assert "problem-autopsy.md" in result.companion_files
        assert "templates/kickoff.md" in result.companion_files

        # No absolute paths
        for key in result.companion_files:
            assert not key.startswith("/"), f"Companion file key is absolute: {key!r}"
