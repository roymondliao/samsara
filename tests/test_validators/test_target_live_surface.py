"""
Death tests for TargetValidator's live-surface source-tree scan exclusion
(ISSUE-002 / SS-1 / SD-1).

`samsara-cli validate` defaults `--source` to the repo root (Path.cwd()), so
`TargetValidator._scan_source_patterns`'s `output_dir.rglob("*")` walks the
ENTIRE repo tree — including historical/demonstrative documentation
(changes/, docs/, bugfix/, tests/) that legitimately contains sample text
matching the source patterns ("invoke `samsara:X`", "subagent_type:"). That
noise made `validate` permanently non-zero (main 42, branch 36 issues) and
therefore unusable as a gate signal.

Each test below names the specific silent failure path it guards against.
Death tests run before unit tests. They must fail red before implementation.

Silent failures guarded:
  DTV-3-1 (noise suppression): planted leak-pattern text under changes/ must
           NOT be counted — this is exactly the noise ISSUE-002 exists to cut.
  DTV-3-2 (death case 1 / SS-1 boundary): planted leak-pattern text under
           skills/ (live instruction surface) must STILL be caught. If the
           exclusion list ever grows to accidentally shadow a live-surface
           path, this is the test that goes red.
  DTV-3-3 (death case 2 / SD-1 single constant): TargetValidator.validate()
           called directly and the same validator invoked through
           `samsara-cli validate` (CLI) must see IDENTICAL exclusion
           behavior. If the CLI or the validator internals ever grow a
           second/duplicate exclusion list, the two call paths would drift
           and produce a different issue count for the same directory.
"""

from pathlib import Path

from typer.testing import CliRunner

from samsara_cli.main import app
from samsara_cli.validators.target import TargetValidator


runner = CliRunner()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def plant_noise_in_changes(root: Path) -> Path:
    """Plant a leak-pattern .md file under changes/ (must be excluded)."""
    changes_dir = root / "changes" / "2026-01-01_some-feature"
    changes_dir.mkdir(parents=True)
    noise_file = changes_dir / "plan.md"
    noise_file.write_text(
        "# Plan\n\nStep 3: invoke `samsara:planning` to continue the chain.\n"
    )
    return noise_file


def plant_leak_in_skills(root: Path) -> Path:
    """Plant a genuine leak-pattern .md file under skills/ (must be caught)."""
    skill_dir = root / "skills" / "samsara-example"
    skill_dir.mkdir(parents=True)
    leak_file = skill_dir / "SKILL.md"
    leak_file.write_text(
        "---\nname: example\ndescription: Example\n---\n\n"
        "After this, invoke `samsara:planning` to proceed.\n"
    )
    return leak_file


# ---------------------------------------------------------------------------
# DTV-3-1: Noise under changes/ must not be counted
# ---------------------------------------------------------------------------


class TestDTV31NoiseUnderChangesExcluded:
    def test_planted_leak_pattern_under_changes_is_not_reported(self, tmp_path: Path):
        """
        A leak-pattern-looking .md file planted under changes/ is legitimate
        historical/demonstrative text, not a real unconverted chain link.
        It must NOT appear in the validator's issue list.
        """
        plant_noise_in_changes(tmp_path)

        validator = TargetValidator()
        errors = validator.validate(output_dir=tmp_path, platform="codex")

        assert errors == [], (
            "SILENT FAILURE [DTV-3-1]: TargetValidator counted a leak pattern "
            f"planted under changes/ as a real issue. Got: {errors}. "
            "Noise under changes/ must be excluded from the live-surface scan."
        )


# ---------------------------------------------------------------------------
# DTV-3-2: Leak under skills/ (live surface) must still be caught
# ---------------------------------------------------------------------------


class TestDTV32LiveSurfaceLeakStillCaught:
    def test_planted_leak_pattern_under_skills_is_still_reported(self, tmp_path: Path):
        """
        skills/ is live instruction surface (SS-1). A genuine unconverted
        chain-link pattern planted there must still be reported as an issue —
        the exclusion list must never shadow a live-surface path.
        """
        plant_leak_in_skills(tmp_path)

        validator = TargetValidator()
        errors = validator.validate(output_dir=tmp_path, platform="codex")

        assert len(errors) > 0, (
            "SILENT FAILURE [DTV-3-2]: TargetValidator did not report a genuine "
            "leak pattern planted under skills/. The live-surface exclusion "
            "list must never shadow skills/ — this would let real chain "
            "breaks in shipped skill content go undetected."
        )

    def test_noise_excluded_but_live_leak_still_counted_together(self, tmp_path: Path):
        """
        With BOTH a changes/ noise file and a skills/ live leak present in
        the same tree, the issue count must reflect ONLY the live leak —
        proving the exclusion filters noise without swallowing real issues.
        """
        plant_noise_in_changes(tmp_path)
        plant_leak_in_skills(tmp_path)

        validator = TargetValidator()
        errors = validator.validate(output_dir=tmp_path, platform="codex")

        assert len(errors) == 1, (
            "SILENT FAILURE [DTV-3-2]: expected exactly 1 issue (the skills/ "
            f"leak) with changes/ noise excluded. Got {len(errors)}: {errors}"
        )
        error_text = " ".join(errors)
        assert "changes" not in error_text, (
            f"changes/ noise leaked into the issue list: {errors}"
        )
        assert "skills" in error_text, (
            f"The live skills/ leak was not reported: {errors}"
        )


# ---------------------------------------------------------------------------
# DTV-3-3: Direct call and CLI call must see identical exclusion behavior
# (SD-1 — single constant, no duplicate exclusion list)
# ---------------------------------------------------------------------------


class TestDTV33SingleConstantSharedByDirectCallAndCLI:
    def test_direct_call_and_cli_call_report_same_issue_count(self, tmp_path: Path):
        """
        Calling TargetValidator().validate() directly and invoking
        `samsara-cli validate` (which delegates to the same TargetValidator)
        must observe the SAME exclusion behavior on the same directory.

        If the CLI (main.py) or the validator ever grows a second, divergent
        exclusion list, a direct caller of TargetValidator would see a
        different issue count than a CLI user validating the identical
        directory — this test pins that they must not drift apart.
        """
        plant_noise_in_changes(tmp_path)
        plant_leak_in_skills(tmp_path)

        validator = TargetValidator()
        direct_errors = validator.validate(output_dir=tmp_path, platform="codex")

        result = runner.invoke(
            app,
            ["validate", "--platform", "codex", "--source", str(tmp_path)],
        )

        assert len(direct_errors) == 1, (
            f"Precondition failed: expected exactly 1 direct-call issue, got "
            f"{direct_errors}"
        )
        assert result.exit_code != 0, (
            "SILENT FAILURE [DTV-3-3]: CLI exited 0 despite the direct "
            f"TargetValidator call reporting {len(direct_errors)} issue(s). "
            "CLI and direct call diverged — a duplicate exclusion list may "
            "exist in main.py."
        )
        assert "1 error(s) found" in result.output, (
            "SILENT FAILURE [DTV-3-3]: CLI reported a different issue count "
            f"than the direct call ({len(direct_errors)}). CLI output: "
            f"{result.output!r}"
        )

    def test_direct_call_and_cli_call_agree_on_clean_output(self, tmp_path: Path):
        """
        With ONLY changes/ noise (no live leak), both the direct call and the
        CLI call must report zero issues and the CLI must exit 0.
        """
        plant_noise_in_changes(tmp_path)

        validator = TargetValidator()
        direct_errors = validator.validate(output_dir=tmp_path, platform="codex")

        result = runner.invoke(
            app,
            ["validate", "--platform", "codex", "--source", str(tmp_path)],
        )

        assert direct_errors == [], (
            f"Precondition failed: expected no direct-call issues, got {direct_errors}"
        )
        assert result.exit_code == 0, (
            "SILENT FAILURE [DTV-3-3]: CLI reported an error despite the "
            f"direct TargetValidator call reporting none. CLI output: "
            f"{result.output!r}"
        )


# ---------------------------------------------------------------------------
# Unit tests — contract-bound to TargetValidator.validate()'s public return
# value (the issue list). These assert inclusion/exclusion behavior for
# planted files; they never inspect the exclusion constant's internal
# representation (per the task's Unit Test Contract).
# ---------------------------------------------------------------------------


class TestLiveSurfaceExclusionCoversAllFourPrefixes:
    """Each of the four documented top-level prefixes (SS-1: changes/, docs/,
    bugfix/, tests/) excludes planted noise on its own — not just changes/."""

    def test_docs_top_level_prefix_excluded(self, tmp_path: Path):
        docs_dir = tmp_path / "docs" / "specs"
        docs_dir.mkdir(parents=True)
        (docs_dir / "design.md").write_text(
            "See invoke `samsara:planning` for background.\n"
        )
        validator = TargetValidator()
        errors = validator.validate(output_dir=tmp_path, platform="codex")
        assert errors == [], f"docs/ noise was not excluded: {errors}"

    def test_bugfix_top_level_prefix_excluded(self, tmp_path: Path):
        bugfix_dir = tmp_path / "bugfix" / "2026-01-01_issue"
        bugfix_dir.mkdir(parents=True)
        (bugfix_dir / "notes.md").write_text('subagent_type: "samsara:implementer"\n')
        validator = TargetValidator()
        errors = validator.validate(output_dir=tmp_path, platform="codex")
        assert errors == [], f"bugfix/ noise was not excluded: {errors}"

    def test_tests_top_level_prefix_excluded(self, tmp_path: Path):
        fixtures_dir = tmp_path / "tests" / "fixtures"
        fixtures_dir.mkdir(parents=True)
        (fixtures_dir / "sample.md").write_text(
            "invoke `samsara:research` as a fixture example.\n"
        )
        validator = TargetValidator()
        errors = validator.validate(output_dir=tmp_path, platform="codex")
        assert errors == [], f"tests/ noise was not excluded: {errors}"

    def test_nested_file_deep_under_excluded_prefix_is_also_excluded(
        self, tmp_path: Path
    ):
        """Exclusion applies to the whole subtree, not just direct children."""
        deep_dir = tmp_path / "changes" / "feature" / "tasks" / "nested" / "deep"
        deep_dir.mkdir(parents=True)
        (deep_dir / "task.md").write_text("invoke `samsara:planning` deep nesting.\n")
        validator = TargetValidator()
        errors = validator.validate(output_dir=tmp_path, platform="codex")
        assert errors == [], f"Deeply nested changes/ noise was not excluded: {errors}"


class TestLiveSurfaceExclusionDoesNotOverreach:
    """The exclusion must match the exact top-level path SEGMENT, not any
    directory name that merely starts with an excluded prefix string."""

    def test_directory_name_prefix_collision_is_not_excluded(self, tmp_path: Path):
        """
        A top-level directory named 'docs-site' (which starts with the
        substring "docs" but is NOT the segment "docs") must still be
        scanned — a naive `str.startswith("docs")` prefix check would wrongly
        exclude it. This guards the SS-1 boundary against over-exclusion.
        """
        collision_dir = tmp_path / "docs-site"
        collision_dir.mkdir()
        (collision_dir / "page.md").write_text(
            "invoke `samsara:planning` should still be caught here.\n"
        )
        validator = TargetValidator()
        errors = validator.validate(output_dir=tmp_path, platform="codex")
        assert len(errors) > 0, (
            "Over-exclusion: 'docs-site/' was wrongly excluded because it "
            "shares a string prefix with 'docs/'. The exclusion must match "
            "the exact top-level path segment."
        )

    def test_excluded_prefix_nested_inside_live_surface_is_not_excluded(
        self, tmp_path: Path
    ):
        """
        A directory literally named 'changes' nested INSIDE skills/ (not at
        the tree's top level) must still be scanned — SS-1 excludes top-level
        changes/, not any directory named 'changes' anywhere in the tree.
        """
        nested_dir = tmp_path / "skills" / "samsara-example" / "changes"
        nested_dir.mkdir(parents=True)
        (nested_dir / "log.md").write_text(
            "invoke `samsara:planning` nested under skills/.\n"
        )
        validator = TargetValidator()
        errors = validator.validate(output_dir=tmp_path, platform="codex")
        assert len(errors) > 0, (
            "Over-exclusion: a 'changes' directory nested under skills/ (not "
            "at top level) was wrongly excluded. Only the top-level "
            "changes/ prefix is in scope for exclusion."
        )


class TestLiveSurfaceExclusionAppliesRegardlessOfPlatform:
    def test_exclusion_holds_for_gemini_platform_too(self, tmp_path: Path):
        """
        The live-surface scan boundary is platform-independent — it governs
        which files are scanned for source patterns, not platform-specific
        layout. Noise under changes/ must be excluded for gemini-cli too.

        Note: gemini-cli triggers additional Gemini-layout checks unrelated
        to pattern scanning (e.g. missing .gemini/skills). This test asserts
        only the pattern-scan contract — that no reported issue mentions the
        changes/ noise file — not the full error list, since layout checks
        are out of scope for the live-surface exclusion boundary.
        """
        noise_file = plant_noise_in_changes(tmp_path)
        validator = TargetValidator()
        errors = validator.validate(output_dir=tmp_path, platform="gemini-cli")
        error_text = " ".join(errors)
        assert noise_file.name not in error_text and "changes" not in error_text, (
            f"changes/ noise was not excluded for platform=gemini-cli: {errors}"
        )
