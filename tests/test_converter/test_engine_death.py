"""
Death tests for ConversionEngine — targeting silent failure paths.

Each test names the specific silent failure path it guards against.
Death tests run before unit tests. They must fail red before implementation.

Silent failures guarded:
  DC-7-1: Engine MUST NOT produce partial output if any converter fails mid-run.
           If agent converter fails after skills are done, the output dir must be
           empty (or not exist). A partial output dir looks like success.
  DC-7-3: Agent name mismatch — skill references "samsara-implementer" but agent
           file is named "implementer.toml" (no prefix). Cross-validation must
           catch this in the target validator before the output is committed.
  DC-7-5: Engine with extra unknown files in source must NOT delete them from output.
           Unknown files must be preserved with a warning — not silently dropped.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from samsara_cli.converter.skill import ConversionError


# ---------------------------------------------------------------------------
# Helpers — build minimal fake source structure for engine tests
# ---------------------------------------------------------------------------


def make_source_structure(tmp_path: Path) -> Path:
    """Create a minimal valid samsara source directory structure."""
    source = tmp_path / "source"
    plugin_dir = source / ".claude-plugin"
    plugin_dir.mkdir(parents=True)
    (plugin_dir / "plugin.json").write_text(
        json.dumps({"name": "samsara", "version": "0.8.0"})
    )

    skills_dir = source / "skills"
    skills_dir.mkdir()
    skill_dir = skills_dir / "research"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        "---\nname: research\ndescription: Research skill\n---\n\n# Research\n"
    )

    agents_dir = source / "agents"
    agents_dir.mkdir()
    (agents_dir / "implementer.md").write_text(
        "# Implementer\n\nYou are the implementer agent.\n"
    )

    hooks_dir = source / "hooks"
    hooks_dir.mkdir()
    (hooks_dir / "hooks.json").write_text(json.dumps({"hooks": []}))
    (hooks_dir / "session-start").write_text("#!/bin/bash\necho hello\n")

    references_dir = source / "references"
    references_dir.mkdir()
    (references_dir / "code-review.md").write_text("# Code Review\n\nReference doc.\n")

    return source


# ---------------------------------------------------------------------------
# DC-7-1: Engine must NOT produce partial output on failure
#
# Silent failure: Agent converter raises after skills have already been written
# to the temp dir. The temp dir contains partial output. If the engine does NOT
# clean up the temp dir before reporting failure, a caller might read from it
# (e.g., check "does the output dir exist?") and falsely assume success.
#
# First discoverer: CI pipeline that checks for output dir existence, not exit code.
# Damage before discovery: broken skill→agent chain in every Codex user environment.
# ---------------------------------------------------------------------------


class TestDC71NoPartialOutputOnFailure:
    def test_output_dir_does_not_exist_after_engine_failure(self, tmp_path: Path):
        """
        If the engine fails during conversion (e.g., agent converter crashes),
        the final output directory MUST NOT exist after the failure.
        A partial output directory is worse than no output directory — it looks
        like a successful conversion.
        """
        from samsara_cli.converter.engine import ConversionEngine, EngineError

        source = make_source_structure(tmp_path)
        output = tmp_path / "output"

        # We need the engine to partially succeed (skills) then fail (agents).
        # Patch AgentConverter.convert_from_text to raise on first call.
        with patch("samsara_cli.converter.engine.AgentConverter") as MockAgentConverter:
            mock_instance = MagicMock()
            mock_instance.convert_from_text.side_effect = ValueError(
                "Agent converter intentionally failed in death test"
            )
            MockAgentConverter.return_value = mock_instance

            with pytest.raises((EngineError, ValueError, Exception)):
                engine = ConversionEngine(platform="codex")
                engine.run(source_dir=source, output_dir=output)

        # CRITICAL: output dir must not exist (or must be empty) after failure.
        # Either is acceptable — what is NOT acceptable is a partial output dir.
        if output.exists():
            remaining_files = list(output.rglob("*"))
            assert len(remaining_files) == 0, (
                f"SILENT FAILURE [DC-7-1]: Output dir exists with {len(remaining_files)} files "
                f"after engine failure. Partial output: {[str(f) for f in remaining_files[:5]]}. "
                "All-or-nothing violated — partial output is worse than no output."
            )

    def test_temp_dir_cleaned_up_after_failure(self, tmp_path: Path):
        """
        The engine uses a temp dir for intermediate work. After failure, the temp dir
        must be deleted. Leaving temp dirs around is a silent resource leak that
        accumulates across failed runs.
        """
        from samsara_cli.converter.engine import ConversionEngine

        source = make_source_structure(tmp_path)
        output = tmp_path / "output"

        temp_dirs_before = set(tmp_path.iterdir())

        with patch("samsara_cli.converter.engine.AgentConverter") as MockAgentConverter:
            mock_instance = MagicMock()
            mock_instance.convert_from_text.side_effect = ConversionError(
                "forced failure"
            )
            MockAgentConverter.return_value = mock_instance

            with pytest.raises(Exception):
                engine = ConversionEngine(platform="codex")
                engine.run(source_dir=source, output_dir=output)

        # No new directories (other than the output dir which may or may not exist)
        # should have been left behind.
        temp_dirs_after = set(
            d for d in tmp_path.iterdir() if d.is_dir() and d != output
        )
        new_dirs = temp_dirs_after - temp_dirs_before
        assert len(new_dirs) == 0, (
            f"SILENT FAILURE [DC-7-1]: Temp dirs left behind after failure: {new_dirs}. "
            "Engine must clean up temp dirs on failure."
        )


# ---------------------------------------------------------------------------
# DC-7-3: Agent name mismatch — skill references agent that doesn't match
#         the converted agent filename (missing prefix).
#
# Silent failure: SkillConverter produces skill with dispatch reference
# "samsara-implementer" but AgentConverter produces "implementer.toml"
# (no prefix). The target validator MUST catch this before committing output.
#
# First discoverer: Codex user runs the implement skill, dispatches to
# "samsara-implementer", agent not found, task fails silently.
# Damage: every skill that dispatches to agents is broken.
# ---------------------------------------------------------------------------


class TestDC73AgentNameMismatchDetected:
    def test_target_validator_catches_skill_referencing_nonexistent_agent(
        self, tmp_path: Path
    ):
        """
        Target validator must detect when a skill's dispatch-template.md references
        an agent name that does NOT exist in the converted agent files.

        This is the name mismatch death case: skill references "samsara-implementer"
        but agent file is "implementer.toml" (name inside is "implementer", no prefix).
        """
        from samsara_cli.validators.target import TargetValidator

        output = tmp_path / "output"
        output.mkdir()

        # Skill references "samsara-implementer" in its dispatch template
        skills_dir = output / "skills"
        skills_dir.mkdir()
        skill_dir = skills_dir / "samsara-implement"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: implement\ndescription: Implement\n---\n\n# Implement\n"
        )
        # dispatch-template.md references the agent by name
        (skill_dir / "dispatch-template.md").write_text(
            'Use agent named "samsara-implementer" to implement.\n'
        )

        # Agent files directory — agent file is named "implementer.toml" (MISSING prefix)
        agents_dir = output / "agents"
        agents_dir.mkdir()
        (agents_dir / "implementer.toml").write_text(
            'name = "implementer"\n'
            'description = "Implementer"\n'
            'developer_instructions = "You are an agent."\n'
        )

        validator = TargetValidator()
        errors = validator.validate(output_dir=output)

        # Must have detected the name mismatch
        assert len(errors) > 0, (
            "SILENT FAILURE [DC-7-3]: Target validator reported no errors but "
            "'samsara-implementer' referenced in skill does not match any agent file. "
            "Agent name mismatch would cause every skill dispatch to fail at runtime."
        )
        error_text = " ".join(errors)
        assert (
            "samsara-implementer" in error_text
            or "mismatch" in error_text.lower()
            or "not found" in error_text.lower()
        ), (
            f"Error message does not mention the missing agent or mismatch. Got: {errors}"
        )


# ---------------------------------------------------------------------------
# DC-7-5: Engine must preserve unknown/extra files in source — not delete them
#
# Silent failure: source directory contains extra files not in the conversion
# plan (e.g., custom scripts, README files, platform-specific additions).
# Engine silently ignores/drops them. User's extra files are not in output.
# First discoverer: user checks output, notices custom file is missing.
# Damage: user's custom content silently lost on every conversion run.
# ---------------------------------------------------------------------------


class TestDC75UnknownFilesPreserved:
    def test_extra_files_in_skill_dir_are_copied_to_output(self, tmp_path: Path):
        """
        If a skill directory contains files not recognized by the converter
        (e.g., a custom README or extra script), those files must be preserved
        in the output — not silently dropped.
        """
        from samsara_cli.converter.engine import ConversionEngine

        source = make_source_structure(tmp_path)
        output = tmp_path / "output"

        # Add an extra file in the skill dir that the engine doesn't know about
        extra_file = source / "skills" / "research" / "custom-extra-file.txt"
        extra_file.write_text("This is extra content not in conversion plan.\n")

        engine = ConversionEngine(platform="codex")
        engine.run(source_dir=source, output_dir=output)

        # The extra file must appear in the output
        # (it's a companion file in the skill dir — SkillConverter handles it)
        output_files = list(output.rglob("custom-extra-file.txt"))
        assert len(output_files) > 0, (
            "SILENT FAILURE [DC-7-5]: Extra file 'custom-extra-file.txt' was not "
            "found in output after conversion. Unknown files must be preserved."
        )


# ---------------------------------------------------------------------------
# DC-7-6: Duplicate agent names must fail, not silently overwrite
#
# Silent failure: Two agent .md files produce the same output name (e.g.,
# both named 'reviewer.md' in different contexts). The second file silently
# overwrites the first. The output has one agent instead of two — no error.
# First discoverer: user who notices a missing agent in Codex.
# ---------------------------------------------------------------------------


class TestDC76DuplicateAgentNameFails:
    def test_duplicate_agent_names_raise_engine_error(self, tmp_path: Path):
        """Two agent files producing the same output name must raise EngineError."""
        from samsara_cli.converter.engine import ConversionEngine, EngineError

        source = make_source_structure(tmp_path)
        output = tmp_path / "output"

        agents_dir = source / "agents"
        duplicate = agents_dir / "implementer-copy.md"
        duplicate.write_text("# Implementer Copy\n\nDuplicate agent.\n")

        with patch("samsara_cli.converter.engine.AgentConverter") as MockAgentConverter:
            mock_converter = MagicMock()
            MockAgentConverter.return_value = mock_converter

            mock_result = MagicMock()
            mock_result.agent_name = "samsara-implementer"
            mock_result.toml_content = (
                'name = "samsara-implementer"\n'
                'description = "Implementer"\n'
                'developer_instructions = "Body"\n'
            )
            mock_converter.convert_from_text.return_value = mock_result

            with pytest.raises(EngineError, match="[Dd]uplicate") as exc_info:
                engine = ConversionEngine(platform="codex")
                engine.run(source_dir=source, output_dir=output)

            error_msg = str(exc_info.value)
            assert "Collides with" in error_msg, (
                "Error must name the prior file that produced the collision"
            )

    def test_case_insensitive_collision_detected(self, tmp_path: Path):
        """Names differing only in case must collide (macOS filesystem safety).

        'samsara-Implementer' vs 'samsara-implementer' would overwrite on
        case-insensitive filesystems. The engine must catch this via casefold().
        """
        from samsara_cli.converter.engine import ConversionEngine, EngineError

        source = make_source_structure(tmp_path)
        output = tmp_path / "output"

        agents_dir = source / "agents"
        agents_dir.mkdir(exist_ok=True)
        (agents_dir / "other-agent.md").write_text("# Other\n\nAnother agent.\n")

        with patch("samsara_cli.converter.engine.AgentConverter") as MockAgentConverter:
            mock_converter = MagicMock()
            MockAgentConverter.return_value = mock_converter

            result_lower = MagicMock()
            result_lower.agent_name = "samsara-implementer"
            result_lower.toml_content = (
                'name = "samsara-implementer"\n'
                'description = "Implementer"\n'
                'developer_instructions = "Body"\n'
            )

            result_upper = MagicMock()
            result_upper.agent_name = "samsara-Implementer"
            result_upper.toml_content = (
                'name = "samsara-Implementer"\n'
                'description = "Implementer"\n'
                'developer_instructions = "Body"\n'
            )

            # sorted() glob: implementer.md < other-agent.md — result_lower maps to first
            mock_converter.convert_from_text.side_effect = [
                result_lower,
                result_upper,
            ]

            with pytest.raises(EngineError, match="[Dd]uplicate") as exc_info:
                engine = ConversionEngine(platform="codex")
                engine.run(source_dir=source, output_dir=output)

            error_msg = str(exc_info.value)
            assert "Collides with" in error_msg, (
                "Case-insensitive collision error must name the prior file"
            )
