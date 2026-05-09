"""
Integration tests — Pipeline (end-to-end conversion verification).

Tests the full source → convert → validate → output structure pipeline.
All tests use the committed fixture at tests/fixtures/source/ as the source,
and convert to a temporary output directory.

Death tests (DC) are at the top. They guard silent failure paths:
  DC-9-1: Pipeline MUST fail if any expected output file is missing — partial
           output must not silently pass as "complete conversion."
  DC-9-2: Pipeline source validator MUST reject the test fixture if the fixture
           itself is invalid (missing required dirs/files) — invalid fixtures
           make all other tests meaningless.
  DC-9-3: Engine MUST NOT leave temp dir behind after failure — if it does,
           a subsequent run might pick up stale partial output.

Unit tests follow, verifying the complete expected output structure.

Assumption: tests run from the repository root (pytest discovers tests/ dir).
Assumption: ConversionEngine("codex") can be constructed without a running Codex CLI.
"""

import json
import tempfile
from pathlib import Path

import pytest

from samsara_cli.converter.engine import ConversionEngine, EngineError

# --- Fixture path (committed, stable across runs) ---
FIXTURE_SOURCE = Path(__file__).parent.parent / "fixtures" / "source"
FIXTURE_EXPECTED = Path(__file__).parent.parent / "fixtures" / "expected" / "codex"


# ---------------------------------------------------------------------------
# DC-9-1: Pipeline must fail if output is missing even one expected file
#
# Silent failure: pipeline test asserts output_dir.exists() but doesn't check
# individual files. If a converter silently drops a file (e.g., agent TOML),
# the test would still pass. This guards against that.
#
# First discoverer: Codex user whose plugin has no agents/ directory.
# Damage before discovery: every conversion after regression ships partial output.
# ---------------------------------------------------------------------------


class TestDC91PipelineMustFailOnPartialOutput:
    """Death test: pipeline test itself must fail if expected file count is wrong."""

    def test_expected_file_count_check_catches_missing_file(
        self, tmp_path: Path
    ) -> None:
        """Verify that asserting exact file count will fail if a file is missing.

        This is a meta-test: we build a partial output and verify our assertion
        logic would catch it. If our test logic only checks dir existence, a
        missing agent.toml would pass silently.
        """
        # Build a partial output (missing agents/ entirely)
        partial_output = tmp_path / "partial"
        partial_output.mkdir()
        (partial_output / "skills").mkdir()
        skill_dir = partial_output / "skills" / "samsara-research"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("# research\n")
        # agents/ is intentionally missing — simulates a failed agent converter

        # Our test logic: collect all .md and .toml files recursively
        actual_files = set(
            str(f.relative_to(partial_output))
            for f in partial_output.rglob("*")
            if f.is_file()
        )
        # Expect at least one TOML file in agents/
        has_agent_toml = any(f.endswith(".toml") for f in actual_files)
        assert not has_agent_toml, (
            "This verifies our check would fail on missing agent TOML. "
            "If this assertion itself fails, our check logic is broken."
        )

    def test_pipeline_output_must_contain_agent_toml(self, tmp_path: Path) -> None:
        """DC-9-1: Pipeline test fails if agents/ TOML file is absent from output.

        This test exercises the real engine and asserts the agents/ directory exists
        with at least one TOML file. If agent conversion is silently skipped,
        this test fails — not the assertion about whether output_dir exists.
        """
        output_dir = tmp_path / "output"
        engine = ConversionEngine("codex")
        engine.run(source_dir=FIXTURE_SOURCE, output_dir=output_dir)

        agents_dir = output_dir / ".codex" / "agents"
        assert agents_dir.exists(), "agents/ directory must exist after pipeline run"

        toml_files = list(agents_dir.glob("*.toml"))
        assert len(toml_files) >= 1, (
            f"Expected at least 1 .toml file in agents/, got {len(toml_files)}. "
            "Agent conversion may have been silently skipped."
        )

    def test_pipeline_output_must_contain_skills(self, tmp_path: Path) -> None:
        """DC-9-1: Pipeline test fails if skills/ directory has fewer dirs than source.

        Checks skill count is equal between source and output — no silent drops.
        """
        output_dir = tmp_path / "output"
        engine = ConversionEngine("codex")
        engine.run(source_dir=FIXTURE_SOURCE, output_dir=output_dir)

        source_skill_dirs = [
            d for d in (FIXTURE_SOURCE / "skills").iterdir() if d.is_dir()
        ]
        output_skills_dir = output_dir / ".agents" / "skills"
        assert output_skills_dir.exists(), "skills/ directory must exist in output"

        output_skill_dirs = [d for d in output_skills_dir.iterdir() if d.is_dir()]
        assert len(output_skill_dirs) == len(source_skill_dirs), (
            f"Source has {len(source_skill_dirs)} skill dirs, "
            f"output has {len(output_skill_dirs)}. "
            "Skill conversion silently dropped a skill directory."
        )


# ---------------------------------------------------------------------------
# DC-9-2: Test fixture source must be valid samsara source
#
# Silent failure: if the fixture is itself invalid (missing agents/, no SKILL.md),
# SourceValidator would reject it, engine raises EngineError, and all downstream
# tests fail with a confusing error. Worse: if the fixture is "almost valid" and
# the validator has a gap, tests pass on broken fixtures — meaningless results.
#
# First discoverer: developer who sees all integration tests fail with EngineError
# pointing to source structure, not conversion logic.
# Damage: all integration tests produce false negatives until fixture is fixed.
# ---------------------------------------------------------------------------


class TestDC92FixtureMustBeValidSource:
    """Death test: fixture source must pass the SourceValidator."""

    def test_fixture_plugin_json_exists(self) -> None:
        """Fixture must have .claude-plugin/plugin.json."""
        plugin_json = FIXTURE_SOURCE / ".claude-plugin" / "plugin.json"
        assert plugin_json.exists(), (
            f"Test fixture is missing plugin.json at {plugin_json}. "
            "Invalid fixtures make all integration tests meaningless."
        )

    def test_fixture_plugin_json_has_required_fields(self) -> None:
        """Fixture plugin.json must have name and version fields."""
        plugin_json = FIXTURE_SOURCE / ".claude-plugin" / "plugin.json"
        data = json.loads(plugin_json.read_text())
        assert "name" in data, "plugin.json missing 'name' field"
        assert "version" in data, "plugin.json missing 'version' field"
        assert data["name"], "plugin.json 'name' field is empty"
        assert data["version"], "plugin.json 'version' field is empty"

    def test_fixture_skills_dir_exists(self) -> None:
        """Fixture must have skills/ directory."""
        assert (FIXTURE_SOURCE / "skills").is_dir(), (
            "Fixture skills/ directory is missing."
        )

    def test_fixture_each_skill_has_skill_md(self) -> None:
        """Every skill directory in fixture must have a SKILL.md file."""
        skills_dir = FIXTURE_SOURCE / "skills"
        for skill_dir in skills_dir.iterdir():
            if skill_dir.is_dir():
                skill_md = skill_dir / "SKILL.md"
                assert skill_md.exists(), (
                    f"Skill directory '{skill_dir.name}' is missing SKILL.md. "
                    "All skill dirs must have SKILL.md — this is a fixture bug."
                )

    def test_fixture_agents_dir_has_at_least_one_md(self) -> None:
        """Fixture must have at least one .md file in agents/."""
        agents_dir = FIXTURE_SOURCE / "agents"
        assert agents_dir.is_dir(), "Fixture agents/ directory is missing"
        agent_mds = list(agents_dir.glob("*.md"))
        assert len(agent_mds) >= 1, (
            "Fixture agents/ has no .md files. "
            "SourceValidator would reject this fixture."
        )

    def test_fixture_hooks_json_exists(self) -> None:
        """Fixture must have hooks/hooks.json."""
        hooks_json = FIXTURE_SOURCE / "hooks" / "hooks.json"
        assert hooks_json.exists(), "Fixture hooks/hooks.json is missing"

    def test_fixture_passes_source_validator(self) -> None:
        """Fixture passes SourceValidator without errors.

        If this test fails, all other integration tests are running on an
        invalid fixture — their results are meaningless.
        """
        from samsara_cli.validators.source import SourceValidator

        skills_dir = FIXTURE_SOURCE / "skills"
        expected_skills = [d.name for d in skills_dir.iterdir() if d.is_dir()]

        validator = SourceValidator()
        errors = validator.validate(
            source_dir=FIXTURE_SOURCE, expected_skills=expected_skills
        )
        assert errors == [], (
            f"Test fixture failed SourceValidator with {len(errors)} error(s):\n"
            + "\n".join(f"  - {e}" for e in errors)
            + "\nFix the fixture before other integration tests mean anything."
        )


# ---------------------------------------------------------------------------
# DC-9-3: Engine must not leave temp dir behind on failure
#
# Silent failure: if the engine fails mid-conversion and leaks the temp dir,
# a CI pipeline checking for any output dir might pick up the partial dir.
# This is a re-verification of DC-7-1 at the integration test level, using
# real fixture source rather than mocks.
#
# First discoverer: CI pipeline that checks for existence of any temp dir
# starting with "samsara-convert-" after a failed run.
# Damage: stale partial output misleads the next tool in the chain.
# ---------------------------------------------------------------------------


class TestDC93NoTempDirLeakOnFailure:
    """Death test: engine must clean up temp dir after any failure."""

    def test_no_temp_dir_remains_after_engine_failure(self, tmp_path: Path) -> None:
        """Engine must delete its temp dir when it raises EngineError.

        We inject an invalid source (missing plugin.json) to force EngineError,
        then verify no temp dir was left behind in the system temp directory.
        """
        import glob

        invalid_source = tmp_path / "invalid-source"
        invalid_source.mkdir()
        # Create a minimal invalid source — missing plugin.json so SourceValidator fails
        (invalid_source / ".claude-plugin").mkdir()
        # Note: intentionally omit plugin.json to trigger source validation failure
        (invalid_source / "skills").mkdir()
        skill_dir = invalid_source / "skills" / "research"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("---\nname: research\n---\n# Research\n")
        (invalid_source / "agents").mkdir()
        (invalid_source / "agents" / "implementer.md").write_text("# Implementer\n")
        (invalid_source / "hooks").mkdir()
        (invalid_source / "hooks" / "hooks.json").write_text("{}")

        output_dir = tmp_path / "output"
        engine = ConversionEngine("codex")

        # Capture temp dirs before the run
        pre_run_temp_dirs = set(glob.glob(tempfile.gettempdir() + "/samsara-convert-*"))

        with pytest.raises(EngineError):
            engine.run(source_dir=invalid_source, output_dir=output_dir)

        # Verify no new temp dirs were left behind
        post_run_temp_dirs = set(
            glob.glob(tempfile.gettempdir() + "/samsara-convert-*")
        )
        leaked_dirs = post_run_temp_dirs - pre_run_temp_dirs
        assert leaked_dirs == set(), (
            f"Engine left temp dir(s) behind after failure: {leaked_dirs}. "
            "Leaked temp dirs may contain partial output that misleads downstream tools."
        )

    def test_output_dir_not_created_on_engine_failure(self, tmp_path: Path) -> None:
        """Output dir must NOT exist after engine failure.

        If source validation fails, the output_dir must not be created at all.
        """
        invalid_source = tmp_path / "empty-source"
        invalid_source.mkdir()
        output_dir = tmp_path / "output"

        engine = ConversionEngine("codex")
        with pytest.raises(EngineError):
            engine.run(source_dir=invalid_source, output_dir=output_dir)

        assert not output_dir.exists(), (
            "output_dir was created even though engine raised EngineError. "
            "All-or-nothing contract violated."
        )


# ---------------------------------------------------------------------------
# Unit tests — full pipeline structure verification
# ---------------------------------------------------------------------------


class TestPipelineOutputStructure:
    """Verify the complete expected output structure after a successful pipeline run."""

    @pytest.fixture(scope="class")
    def pipeline_output(self, tmp_path_factory) -> Path:
        """Run the full pipeline once and return the output directory.

        Scoped to class to avoid re-running the engine for every test method.
        """
        output_dir = tmp_path_factory.mktemp("pipeline") / "codex_output"
        engine = ConversionEngine("codex")
        engine.run(source_dir=FIXTURE_SOURCE, output_dir=output_dir)
        return output_dir

    def test_skills_directory_exists(self, pipeline_output: Path) -> None:
        assert (pipeline_output / ".agents" / "skills").is_dir(), (
            "skills/ directory missing from output"
        )

    def test_agents_directory_exists(self, pipeline_output: Path) -> None:
        assert (pipeline_output / ".codex" / "agents").is_dir(), (
            "agents/ directory missing from output"
        )

    def test_codex_native_directory_exists(self, pipeline_output: Path) -> None:
        assert (pipeline_output / ".codex").is_dir(), ".codex/ directory missing"

    def test_codex_native_has_config_toml(self, pipeline_output: Path) -> None:
        config_toml = pipeline_output / ".codex" / "config.toml"
        assert config_toml.exists(), ".codex/config.toml missing"

    def test_codex_native_has_hooks_json(self, pipeline_output: Path) -> None:
        hooks_json = pipeline_output / ".codex" / "hooks.json"
        assert hooks_json.exists(), ".codex/hooks.json missing"

    def test_codex_plugin_has_hooks_dir(self, pipeline_output: Path) -> None:
        hooks_dir = pipeline_output / ".codex" / "hooks"
        assert hooks_dir.is_dir(), ".codex/hooks/ directory missing"

    def test_codex_plugin_has_session_start_script(self, pipeline_output: Path) -> None:
        script = pipeline_output / ".codex" / "hooks" / "samsara-session-start.sh"
        assert script.exists(), ".codex/hooks/samsara-session-start.sh missing"

    def test_codex_plugin_has_references_dir(self, pipeline_output: Path) -> None:
        refs_dir = pipeline_output / ".agents" / "references"
        assert refs_dir.is_dir(), ".agents/references/ directory missing"

    def test_skill_names_use_samsara_prefix(self, pipeline_output: Path) -> None:
        """All output skill dirs must start with 'samsara-' prefix."""
        skills_dir = pipeline_output / ".agents" / "skills"
        for skill_dir in skills_dir.iterdir():
            if skill_dir.is_dir():
                assert skill_dir.name.startswith("samsara-"), (
                    f"Skill dir '{skill_dir.name}' does not use 'samsara-' prefix. "
                    "Naming config (prefix=samsara, separator=-) must be applied."
                )

    def test_skill_dirs_have_no_colon_in_name(self, pipeline_output: Path) -> None:
        """No output skill dir name may contain a colon."""
        skills_dir = pipeline_output / ".agents" / "skills"
        for skill_dir in skills_dir.iterdir():
            if skill_dir.is_dir():
                assert ":" not in skill_dir.name, (
                    f"Skill dir '{skill_dir.name}' contains colon — source format, not target."
                )

    def test_each_output_skill_has_skill_md(self, pipeline_output: Path) -> None:
        """Every output skill directory must have SKILL.md."""
        skills_dir = pipeline_output / ".agents" / "skills"
        for skill_dir in skills_dir.iterdir():
            if skill_dir.is_dir():
                assert (skill_dir / "SKILL.md").exists(), (
                    f"Output skill dir '{skill_dir.name}' missing SKILL.md"
                )

    def test_agent_output_is_toml_format(self, pipeline_output: Path) -> None:
        """Agent output files must be .toml, not .md."""
        agents_dir = pipeline_output / ".codex" / "agents"
        toml_files = list(agents_dir.glob("*.toml"))
        md_files = list(agents_dir.glob("*.md"))
        assert len(toml_files) >= 1, "No .toml agent files found"
        assert len(md_files) == 0, (
            f"Found .md files in agents/ (unconverted): {md_files}"
        )

    def test_implement_companion_file_preserved(self, pipeline_output: Path) -> None:
        """dispatch-template.md companion file must be preserved in output skill dir."""
        # samsara-implement should have dispatch-template.md (companion file)
        implement_dir = pipeline_output / ".agents" / "skills" / "samsara-implement"
        assert implement_dir.exists(), "samsara-implement skill dir missing"
        companion = implement_dir / "dispatch-template.md"
        assert companion.exists(), (
            "dispatch-template.md companion file missing from samsara-implement. "
            "Companion files must be preserved in output."
        )

    def test_skill_count_matches_source(self, pipeline_output: Path) -> None:
        """Output skill count must match source skill count exactly."""
        source_skills = [d for d in (FIXTURE_SOURCE / "skills").iterdir() if d.is_dir()]
        output_skills = [
            d for d in (pipeline_output / ".agents" / "skills").iterdir() if d.is_dir()
        ]
        assert len(output_skills) == len(source_skills), (
            f"Source has {len(source_skills)} skills, "
            f"output has {len(output_skills)}. "
            "Pipeline silently dropped or added skill directories."
        )

    def test_skill_names_are_derived_from_frontmatter_names(
        self, pipeline_output: Path
    ) -> None:
        """Each output skill name must correspond to a source SKILL.md frontmatter name.

        Guards against: count matching but wrong names (e.g., one skill renamed,
        another duplicated). Output dir name is samsara-<frontmatter_name>.

        Note: output_dir_name = samsara-<frontmatter_name>, NOT samsara-<source_dir_name>.
        For 'samsara-bootstrap' (frontmatter name), output is 'samsara-samsara-bootstrap'.
        This is the SkillConverter's naming convention (_derive_output_dir_name).

        Silent failure: if this test only checked count (not names), a converter that
        drops 'implement' and creates 'implement-dup' would produce a matching count
        but wrong output — Codex user loses the implement skill.
        """
        # Extract frontmatter names from each source SKILL.md
        source_frontmatter_names: set[str] = set()
        for skill_dir in (FIXTURE_SOURCE / "skills").iterdir():
            if not skill_dir.is_dir():
                continue
            skill_md = skill_dir / "SKILL.md"
            if not skill_md.exists():
                continue
            content = skill_md.read_text(encoding="utf-8")
            lines = content.splitlines()
            if lines and lines[0].strip() == "---":
                for line in lines[1:]:
                    if line.strip() == "---":
                        break
                    if line.startswith("name:"):
                        name = line.split(":", 1)[1].strip().strip("\"'")
                        if name:
                            source_frontmatter_names.add(name)
                        break

        output_skill_names = {
            d.name
            for d in (pipeline_output / ".agents" / "skills").iterdir()
            if d.is_dir()
        }

        # Each source frontmatter name 'X' should produce output dir 'samsara-X'
        expected_output_names = {f"samsara-{name}" for name in source_frontmatter_names}
        missing = expected_output_names - output_skill_names
        extra = output_skill_names - expected_output_names

        assert not missing, (
            f"Expected output skill dirs are missing: {sorted(missing)}. "
            "These source skills were silently dropped or renamed. "
            f"Source frontmatter names: {sorted(source_frontmatter_names)}"
        )
        assert not extra, (
            f"Unexpected output skill dirs found: {sorted(extra)}. "
            "These were not derived from any source skill frontmatter name."
        )


class TestGeminiPipelineOutputStructure:
    """Verify Gemini output structure after a successful pipeline run."""

    @pytest.fixture(scope="class")
    def pipeline_output(self, tmp_path_factory) -> Path:
        output_dir = tmp_path_factory.mktemp("pipeline-gemini") / "gemini_output"
        engine = ConversionEngine("gemini-cli")
        engine.run(source_dir=FIXTURE_SOURCE, output_dir=output_dir)
        return output_dir

    def test_gemini_skills_directory_exists(self, pipeline_output: Path) -> None:
        assert (pipeline_output / ".gemini" / "skills").is_dir()
        assert not (pipeline_output / ".agents" / "skills").exists()

    def test_gemini_agents_are_markdown(self, pipeline_output: Path) -> None:
        agents_dir = pipeline_output / ".gemini" / "agents"
        assert agents_dir.is_dir()
        assert list(agents_dir.glob("*.md"))
        assert not list(agents_dir.glob("*.toml"))

    def test_gemini_settings_json_exists_and_parses(
        self, pipeline_output: Path
    ) -> None:
        settings_path = pipeline_output / ".gemini" / "settings.json"
        assert settings_path.exists()
        data = json.loads(settings_path.read_text(encoding="utf-8"))
        assert data["hooks"]["SessionStart"]

    def test_gemini_skill_count_matches_source(self, pipeline_output: Path) -> None:
        source_skills = [d for d in (FIXTURE_SOURCE / "skills").iterdir() if d.is_dir()]
        output_skills = [
            d for d in (pipeline_output / ".gemini" / "skills").iterdir() if d.is_dir()
        ]
        assert len(output_skills) == len(source_skills)
