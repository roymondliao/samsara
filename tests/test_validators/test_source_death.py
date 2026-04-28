"""
Death tests for SourceValidator — targeting silent failure paths.

Each test names the specific silent failure path it guards against.
Death tests run before unit tests. They must fail red before implementation.

Silent failures guarded:
  DC-7-4: Source validator must fail loudly if a required skill directory is missing —
           not silently skip it and produce output with missing skills.
  DC-SV-1: Source validator must fail if plugin.json is missing required fields —
            not silently continue with a broken manifest.
  DC-SV-2: Source validator must fail if SKILL.md is missing from a skill directory —
            a skill without SKILL.md produces no output, silently dropping a skill.
"""

import json
from pathlib import Path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_valid_source(tmp_path: Path, skill_names: list[str] | None = None) -> Path:
    """Create a valid samsara source directory with the given skills."""
    source = tmp_path / "source"
    plugin_dir = source / ".claude-plugin"
    plugin_dir.mkdir(parents=True)
    (plugin_dir / "plugin.json").write_text(
        json.dumps({"name": "samsara", "version": "0.8.0"})
    )

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
    (agents_dir / "implementer.md").write_text(
        "# Implementer\n\nYou are the implementer agent.\n"
    )

    hooks_dir = source / "hooks"
    hooks_dir.mkdir()
    (hooks_dir / "hooks.json").write_text(json.dumps({"hooks": []}))

    references_dir = source / "references"
    references_dir.mkdir()

    return source


# ---------------------------------------------------------------------------
# DC-7-4: Required skill directory missing must fail loudly
#
# Silent failure: source has 10 skills but "implement" is accidentally missing.
# SourceValidator silently skips it. Engine produces output with 10 skills.
# User doesn't notice "implement" skill is gone — nothing in the output says
# the skill count is wrong. First discoverer: user tries to use implement skill,
# finds it doesn't exist, thinks it was never installed.
# Damage: implement skill (the most critical operational skill) silently absent.
# ---------------------------------------------------------------------------


class TestDC74RequiredSkillDirectoryMissing:
    def test_source_validator_fails_when_required_skill_dir_missing(
        self, tmp_path: Path
    ):
        """
        If a skill expected to be in the source is missing (e.g., 'implement'),
        SourceValidator must report it as an error — not silently skip it.
        """
        from samsara_cli.validators.source import SourceValidator

        source = make_valid_source(tmp_path, skill_names=["research", "planning"])
        # 'implement' is missing — but it's listed as expected
        expected_skills = ["research", "planning", "implement"]

        validator = SourceValidator()
        errors = validator.validate(source_dir=source, expected_skills=expected_skills)

        assert len(errors) > 0, (
            "SILENT FAILURE [DC-7-4]: SourceValidator reported no errors even though "
            "'implement' skill directory is missing. Validator must fail loudly, not skip."
        )
        error_text = " ".join(errors)
        assert "implement" in error_text, (
            f"Error message does not mention the missing skill 'implement'. Got: {errors}"
        )

    def test_source_validator_fails_for_each_missing_skill(self, tmp_path: Path):
        """
        If multiple skills are missing, each must be reported — not just the first.
        """
        from samsara_cli.validators.source import SourceValidator

        source = make_valid_source(tmp_path, skill_names=["research"])
        expected_skills = ["research", "planning", "implement", "debugging"]

        validator = SourceValidator()
        errors = validator.validate(source_dir=source, expected_skills=expected_skills)

        # All three missing skills must be mentioned
        error_text = " ".join(errors)
        assert "planning" in error_text, "Missing 'planning' not reported"
        assert "implement" in error_text, "Missing 'implement' not reported"
        assert "debugging" in error_text, "Missing 'debugging' not reported"

    def test_source_validator_passes_when_all_expected_skills_present(
        self, tmp_path: Path
    ):
        """
        Sanity: when all expected skills are present, no errors reported.
        """
        from samsara_cli.validators.source import SourceValidator

        source = make_valid_source(
            tmp_path, skill_names=["research", "planning", "implement"]
        )
        expected_skills = ["research", "planning", "implement"]

        validator = SourceValidator()
        errors = validator.validate(source_dir=source, expected_skills=expected_skills)

        assert len(errors) == 0, (
            f"SourceValidator reported errors for a valid source structure: {errors}"
        )


# ---------------------------------------------------------------------------
# DC-SV-1: plugin.json missing required fields must fail loudly
#
# Silent failure: plugin.json exists but has no 'name' field. SourceValidator
# says OK. Engine proceeds. ManifestConverter later raises ValueError.
# But the failure is deep in the pipeline, after temp dir is created, after
# skills are converted. All-or-nothing still holds, but the error message is
# confusing — it looks like a converter bug, not a source problem.
# Detecting at source validation time gives cleaner error attribution.
# ---------------------------------------------------------------------------


class TestDCSV1PluginJsonRequiredFields:
    def test_source_validator_fails_if_plugin_json_missing(self, tmp_path: Path):
        """
        If .claude-plugin/plugin.json does not exist, SourceValidator must fail.
        """
        from samsara_cli.validators.source import SourceValidator

        source = make_valid_source(tmp_path)
        # Remove plugin.json
        (source / ".claude-plugin" / "plugin.json").unlink()

        validator = SourceValidator()
        errors = validator.validate(source_dir=source, expected_skills=["research"])

        assert len(errors) > 0, (
            "SILENT FAILURE [DC-SV-1]: SourceValidator passed even though plugin.json is missing."
        )

    def test_source_validator_fails_if_plugin_json_missing_name(self, tmp_path: Path):
        """
        If plugin.json exists but has no 'name' field, SourceValidator must fail.
        """
        from samsara_cli.validators.source import SourceValidator

        source = make_valid_source(tmp_path)
        (source / ".claude-plugin" / "plugin.json").write_text(
            json.dumps({"version": "0.8.0"})  # missing 'name'
        )

        validator = SourceValidator()
        errors = validator.validate(source_dir=source, expected_skills=["research"])

        assert len(errors) > 0, (
            "SILENT FAILURE [DC-SV-1]: SourceValidator passed with plugin.json missing 'name' field."
        )
        error_text = " ".join(errors)
        assert "name" in error_text.lower(), (
            f"Error message doesn't mention missing 'name' field. Got: {errors}"
        )

    def test_source_validator_fails_if_plugin_json_missing_version(
        self, tmp_path: Path
    ):
        """
        If plugin.json exists but has no 'version' field, SourceValidator must fail.
        """
        from samsara_cli.validators.source import SourceValidator

        source = make_valid_source(tmp_path)
        (source / ".claude-plugin" / "plugin.json").write_text(
            json.dumps({"name": "samsara"})  # missing 'version'
        )

        validator = SourceValidator()
        errors = validator.validate(source_dir=source, expected_skills=["research"])

        assert len(errors) > 0, (
            "SILENT FAILURE [DC-SV-1]: SourceValidator passed with plugin.json missing 'version' field."
        )


# ---------------------------------------------------------------------------
# DC-SV-2: SKILL.md missing from skill directory must fail loudly
#
# Silent failure: a skill directory exists but has no SKILL.md (e.g., leftover
# directory from a deleted skill). SourceValidator says OK. SkillConverter
# raises ConversionError when it can't find SKILL.md. Again, the error is deep
# in the pipeline. Better to detect at source validation time.
# ---------------------------------------------------------------------------


class TestDCSV2SkillMdMissingFails:
    def test_source_validator_fails_if_skill_md_missing(self, tmp_path: Path):
        """
        If a skill directory exists but has no SKILL.md, SourceValidator must
        report it as an error. An empty skill directory produces no skill output
        — SkillConverter would raise ConversionError, but catching it at source
        validation time is cleaner.
        """
        from samsara_cli.validators.source import SourceValidator

        source = make_valid_source(tmp_path, skill_names=["research"])
        # Remove the SKILL.md from research skill
        (source / "skills" / "research" / "SKILL.md").unlink()

        validator = SourceValidator()
        errors = validator.validate(source_dir=source, expected_skills=["research"])

        assert len(errors) > 0, (
            "SILENT FAILURE [DC-SV-2]: SourceValidator passed even though SKILL.md is missing "
            "from 'research' skill directory."
        )
        error_text = " ".join(errors)
        assert "SKILL.md" in error_text or "research" in error_text, (
            f"Error message doesn't mention the problematic skill. Got: {errors}"
        )
