"""
Death tests for TargetValidator — targeting silent failure paths.

Each test names the specific silent failure path it guards against.
Death tests run before unit tests. They must fail red before implementation.

Silent failures guarded:
  DC-7-2: Target validator must detect unconverted "invoke `samsara:X`" pattern
           in ANY output file — not just SKILL.md. A broken chain link is the
           highest-severity production failure.
  DC-7-3: Target validator must detect agent name mismatch — skill references
           "samsara-implementer" but agent file is "implementer.toml" (no prefix).
  DTV-1:  Target validator must detect `subagent_type:` pattern in output —
           this is the agent dispatch source pattern, not the transition pattern.
  DTV-2:  Target validator must detect `:` separator in skill output directory names
           — the source format uses samsara:X but output must use samsara-X.
"""

from pathlib import Path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_output_structure(tmp_path: Path) -> Path:
    """Create a minimal valid converted output directory."""
    output = tmp_path / "output"
    output.mkdir()

    skills_dir = output / "skills"
    skills_dir.mkdir()
    skill_dir = skills_dir / "samsara-research"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        "---\nname: research\ndescription: Research\n---\n\nResearch body.\n"
    )

    agents_dir = output / "agents"
    agents_dir.mkdir()
    # Agent file with TOML content — name matches "samsara-implementer"
    (agents_dir / "samsara-implementer.toml").write_text(
        '[agent]\nname = "samsara-implementer"\ndeveloper_instructions = "You are the implementer."\n'
    )

    return output


# ---------------------------------------------------------------------------
# DC-7-2: Unconverted `invoke \`samsara:\`` pattern in ANY output file
#
# Silent failure: SkillConverter's internal target validator only runs on
# the single skill being converted. The engine-level target validator must
# scan the ENTIRE output directory, including companion files.
#
# Example: implement/dispatch-template.md still has "invoke `samsara:research`"
# after conversion. The single-skill validator checked SKILL.md but missed
# the companion file. Engine-level validator catches it.
#
# First discoverer: Codex user follows implement skill, hits the broken chain.
# ---------------------------------------------------------------------------


class TestDC72UnconvertedInvokePatternDetected:
    def test_target_validator_detects_invoke_samsara_in_skill_md(self, tmp_path: Path):
        """
        SKILL.md in output containing "invoke `samsara:X`" must be detected.
        This is the primary chain break pattern.
        """
        from samsara_cli.validators.target import TargetValidator

        output = make_output_structure(tmp_path)
        # Inject the unconverted pattern into SKILL.md
        skill_md = output / "skills" / "samsara-research" / "SKILL.md"
        skill_md.write_text(
            "---\nname: research\ndescription: Research\n---\n\n"
            "After research, invoke `samsara:planning` to proceed.\n"
        )

        validator = TargetValidator()
        errors = validator.validate(output_dir=output)

        assert len(errors) > 0, (
            "SILENT FAILURE [DC-7-2]: TargetValidator reported no errors despite "
            "`invoke `samsara:planning`` remaining in SKILL.md output. "
            "Chain break would be undetected until a Codex user hits it."
        )
        error_text = " ".join(errors)
        assert "samsara:" in error_text or "invoke" in error_text.lower(), (
            f"Error message doesn't mention the unconverted pattern. Got: {errors}"
        )

    def test_target_validator_detects_invoke_samsara_in_companion_file(
        self, tmp_path: Path
    ):
        """
        A companion file (dispatch-template.md) containing "invoke `samsara:X`"
        must be detected. The single-skill validator might miss companion files;
        the engine-level validator must catch them.
        """
        from samsara_cli.validators.target import TargetValidator

        output = make_output_structure(tmp_path)
        # Add a companion file with unconverted pattern
        skill_dir = output / "skills" / "samsara-research"
        (skill_dir / "dispatch-template.md").write_text(
            "# Dispatch\n\nUse invoke `samsara:planning` to proceed.\n"
        )

        validator = TargetValidator()
        errors = validator.validate(output_dir=output)

        assert len(errors) > 0, (
            "SILENT FAILURE [DC-7-2]: TargetValidator did not detect "
            "`invoke `samsara:planning`` in companion file dispatch-template.md."
        )

    def test_target_validator_passes_when_no_source_patterns_remain(
        self, tmp_path: Path
    ):
        """
        Sanity: when output has no source patterns, no errors reported.
        """
        from samsara_cli.validators.target import TargetValidator

        output = make_output_structure(tmp_path)

        validator = TargetValidator()
        errors = validator.validate(output_dir=output)

        assert len(errors) == 0, (
            f"TargetValidator reported false positive errors on clean output: {errors}"
        )


# ---------------------------------------------------------------------------
# DC-7-3 (duplicate — also in engine death): Agent name mismatch
#
# Additional test focusing purely on validator behavior in isolation.
# The engine death test (DC-7-3) tests end-to-end. This tests the validator
# contract in isolation — verifies the validator itself can detect the mismatch.
# ---------------------------------------------------------------------------


class TestDC73AgentNameMismatchIsolated:
    def test_skill_references_agent_not_in_output(self, tmp_path: Path):
        """
        A skill's dispatch reference to "samsara-implementer" must match an
        agent file whose TOML name is "samsara-implementer". If the agent file
        has name "implementer" (no prefix), the validator must catch it.
        """
        from samsara_cli.validators.target import TargetValidator

        output = tmp_path / "output"
        output.mkdir()
        skills_dir = output / "skills"
        skills_dir.mkdir()
        skill_dir = skills_dir / "samsara-implement"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: implement\ndescription: Implement\n---\n\n# Implement\n"
        )
        (skill_dir / "dispatch-template.md").write_text(
            'Use agent named "samsara-implementer" to implement the plan.\n'
        )

        agents_dir = output / "agents"
        agents_dir.mkdir()
        # Agent TOML has name = "implementer" (MISSING prefix — the death case)
        (agents_dir / "implementer.toml").write_text(
            '[agent]\nname = "implementer"\ndeveloper_instructions = "Instructions."\n'
        )

        validator = TargetValidator()
        errors = validator.validate(output_dir=output)

        assert len(errors) > 0, (
            "SILENT FAILURE [DC-7-3]: TargetValidator did not detect agent name mismatch. "
            "Skill references 'samsara-implementer' but no agent with that name exists."
        )


# ---------------------------------------------------------------------------
# DTV-1: `subagent_type:` pattern detection
#
# Silent failure: AgentConverter converts `subagent_type: "samsara:X"` in dispatch
# templates. If a rule misses this pattern, the target validator must still catch it.
# The source pattern `subagent_type:` should NOT appear in any output file.
# ---------------------------------------------------------------------------


class TestDTV1SubagentTypePatternDetected:
    def test_target_validator_detects_subagent_type_in_output(self, tmp_path: Path):
        """
        If `subagent_type:` appears in any output file, it means the conversion
        missed transforming this source-format dispatch pattern. Must be detected.
        """
        from samsara_cli.validators.target import TargetValidator

        output = make_output_structure(tmp_path)
        skill_dir = output / "skills" / "samsara-research"
        (skill_dir / "dispatch-template.md").write_text(
            "Agent tool:\n"
            '  subagent_type: "samsara:implementer"\n'
            "  prompt: Implement the plan\n"
        )

        validator = TargetValidator()
        errors = validator.validate(output_dir=output)

        assert len(errors) > 0, (
            "SILENT FAILURE [DTV-1]: TargetValidator did not detect 'subagent_type:' "
            "pattern in output. This source-format pattern means conversion was incomplete."
        )

    def test_target_validator_passes_when_subagent_type_converted(self, tmp_path: Path):
        """
        When `subagent_type:` is correctly converted to the target format,
        no errors should be reported.
        """
        from samsara_cli.validators.target import TargetValidator

        output = make_output_structure(tmp_path)
        skill_dir = output / "skills" / "samsara-research"
        (skill_dir / "dispatch-template.md").write_text(
            "Subagent dispatch:\n"
            '  agent named "samsara-implementer"\n'
            "  prompt: Implement the plan\n"
        )

        validator = TargetValidator()
        errors = validator.validate(output_dir=output)

        assert len(errors) == 0, (
            f"False positive: TargetValidator reported errors for correctly converted dispatch: {errors}"
        )


# ---------------------------------------------------------------------------
# DTV-2: Colon separator in skill output directory names
#
# Silent failure: The source format uses "samsara:research" (colon) but the
# target must use "samsara-research" (hyphen). If the output directory is named
# with a colon, Codex cannot locate the skill.
# ---------------------------------------------------------------------------


class TestDTV2ColonInSkillDirName:
    def test_target_validator_detects_colon_in_skill_dir_name(self, tmp_path: Path):
        """
        If an output skill directory is named with a colon (e.g., 'samsara:research'),
        the target validator must detect this as an error.
        """
        from samsara_cli.validators.target import TargetValidator

        output = tmp_path / "output"
        output.mkdir()
        skills_dir = output / "skills"
        skills_dir.mkdir()
        # Directory with colon — wrong format
        bad_skill_dir = skills_dir / "samsara:research"
        bad_skill_dir.mkdir()
        (bad_skill_dir / "SKILL.md").write_text(
            "---\nname: research\ndescription: Research\n---\n\nBody.\n"
        )

        agents_dir = output / "agents"
        agents_dir.mkdir()

        validator = TargetValidator()
        errors = validator.validate(output_dir=output)

        assert len(errors) > 0, (
            "SILENT FAILURE [DTV-2]: TargetValidator did not detect colon in skill directory name. "
            "Directory 'samsara:research' uses source format, not target format."
        )
        error_text = " ".join(errors)
        assert (
            ":" in error_text
            or "colon" in error_text.lower()
            or "samsara:research" in error_text
        ), f"Error message doesn't mention the colon separator issue. Got: {errors}"
