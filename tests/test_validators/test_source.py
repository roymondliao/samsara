"""
Unit tests for SourceValidator — happy path and behavioral contract tests.

Death tests (silent failure paths) are in test_source_death.py.
These tests cover: basic validation behavior, multi-skill validation, agent file
checks, hooks checks, and the shape of ValidationError reporting.
"""

import json
from pathlib import Path


from samsara_cli.validators.source import SourceValidator


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_full_source(
    tmp_path: Path,
    skill_names: list[str] | None = None,
    agent_names: list[str] | None = None,
    include_hooks_json: bool = True,
    include_plugin_json: bool = True,
    plugin_json_content: dict | None = None,
) -> Path:
    """Create a full valid samsara source directory."""
    source = tmp_path / "source"

    plugin_dir = source / ".claude-plugin"
    plugin_dir.mkdir(parents=True)
    if include_plugin_json:
        content = plugin_json_content or {"name": "samsara", "version": "0.8.0"}
        (plugin_dir / "plugin.json").write_text(json.dumps(content))

    skills_dir = source / "skills"
    skills_dir.mkdir()
    for skill_name in skill_names or ["research"]:
        skill_dir = skills_dir / skill_name
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            f"---\nname: {skill_name}\ndescription: Skill {skill_name}\n---\n\n# {skill_name}\n"
        )

    agents_dir = source / "agents"
    agents_dir.mkdir()
    for agent_name in agent_names or ["implementer"]:
        (agents_dir / f"{agent_name}.md").write_text(
            f"# {agent_name}\n\nYou are the {agent_name} agent.\n"
        )

    hooks_dir = source / "hooks"
    hooks_dir.mkdir()
    if include_hooks_json:
        (hooks_dir / "hooks.json").write_text(json.dumps({"hooks": []}))

    references_dir = source / "references"
    references_dir.mkdir()
    (references_dir / "code-review.md").write_text("# Code Review\n\nReference.\n")

    return source


# ---------------------------------------------------------------------------
# Basic validation — structure presence
# ---------------------------------------------------------------------------


class TestBasicStructureValidation:
    def test_valid_source_produces_no_errors(self, tmp_path: Path):
        """A fully valid source structure produces no validation errors."""
        source = make_full_source(tmp_path, skill_names=["research", "planning"])
        validator = SourceValidator()
        errors = validator.validate(
            source_dir=source, expected_skills=["research", "planning"]
        )
        assert errors == [], f"Unexpected errors: {errors}"

    def test_missing_plugin_dir_produces_error(self, tmp_path: Path):
        """If .claude-plugin directory is missing, error is reported."""
        source = make_full_source(tmp_path)
        import shutil

        shutil.rmtree(source / ".claude-plugin")
        validator = SourceValidator()
        errors = validator.validate(source_dir=source, expected_skills=["research"])
        assert len(errors) > 0
        error_text = " ".join(errors)
        assert ".claude-plugin" in error_text or "plugin" in error_text.lower()

    def test_missing_skills_dir_produces_error(self, tmp_path: Path):
        """If skills/ directory is missing, error is reported."""
        source = make_full_source(tmp_path)
        import shutil

        shutil.rmtree(source / "skills")
        validator = SourceValidator()
        errors = validator.validate(source_dir=source, expected_skills=["research"])
        assert len(errors) > 0
        error_text = " ".join(errors)
        assert "skills" in error_text.lower()

    def test_missing_agents_dir_produces_error(self, tmp_path: Path):
        """If agents/ directory is missing, error is reported."""
        source = make_full_source(tmp_path)
        import shutil

        shutil.rmtree(source / "agents")
        validator = SourceValidator()
        errors = validator.validate(source_dir=source, expected_skills=["research"])
        assert len(errors) > 0
        error_text = " ".join(errors)
        assert "agents" in error_text.lower()

    def test_missing_hooks_dir_produces_error(self, tmp_path: Path):
        """If hooks/ directory is missing, error is reported."""
        source = make_full_source(tmp_path)
        import shutil

        shutil.rmtree(source / "hooks")
        validator = SourceValidator()
        errors = validator.validate(source_dir=source, expected_skills=["research"])
        assert len(errors) > 0
        error_text = " ".join(errors)
        assert "hooks" in error_text.lower()


# ---------------------------------------------------------------------------
# Skill validation
# ---------------------------------------------------------------------------


class TestSkillValidation:
    def test_all_expected_skills_present_produces_no_errors(self, tmp_path: Path):
        """When all expected skills are present with SKILL.md, no errors."""
        skill_names = ["research", "planning", "implement", "debugging"]
        source = make_full_source(tmp_path, skill_names=skill_names)
        validator = SourceValidator()
        errors = validator.validate(source_dir=source, expected_skills=skill_names)
        assert errors == [], f"Unexpected errors: {errors}"

    def test_extra_skills_not_in_expected_list_do_not_cause_error(self, tmp_path: Path):
        """Extra skills in source (not in expected list) do not cause errors."""
        source = make_full_source(tmp_path, skill_names=["research", "extra-skill"])
        validator = SourceValidator()
        # Only expect research — extra-skill is bonus, not an error
        errors = validator.validate(source_dir=source, expected_skills=["research"])
        assert errors == [], f"Extra skills should not cause errors: {errors}"

    def test_empty_expected_skills_passes(self, tmp_path: Path):
        """Empty expected_skills list means no skill validation — passes."""
        source = make_full_source(tmp_path, skill_names=["research"])
        validator = SourceValidator()
        errors = validator.validate(source_dir=source, expected_skills=[])
        assert errors == [], f"Empty expected skills should always pass: {errors}"


# ---------------------------------------------------------------------------
# Agent file validation
# ---------------------------------------------------------------------------


class TestAgentFileValidation:
    def test_no_md_files_in_agents_dir_produces_error(self, tmp_path: Path):
        """If agents/ dir exists but has no .md files, error is reported."""
        source = make_full_source(tmp_path)
        # Remove all agent .md files
        for f in (source / "agents").iterdir():
            f.unlink()

        validator = SourceValidator()
        errors = validator.validate(source_dir=source, expected_skills=["research"])
        assert len(errors) > 0
        error_text = " ".join(errors)
        assert "agent" in error_text.lower()

    def test_agents_with_md_files_passes(self, tmp_path: Path):
        """agents/ dir with .md files passes validation."""
        source = make_full_source(
            tmp_path,
            agent_names=["implementer", "code-reviewer"],
        )
        validator = SourceValidator()
        errors = validator.validate(source_dir=source, expected_skills=["research"])
        assert errors == [], f"Unexpected errors: {errors}"


# ---------------------------------------------------------------------------
# Hooks validation
# ---------------------------------------------------------------------------


class TestHooksValidation:
    def test_hooks_json_missing_produces_error(self, tmp_path: Path):
        """If hooks/hooks.json is missing, error is reported."""
        source = make_full_source(tmp_path, include_hooks_json=False)
        validator = SourceValidator()
        errors = validator.validate(source_dir=source, expected_skills=["research"])
        assert len(errors) > 0
        error_text = " ".join(errors)
        assert "hooks.json" in error_text or "hooks" in error_text.lower()


# ---------------------------------------------------------------------------
# Plugin.json validation
# ---------------------------------------------------------------------------


class TestPluginJsonValidation:
    def test_valid_plugin_json_passes(self, tmp_path: Path):
        """plugin.json with name and version passes validation."""
        source = make_full_source(
            tmp_path,
            plugin_json_content={"name": "samsara", "version": "0.8.0"},
        )
        validator = SourceValidator()
        errors = validator.validate(source_dir=source, expected_skills=["research"])
        assert errors == [], f"Unexpected errors: {errors}"

    def test_plugin_json_with_extra_fields_passes(self, tmp_path: Path):
        """plugin.json with extra fields beyond required ones still passes."""
        source = make_full_source(
            tmp_path,
            plugin_json_content={
                "name": "samsara",
                "version": "0.8.0",
                "description": "A plugin",
                "author": {"name": "Someone"},
            },
        )
        validator = SourceValidator()
        errors = validator.validate(source_dir=source, expected_skills=["research"])
        assert errors == [], f"Unexpected errors: {errors}"

    def test_plugin_json_malformed_produces_error(self, tmp_path: Path):
        """Malformed JSON in plugin.json produces an error."""
        source = make_full_source(tmp_path)
        (source / ".claude-plugin" / "plugin.json").write_text("{broken json")
        validator = SourceValidator()
        errors = validator.validate(source_dir=source, expected_skills=["research"])
        assert len(errors) > 0

    def test_errors_accumulated_not_raised(self, tmp_path: Path):
        """Multiple validation errors are accumulated and returned as a list, not raised."""
        source = make_full_source(tmp_path)
        # Remove plugin.json AND remove a skill dir
        (source / ".claude-plugin" / "plugin.json").unlink()
        import shutil

        shutil.rmtree(source / "skills" / "research")

        # Create the skills dir with no skills
        expected_skills = ["research", "planning"]

        validator = SourceValidator()
        # Should not raise — should accumulate errors
        errors = validator.validate(source_dir=source, expected_skills=expected_skills)
        # Multiple errors should be reported
        assert len(errors) >= 2, f"Expected multiple errors, got: {errors}"
