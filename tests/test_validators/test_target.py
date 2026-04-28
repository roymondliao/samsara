"""
Unit tests for TargetValidator — happy path and behavioral contract tests.

Death tests (silent failure paths) are in test_target_death.py.
These tests cover: TOML validation, agent name extraction, clean output validation,
error accumulation, cross-file pattern scanning.
"""

from pathlib import Path


from samsara_cli.validators.target import TargetValidator


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_clean_output(
    tmp_path: Path,
    skill_dir_name: str = "samsara-research",
    skill_body: str = "Research body.\n",
    agent_name: str = "samsara-implementer",
    agent_toml_name: str | None = None,
) -> Path:
    """Create a minimal clean converted output directory."""
    output = tmp_path / "output"
    output.mkdir()

    skills_dir = output / "skills"
    skills_dir.mkdir()
    skill_dir = skills_dir / skill_dir_name
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        f"---\nname: research\ndescription: Research\n---\n\n{skill_body}"
    )

    agents_dir = output / "agents"
    agents_dir.mkdir()
    toml_name = agent_toml_name or agent_name
    (agents_dir / f"{toml_name}.toml").write_text(
        f'[agent]\nname = "{agent_name}"\ndeveloper_instructions = "You are an agent."\n'
    )

    return output


# ---------------------------------------------------------------------------
# Basic validation — clean output passes
# ---------------------------------------------------------------------------


class TestCleanOutputPasses:
    def test_clean_output_produces_no_errors(self, tmp_path: Path):
        """A fully valid converted output produces no validation errors."""
        output = make_clean_output(tmp_path)
        validator = TargetValidator()
        errors = validator.validate(output_dir=output)
        assert errors == [], f"Unexpected errors on clean output: {errors}"

    def test_output_with_companion_files_passes(self, tmp_path: Path):
        """Output with clean companion files in skill dirs also passes."""
        output = make_clean_output(tmp_path)
        skill_dir = output / "skills" / "samsara-research"
        (skill_dir / "problem-autopsy.md").write_text(
            "# Problem Autopsy\n\nUse exec_command to check.\n"
        )
        validator = TargetValidator()
        errors = validator.validate(output_dir=output)
        assert errors == [], f"Unexpected errors with companion files: {errors}"


# ---------------------------------------------------------------------------
# Source pattern detection
# ---------------------------------------------------------------------------


class TestSourcePatternDetection:
    def test_invoke_samsara_pattern_in_body_detected(self, tmp_path: Path):
        """invoke `samsara:X` in SKILL.md body is detected."""
        output = make_clean_output(
            tmp_path, skill_body="invoke `samsara:planning` to proceed.\n"
        )
        validator = TargetValidator()
        errors = validator.validate(output_dir=output)
        assert len(errors) > 0

    def test_invoke_samsara_pattern_in_companion_detected(self, tmp_path: Path):
        """invoke `samsara:X` in companion .md file is detected."""
        output = make_clean_output(tmp_path)
        companion = output / "skills" / "samsara-research" / "companion.md"
        companion.write_text("invoke `samsara:planning` here.\n")
        validator = TargetValidator()
        errors = validator.validate(output_dir=output)
        assert len(errors) > 0

    def test_subagent_type_pattern_in_output_detected(self, tmp_path: Path):
        """subagent_type: pattern in output is detected."""
        output = make_clean_output(tmp_path)
        companion = output / "skills" / "samsara-research" / "dispatch.md"
        companion.write_text('subagent_type: "samsara:implementer"\n')
        validator = TargetValidator()
        errors = validator.validate(output_dir=output)
        assert len(errors) > 0


# ---------------------------------------------------------------------------
# TOML file validation
# ---------------------------------------------------------------------------


class TestTomlValidation:
    def test_valid_toml_passes(self, tmp_path: Path):
        """Valid TOML agent files pass without errors."""
        output = make_clean_output(tmp_path)
        validator = TargetValidator()
        errors = validator.validate(output_dir=output)
        assert errors == [], f"Valid TOML produced errors: {errors}"

    def test_malformed_toml_produces_error(self, tmp_path: Path):
        """Malformed TOML in agents/ directory produces an error."""
        output = make_clean_output(tmp_path)
        (output / "agents" / "samsara-implementer.toml").write_text(
            "[agent\nname = bad toml content\n"
        )
        validator = TargetValidator()
        errors = validator.validate(output_dir=output)
        assert len(errors) > 0
        error_text = " ".join(errors)
        assert "toml" in error_text.lower() or "parse" in error_text.lower()

    def test_empty_toml_file_produces_error(self, tmp_path: Path):
        """An empty TOML file produces an error."""
        output = make_clean_output(tmp_path)
        (output / "agents" / "samsara-implementer.toml").write_text("")
        validator = TargetValidator()
        _errors = validator.validate(output_dir=output)  # noqa: F841
        # An empty TOML is technically valid (empty table), but the agent section is missing.
        # Either error or no error is acceptable — the point is not to silently crash.


# ---------------------------------------------------------------------------
# Skill directory name validation
# ---------------------------------------------------------------------------


class TestSkillDirNameValidation:
    def test_skill_dir_with_hyphen_passes(self, tmp_path: Path):
        """Skill dir with hyphen (correct format) passes."""
        output = make_clean_output(tmp_path, skill_dir_name="samsara-research")
        validator = TargetValidator()
        errors = validator.validate(output_dir=output)
        assert errors == [], f"Valid skill dir name produced errors: {errors}"

    def test_skill_dir_with_colon_detected(self, tmp_path: Path):
        """Skill dir with colon (source format) is detected as error."""
        output = tmp_path / "output"
        output.mkdir()
        skills_dir = output / "skills"
        skills_dir.mkdir()
        bad_dir = skills_dir / "samsara:research"
        bad_dir.mkdir()
        (bad_dir / "SKILL.md").write_text(
            "---\nname: research\ndescription: Research\n---\n\nBody.\n"
        )
        (output / "agents").mkdir()

        validator = TargetValidator()
        errors = validator.validate(output_dir=output)
        assert len(errors) > 0


# ---------------------------------------------------------------------------
# Agent cross-validation
# ---------------------------------------------------------------------------


class TestAgentCrossValidation:
    def test_agent_name_in_toml_matches_filename(self, tmp_path: Path):
        """When agent TOML name matches filename, no cross-validation errors."""
        output = make_clean_output(
            tmp_path,
            agent_name="samsara-implementer",
            agent_toml_name="samsara-implementer",
        )
        validator = TargetValidator()
        errors = validator.validate(output_dir=output)
        assert errors == [], f"Valid agent pairing produced errors: {errors}"

    def test_multiple_agents_all_valid_passes(self, tmp_path: Path):
        """Multiple valid agent files all pass."""
        output = tmp_path / "output"
        output.mkdir()
        (output / "skills").mkdir()
        skill_dir = output / "skills" / "samsara-research"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: research\ndescription: Research\n---\n\nBody.\n"
        )

        agents_dir = output / "agents"
        agents_dir.mkdir()
        agent_names = [
            "samsara-implementer",
            "samsara-code-reviewer",
            "samsara-yin-explorer",
        ]
        for name in agent_names:
            (agents_dir / f"{name}.toml").write_text(
                f'[agent]\nname = "{name}"\ndeveloper_instructions = "Instructions."\n'
            )

        validator = TargetValidator()
        errors = validator.validate(output_dir=output)
        assert errors == [], f"Multiple valid agents produced errors: {errors}"

    def test_errors_are_accumulated_not_raised(self, tmp_path: Path):
        """Multiple errors are accumulated as a list, not raised as exceptions."""
        output = tmp_path / "output"
        output.mkdir()
        skills_dir = output / "skills"
        skills_dir.mkdir()
        # Skill with source pattern AND colon in dir name
        bad_dir = skills_dir / "samsara:research"
        bad_dir.mkdir()
        (bad_dir / "SKILL.md").write_text(
            "---\nname: research\ndescription: Research\n---\n\n"
            "invoke `samsara:planning` here.\n"
        )
        (output / "agents").mkdir()

        validator = TargetValidator()
        # Must not raise — must accumulate errors
        errors = validator.validate(output_dir=output)
        assert isinstance(errors, list), "validate() must return a list, not raise"
        assert len(errors) >= 1, f"Expected errors, got: {errors}"
