"""
Death test — supply-chain sync for nested companion templates.

A companion template file nested under a skill's `templates/` subdirectory
(e.g. skills/planning/templates/*.yaml) must survive the multi-platform
conversion. This module guards the death case: a new template silently
missing from the multi-platform conversion output means the supply chain is
incomplete with nobody noticing. (Originally added by the structural-honesty
feature with structure-spec.yaml as the vehicle; the fixture is now a
neutral nested-template.yaml — the guarded property is unchanged.)

Why this is not fully covered by tests/integration/test_snapshot.py's
generic byte-diff already:
  The generic snapshot comparison (DC-9-7/8/9) catches ANY extra/missing/
  changed file — but it is satisfied the instant someone runs
  UPDATE_SNAPSHOTS=1, which does not verify the regenerated content is the
  CORRECT converted content, only that actual == whatever was last written.
  This module pins the specific, named claim: the committed
  tests/fixtures/expected/<platform>/ snapshot contains a companion file
  nested under templates/ whose bytes are IDENTICAL to the fixture source's
  templates/nested-template.yaml (YAML companion files are copied verbatim,
  never rule-transformed — samsara_cli/converter/skill.py's
  _process_companion_file contract).

Contract source (Unit Test Contract, task-5): emitted output — the actual
file existence and byte content of tests/fixtures/expected/<platform>/ and a
fresh ConversionEngine run against tests/fixtures/source/. Nothing here
asserts SkillConverter's internal implementation.

Assumption: the fixture source skill "implement" is present at
tests/fixtures/source/skills/implement/ and its output directory name is
"samsara-implement" (naming.skill_prefix="samsara" + separator="-" + name
"implement" from its SKILL.md frontmatter). If the naming convention or the
fixture skill's frontmatter `name:` field changes, the hardcoded output path
below must be updated — this is a known coupling to the fixture's current
shape, not a general contract.
"""

from pathlib import Path

from samsara_cli.converter.engine import ConversionEngine

FIXTURE_SOURCE = Path(__file__).parent.parent / "fixtures" / "source"
FIXTURE_EXPECTED_CODEX = (
    Path(__file__).parent.parent / "fixtures" / "expected" / "codex"
)

# The nested companion template in the fixture source (neutral vehicle for
# the nesting-survival property).
_SOURCE_TEMPLATE = (
    FIXTURE_SOURCE / "skills" / "implement" / "templates" / "nested-template.yaml"
)

# Output paths are derived from the platform's skills_dir + naming convention
# (samsara_cli/config/platform/codex.yaml) plus the companion
# file's relative path under the source skill dir — this preserves nesting.
_CODEX_OUTPUT_REL = ".agents/skills/samsara-implement/templates/nested-template.yaml"


class TestNewTemplateSurvivesSourceFixture:
    """Sanity precondition: the fixture source actually carries the new
    companion template. If this file is ever deleted from the fixture
    source, every other assertion below still fails LOUDLY (FileNotFoundError
    reading `_SOURCE_TEMPLATE`, or a missing/EXTRA-file diff against the
    committed snapshot) — never a silent/vacuous pass. This test's value is
    failure LOCALIZATION: it names the actual missing precondition directly,
    instead of surfacing as a confusing traceback several assertions deep in
    an unrelated test."""

    def test_death__fixture_source_carries_the_new_template(self) -> None:
        assert _SOURCE_TEMPLATE.exists(), (
            f"Fixture source template missing: {_SOURCE_TEMPLATE}. "
            "Without this file present in the fixture source, the "
            "supply-chain tests below would fail with a FileNotFoundError or "
            "a snapshot diff pointing at the wrong root cause — this "
            "assertion exists to name the real missing precondition first."
        )


class TestNewTemplateSurvivesCommittedSnapshots:
    """Death test: the COMMITTED expected/ snapshot (not just a fresh
    conversion run) must contain the new template, byte-identical to the
    fixture source. This is what task-5's Death Test Requirement names
    directly: 'tests/fixtures/expected/codex/ 内必須出現轉換後的
    nested 模板'."""

    def test_death__codex_expected_snapshot_contains_converted_template(
        self,
    ) -> None:
        output_path = FIXTURE_EXPECTED_CODEX / _CODEX_OUTPUT_REL
        assert output_path.exists(), (
            f"Missing from committed codex snapshot: {output_path}. "
            "The new templates/*.yaml companion file was silently dropped "
            "from the multi-platform output — this is the I2 death case."
        )
        assert output_path.read_text(encoding="utf-8") == _SOURCE_TEMPLATE.read_text(
            encoding="utf-8"
        ), (
            "Converted codex template content differs from the fixture "
            "source. YAML companion files must be copied verbatim — any "
            "difference means rule-application leaked into a YAML file."
        )


class TestNewTemplateSurvivesFreshConversion:
    """Unit test (contract-bound): a FRESH ConversionEngine run (independent
    of any committed snapshot) must also carry the new template through,
    for both platforms. This catches a regression where someone regenerates
    the committed snapshot from a broken engine (UPDATE_SNAPSHOTS=1 would
    make TestNewTemplateSurvivesCommittedSnapshots pass vacuously by writing
    the broken output as the new 'expected') — this class re-derives the
    same claim from a live engine run each time, not from the snapshot."""

    def test_unit__fresh_codex_conversion_emits_nested_yaml_companion(
        self, tmp_path: Path
    ) -> None:
        output_dir = tmp_path / "codex_output"
        engine = ConversionEngine("codex")
        engine.run(source_dir=FIXTURE_SOURCE, output_dir=output_dir)

        emitted = output_dir / _CODEX_OUTPUT_REL
        assert emitted.exists(), (
            f"Fresh codex conversion did not emit {emitted}. "
            "The new nested templates/*.yaml companion file was dropped by "
            "the live converter, independent of any committed snapshot."
        )
        assert emitted.read_text(encoding="utf-8") == _SOURCE_TEMPLATE.read_text(
            encoding="utf-8"
        )
