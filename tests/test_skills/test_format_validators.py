"""Behavioral tests for the per-skill format-validate scripts (design note 4).

These are NOT doc-contract tests — the scripts are deterministic programs (the
teeth), so we exercise them: a clean feature validates clean, and each mechanical
failure mode produces a line-level finding. Both poles are guarded per script:
silent-green (a validator that never finds anything is cover for rot) and
over-fit (a validator that fails a legitimately-shaped artifact trains people
to stop running it).

Contract sources asserted (observable): exit codes 0/1/2 and the FINDING /
CANNOT VALIDATE line protocol documented in each script's module docstring.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def _load(script: Path, name: str):
    # dont_write_bytecode: exec'ing a module from inside a skill dir must not
    # drop __pycache__/*.pyc there — the skill converter reads every companion
    # file as UTF-8 text, and a binary cache artifact fails the whole build
    # (converter now also skips __pycache__, but do not rely on one guard).
    prev = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec = importlib.util.spec_from_file_location(name, script)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        return module
    finally:
        sys.dont_write_bytecode = prev


planning_validator = _load(
    ROOT / "skills/planning/scripts/validate_format.py", "planning_validate_format"
)
implement_validator = _load(
    ROOT / "skills/implement/scripts/validate_format.py", "implement_validate_format"
)


OVERVIEW = """# Overview: x

## Core Identity (L1)
A parser that turns raw exports into a stable schema.

## Key Decisions
- d: r

### Real Seams (L1 — single source of seam declarations)
- seam: parser-boundary
  what: the export/parse boundary
  evidence: domain-essential (formats vary, schema must not)
  planned: task-2

## File Map
- `src/parser.py` — parse
"""

INDEX = """feature: x
status: pending
tasks:
  - id: task-1
    title: "a"
    status: pending
    depends_on: []
    seam: parser-boundary
    affects:
      - task: task-2
        needs: "second exporter behind this boundary"
    anchors:
      - path: src/parser.py
        why: "caller of the boundary"
  - id: task-2
    title: "b"
    status: pending
    depends_on: [task-1]
    seam: parser-boundary
    affects: []
    anchors: []
"""

SCAR_OK = """task_id: task-1
completion_status: done
known_shortcuts: []
silent_failure_conditions: []
assumptions_made: []
debt_registered: false
debt_location: null
structural_decisions:
  - decision: "port interface between exporter and core"
    serves_seam: parser-boundary
    forced_by:
      - "affects task-2: second exporter behind this boundary"
    refused: "no generic param for an imagined third output"
    risk_if_wrong: "port reshaped once if task-2's exporter differs"
"""


@pytest.fixture
def feature_dir(tmp_path: Path) -> Path:
    feature = tmp_path / "changes" / "2026-07-06_x"
    feature.mkdir(parents=True)
    (feature / "overview.md").write_text(OVERVIEW, encoding="utf-8")
    (feature / "index.yaml").write_text(INDEX, encoding="utf-8")
    return feature


# ---------------------------------------------------------------------------
# planning validator
# ---------------------------------------------------------------------------


def test_planning_clean_feature_validates_clean(feature_dir: Path) -> None:
    assert planning_validator.validate(feature_dir) == []


def test_planning_dangling_seam_is_a_finding(feature_dir: Path) -> None:
    index = (feature_dir / "index.yaml").read_text(encoding="utf-8")
    (feature_dir / "index.yaml").write_text(
        index.replace("seam: parser-boundary", "seam: ghost-seam"), encoding="utf-8"
    )
    findings = planning_validator.validate(feature_dir)
    assert any("seam-resolves" in f and "ghost-seam" in f for f in findings)


def test_planning_affects_pointing_at_no_task_is_a_finding(feature_dir: Path) -> None:
    index = (feature_dir / "index.yaml").read_text(encoding="utf-8")
    (feature_dir / "index.yaml").write_text(
        index.replace("task: task-2", "task: task-9"), encoding="utf-8"
    )
    findings = planning_validator.validate(feature_dir)
    assert any("affects-task" in f and "task-9" in f for f in findings)


def test_planning_empty_needs_is_ordering_noise_finding(feature_dir: Path) -> None:
    index = (feature_dir / "index.yaml").read_text(encoding="utf-8")
    (feature_dir / "index.yaml").write_text(
        index.replace('needs: "second exporter behind this boundary"', 'needs: ""'),
        encoding="utf-8",
    )
    findings = planning_validator.validate(feature_dir)
    assert any("affects-needs" in f for f in findings)


def test_planning_planned_annotation_citing_imaginary_task_is_a_finding(
    feature_dir: Path,
) -> None:
    """Evidence strengthened by an imagined future task = imagination annotated
    as planned-change evidence — the exact corruption note 3's death table names."""
    overview = (feature_dir / "overview.md").read_text(encoding="utf-8")
    (feature_dir / "overview.md").write_text(
        overview.replace("planned: task-2", "planned: task-7"), encoding="utf-8"
    )
    findings = planning_validator.validate(feature_dir)
    assert any("planned-resolves" in f and "task-7" in f for f in findings)


def test_planning_missing_index_is_cannot_validate_not_clean(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        planning_validator.validate(tmp_path)


def test_planning_null_seam_is_valid(feature_dir: Path) -> None:
    index = (feature_dir / "index.yaml").read_text(encoding="utf-8")
    (feature_dir / "index.yaml").write_text(
        index.replace("    seam: parser-boundary\n", "    seam: null\n"),
        encoding="utf-8",
    )
    assert planning_validator.validate(feature_dir) == []


# ---------------------------------------------------------------------------
# implement validator
# ---------------------------------------------------------------------------


@pytest.fixture
def scarred_feature(feature_dir: Path) -> Path:
    scar_dir = feature_dir / "scar-reports"
    scar_dir.mkdir()
    (scar_dir / "task-1-scar.yaml").write_text(SCAR_OK, encoding="utf-8")
    return feature_dir


def _validate_scars(feature_dir: Path, repo_root: Path) -> list[str]:
    scar_dir = feature_dir / "scar-reports"
    known = implement_validator._known_task_ids(feature_dir)
    seams = implement_validator._declared_seams(feature_dir)
    registry = implement_validator._registry_ids(repo_root)
    findings: list[str] = []
    for scar in sorted(scar_dir.glob("*.yaml")):
        findings.extend(
            implement_validator.validate_scar(scar, known, seams, registry, repo_root)
        )
    return findings


def test_implement_clean_scar_validates_clean(
    scarred_feature: Path, tmp_path: Path
) -> None:
    assert _validate_scars(scarred_feature, tmp_path) == []


def test_implement_missing_structural_decisions_key_is_a_finding(
    scarred_feature: Path, tmp_path: Path
) -> None:
    scar_path = scarred_feature / "scar-reports" / "task-1-scar.yaml"
    scar = scar_path.read_text(encoding="utf-8")
    scar_path.write_text(scar[: scar.index("structural_decisions:")], encoding="utf-8")
    findings = _validate_scars(scarred_feature, tmp_path)
    assert any("dual-face" in f and "structural_decisions" in f for f in findings)


def test_implement_empty_structural_decisions_is_valid(
    scarred_feature: Path, tmp_path: Path
) -> None:
    """`structural_decisions: []` = checked, no bet — honest and clean."""
    scar_path = scarred_feature / "scar-reports" / "task-1-scar.yaml"
    scar = scar_path.read_text(encoding="utf-8")
    scar_path.write_text(
        scar[: scar.index("structural_decisions:")] + "structural_decisions: []\n",
        encoding="utf-8",
    )
    assert _validate_scars(scarred_feature, tmp_path) == []


def test_implement_missing_yin_face_is_a_finding(
    scarred_feature: Path, tmp_path: Path
) -> None:
    scar_path = scarred_feature / "scar-reports" / "task-1-scar.yaml"
    scar = scar_path.read_text(encoding="utf-8")
    scar_path.write_text(
        scar.replace(
            '    refused: "no generic param for an imagined third output"\n', ""
        ),
        encoding="utf-8",
    )
    findings = _validate_scars(scarred_feature, tmp_path)
    assert any("dual-face" in f and "refused" in f for f in findings)


def test_implement_uncheckable_forced_by_is_a_finding(
    scarred_feature: Path, tmp_path: Path
) -> None:
    """'felt cleaner' cites no task id / seam / git ref — a feeling posing as
    evidence must surface as a dangling-force finding."""
    scar_path = scarred_feature / "scar-reports" / "task-1-scar.yaml"
    scar = scar_path.read_text(encoding="utf-8")
    scar_path.write_text(
        scar.replace(
            '- "affects task-2: second exporter behind this boundary"',
            '- "felt cleaner"',
        ),
        encoding="utf-8",
    )
    findings = _validate_scars(scarred_feature, tmp_path)
    assert any("forced-by-resolves" in f and "nothing checkable" in f for f in findings)


def test_implement_forced_by_citing_imaginary_task_is_a_finding(
    scarred_feature: Path, tmp_path: Path
) -> None:
    scar_path = scarred_feature / "scar-reports" / "task-1-scar.yaml"
    scar = scar_path.read_text(encoding="utf-8")
    scar_path.write_text(
        scar.replace("affects task-2", "affects task-9"), encoding="utf-8"
    )
    findings = _validate_scars(scarred_feature, tmp_path)
    assert any("forced-by-resolves" in f and "task-9" in f for f in findings)


REAL_SCHEMA_REGISTRY = """entries:
  - id: real-id
    description: "a systemic fact"
    first_recorded: "2026-01-01"
    applies_when: "some condition"
"""


def test_implement_dangling_systemic_ref_is_a_finding(
    scarred_feature: Path, tmp_path: Path
) -> None:
    """Regression fixture for the entries:-schema registry-parsing bug: the
    registry fixture below mirrors .samsara/systemic-scars.yaml's real,
    documented top-level shape (`entries:` list of {id, ...} dicts) verbatim
    — not an invented shape _registry_ids happens to parse."""
    scar_path = scarred_feature / "scar-reports" / "task-1-scar.yaml"
    scar = scar_path.read_text(encoding="utf-8")
    scar_path.write_text(
        scar.replace(
            "known_shortcuts: []",
            'known_shortcuts:\n  - systemic_ref: no-such-id\n    note: "src/x.py:1"',
        ).replace("debt_registered: false", "debt_registered: true"),
        encoding="utf-8",
    )
    (tmp_path / ".samsara").mkdir(exist_ok=True)
    (tmp_path / ".samsara" / "systemic-scars.yaml").write_text(
        REAL_SCHEMA_REGISTRY, encoding="utf-8"
    )
    findings = _validate_scars(scarred_feature, tmp_path)
    assert any("systemic-ref" in f and "no-such-id" in f for f in findings)


def test_implement_valid_systemic_ref_against_real_schema_registry_is_clean(
    scarred_feature: Path, tmp_path: Path
) -> None:
    """Regression test for the entries:-schema parsing bug: citing an id that
    IS present in a registry using the real, documented `entries:` shape must
    produce NO systemic-ref finding. Before the fix, `_registry_ids()` read
    the wrong top-level key and returned `{"entries"}` — every real id,
    including this one, read as dangling regardless of registry content."""
    scar_path = scarred_feature / "scar-reports" / "task-1-scar.yaml"
    scar = scar_path.read_text(encoding="utf-8")
    scar_path.write_text(
        scar.replace(
            "known_shortcuts: []",
            'known_shortcuts:\n  - systemic_ref: real-id\n    note: "src/x.py:1"',
        ).replace("debt_registered: false", "debt_registered: true"),
        encoding="utf-8",
    )
    (tmp_path / ".samsara").mkdir(exist_ok=True)
    (tmp_path / ".samsara" / "systemic-scars.yaml").write_text(
        REAL_SCHEMA_REGISTRY, encoding="utf-8"
    )
    findings = _validate_scars(scarred_feature, tmp_path)
    assert not any("systemic-ref" in f for f in findings)


def test_implement_debt_inconsistency_is_a_finding(
    scarred_feature: Path, tmp_path: Path
) -> None:
    scar_path = scarred_feature / "scar-reports" / "task-1-scar.yaml"
    scar = scar_path.read_text(encoding="utf-8")
    scar_path.write_text(
        scar.replace(
            "silent_failure_conditions: []",
            'silent_failure_conditions:\n  - description: "fails silently when y"',
        ),
        encoding="utf-8",
    )
    findings = _validate_scars(scarred_feature, tmp_path)
    assert any("debt-consistency" in f for f in findings)


# ---------------------------------------------------------------------------
# implement validator — length-budget / legacy-form / slot-required (task-3)
#
# Contract source (all tests below): implement_validator's emitted
# FINDING <class>: <msg> line protocol, asserted via substring membership on
# the findings list returned by validate_scar/_validate_scars — same
# contract style as the pre-existing tests above. Line numbers use the
# module's own `length-budget` class name (task-3 introduces it); the exact
# budget NUMBERS asserted below are named contract values pulled from
# scar-schema.yaml's Budget section (task-2), not implementation details.
# ---------------------------------------------------------------------------

MINIMAL_CLEAN_SCAR = """task_id: task-1
completion_status: done
known_shortcuts: []
silent_failure_conditions: []
assumptions_made: []
debt_registered: false
debt_location: null
structural_decisions: []
"""


def _write_scar(scarred_feature: Path, text: str) -> None:
    (scarred_feature / "scar-reports" / "task-1-scar.yaml").write_text(
        text, encoding="utf-8"
    )


# --- death tests: over-budget fixtures must produce `length-budget` findings ---


def test_implement_overbudget_item_lines_is_a_length_budget_finding(
    scarred_feature: Path, tmp_path: Path
) -> None:
    """A known_shortcuts item spanning 15 physical lines (over the 14-line item
    budget) must be caught even though every field individually is tiny —
    this is the "dies silently under a pile of small lines" mode."""
    _write_scar(
        scarred_feature,
        """task_id: task-1
completion_status: done
known_shortcuts:
  - scar_id: SC-1
    what: "a"
    bites_when: "b"
    where: "c"
    status: accepted
    iteration:
      round: 1
      action: accept
      rationale: "d"
      re_review_signal: "e"
      owner: "f"
      evidence_refs:
        - "g"
        - "h"
        - "i"
silent_failure_conditions: []
assumptions_made: []
debt_registered: true
debt_location: "x:1"
structural_decisions: []
""",
    )
    findings = _validate_scars(scarred_feature, tmp_path)
    assert any("length-budget" in f and "line" in f for f in findings)


def test_implement_overbudget_field_chars_is_a_length_budget_finding(
    scarred_feature: Path, tmp_path: Path
) -> None:
    long_value = "B" * 250
    _write_scar(
        scarred_feature,
        f"""task_id: task-1
completion_status: done
known_shortcuts:
  - what: "{long_value}"
    bites_when: "b"
    where: "c"
silent_failure_conditions: []
assumptions_made: []
debt_registered: true
debt_location: "x:1"
structural_decisions: []
""",
    )
    findings = _validate_scars(scarred_feature, tmp_path)
    assert any("length-budget" in f and "250" in f for f in findings)


def test_implement_overbudget_narrative_is_a_length_budget_finding(
    scarred_feature: Path, tmp_path: Path
) -> None:
    narrative_lines = "\n".join(f"  line {i}" for i in range(11))
    _write_scar(
        scarred_feature,
        f"""task_id: task-1
completion_status: done
known_shortcuts: []
silent_failure_conditions: []
assumptions_made: []
debt_registered: false
debt_location: null
narrative: |
{narrative_lines}
structural_decisions: []
""",
    )
    findings = _validate_scars(scarred_feature, tmp_path)
    assert any("length-budget" in f and "narrative" in f for f in findings)


def test_implement_duplicate_narrative_key_follows_last_key_wins(
    scarred_feature: Path, tmp_path: Path
) -> None:
    """A duplicate top-level `narrative:` key is itself a separate schema
    violation, but the LINE-COUNT the validator reports for it must match
    what yaml.safe_load() actually loads (last key wins) — not silently
    read a different (e.g. first) occurrence than the one that was
    constructed. First occurrence is 11 lines (over budget); the LAST
    occurrence — the one safe_load actually keeps — is 1 line (clean). If
    the validator followed the first occurrence instead, this would wrongly
    report a narrative-budget finding."""
    over_budget_first = "\n".join(f"  line {i}" for i in range(11))
    _write_scar(
        scarred_feature,
        f"""task_id: task-1
completion_status: done
known_shortcuts: []
silent_failure_conditions: []
assumptions_made: []
debt_registered: false
debt_location: null
narrative: |
{over_budget_first}
narrative: |
  short
structural_decisions: []
""",
    )
    findings = _validate_scars(scarred_feature, tmp_path)
    assert not any("length-budget" in f and "narrative" in f for f in findings)


def test_implement_overbudget_report_lines_is_a_length_budget_finding(
    scarred_feature: Path, tmp_path: Path
) -> None:
    padding = "\n".join(f"# padding line {i}" for i in range(85))
    _write_scar(scarred_feature, padding + "\n" + MINIMAL_CLEAN_SCAR)
    findings = _validate_scars(scarred_feature, tmp_path)
    assert any("length-budget" in f and "report" in f for f in findings)


def test_implement_overbudget_structural_entry_is_a_length_budget_finding(
    scarred_feature: Path, tmp_path: Path
) -> None:
    """A structural_decisions entry spanning 11 physical lines (over the
    10-line entry budget) via a padded forced_by list — not a char overage,
    a pure line-count overage on a field class that carries no char cap."""
    _write_scar(
        scarred_feature,
        """task_id: task-1
completion_status: done
known_shortcuts: []
silent_failure_conditions: []
assumptions_made: []
debt_registered: false
debt_location: null
structural_decisions:
  - decision: "some structural bet"
    serves_seam: null
    forced_by:
      - "affects task-2: reason 1"
      - "affects task-2: reason 2"
      - "affects task-2: reason 3"
      - "affects task-2: reason 4"
      - "affects task-2: reason 5"
      - "affects task-2: reason 6"
    refused: "an alternative not built"
    risk_if_wrong: "what breaks if wrong"
""",
    )
    findings = _validate_scars(scarred_feature, tmp_path)
    assert any(
        "length-budget" in f and "structural" in f and "line" in f for f in findings
    )


def test_implement_folded_scalar_defeats_line_count_but_not_char_cap(
    scarred_feature: Path, tmp_path: Path
) -> None:
    """DC-E: a folded (`>`) scalar can pack 400 chars onto few physical
    source lines — item-line-count alone would read this item as clean (4
    lines). The char cap on the decoded value is the fallback that must
    still catch it."""
    long_value = "A" * 400
    _write_scar(
        scarred_feature,
        f"""task_id: task-1
completion_status: done
known_shortcuts:
  - what: >
      {long_value}
    bites_when: "b"
    where: "c"
silent_failure_conditions: []
assumptions_made: []
debt_registered: true
debt_location: "x:1"
structural_decisions: []
""",
    )
    findings = _validate_scars(scarred_feature, tmp_path)
    assert any("length-budget" in f and "what" in f and "chars" in f for f in findings)
    # and the item itself must NOT be flagged as over the item-line budget —
    # proving line-count alone would have missed this and the char cap is
    # doing the actual catching, not a coincidental double-hit.
    assert not any("length-budget" in f and "item budget" in f for f in findings)


# --- death tests: legacy-form (budget-evasion escape hatch) ---


def test_implement_description_dict_is_a_legacy_form_finding(
    scarred_feature: Path, tmp_path: Path
) -> None:
    _write_scar(
        scarred_feature,
        """task_id: task-1
completion_status: done
known_shortcuts:
  - description: "the old free-text way of writing a shortcut"
    status: resolved
    resolution: "fixed it"
silent_failure_conditions: []
assumptions_made: []
debt_registered: true
debt_location: "x:1"
structural_decisions: []
""",
    )
    findings = _validate_scars(scarred_feature, tmp_path)
    assert any("legacy-form" in f for f in findings)


def test_implement_plain_string_item_is_a_legacy_form_finding(
    scarred_feature: Path, tmp_path: Path
) -> None:
    _write_scar(
        scarred_feature,
        """task_id: task-1
completion_status: done
known_shortcuts:
  - "a plain string legacy shortcut with no slots at all"
silent_failure_conditions: []
assumptions_made: []
debt_registered: true
debt_location: "x:1"
structural_decisions: []
""",
    )
    findings = _validate_scars(scarred_feature, tmp_path)
    assert any("legacy-form" in f for f in findings)


def test_implement_systemic_ref_item_does_not_trigger_legacy_form(
    scarred_feature: Path, tmp_path: Path
) -> None:
    _write_scar(
        scarred_feature,
        """task_id: task-1
completion_status: done
known_shortcuts:
  - systemic_ref: some-id
    note: "this task's concrete landing point"
silent_failure_conditions: []
assumptions_made: []
debt_registered: true
debt_location: "x:1"
structural_decisions: []
""",
    )
    findings = _validate_scars(scarred_feature, tmp_path)
    assert not any("legacy-form" in f for f in findings)


# --- death tests: required slots ---


def test_implement_missing_bites_when_is_a_slot_required_finding(
    scarred_feature: Path, tmp_path: Path
) -> None:
    _write_scar(
        scarred_feature,
        """task_id: task-1
completion_status: done
known_shortcuts:
  - what: "a"
    where: "c"
silent_failure_conditions: []
assumptions_made: []
debt_registered: true
debt_location: "x:1"
structural_decisions: []
""",
    )
    findings = _validate_scars(scarred_feature, tmp_path)
    assert any("slot-required" in f and "bites_when" in f for f in findings)


def test_implement_missing_where_is_a_slot_required_finding(
    scarred_feature: Path, tmp_path: Path
) -> None:
    _write_scar(
        scarred_feature,
        """task_id: task-1
completion_status: done
known_shortcuts:
  - what: "a"
    bites_when: "b"
silent_failure_conditions: []
assumptions_made: []
debt_registered: true
debt_location: "x:1"
structural_decisions: []
""",
    )
    findings = _validate_scars(scarred_feature, tmp_path)
    assert any("slot-required" in f and "where" in f for f in findings)


def test_implement_missing_what_is_a_slot_required_finding(
    scarred_feature: Path, tmp_path: Path
) -> None:
    _write_scar(
        scarred_feature,
        """task_id: task-1
completion_status: done
known_shortcuts:
  - bites_when: "b"
    where: "c"
silent_failure_conditions: []
assumptions_made: []
debt_registered: true
debt_location: "x:1"
structural_decisions: []
""",
    )
    findings = _validate_scars(scarred_feature, tmp_path)
    assert any("slot-required" in f and "what" in f for f in findings)


# --- death test: degradation path must not silently become a pass ---


def test_implement_missing_scar_dir_is_cannot_validate_not_a_pass(
    feature_dir: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    exit_code = implement_validator.main(
        ["prog", str(feature_dir), "--repo-root", str(tmp_path)]
    )
    assert exit_code == 2
    captured = capsys.readouterr()
    assert "CANNOT VALIDATE" in captured.out


# --- unit tests: clean new-format fixture must validate clean (zero false positives) ---


def test_implement_clean_slot_form_fixture_validates_clean(
    scarred_feature: Path, tmp_path: Path
) -> None:
    """Named contract source: scar-schema.yaml's own Verbatim Example
    (task-2). If the validator flags its own documented example, the
    write-contract and its gate have drifted apart."""
    (scarred_feature / "scar-reports" / "task-2-scar.yaml").write_text(
        """task_id: task-2
completion_status: done_with_concerns
known_shortcuts:
  - what: "Sort order is insertion order, not defined by spec"
    bites_when: "a caller depends on alphabetical order"
    where: "scripts/paper_scan.py:88"
silent_failure_conditions: []
assumptions_made:
  - assumption: "all topic folders match [0-9]{2}_* pattern"
    verified: true
    note: "tests/test_paper_scan.py::test_all_folders_match_pattern"
debt_registered: true
debt_location: "scripts/paper_scan.py:88"
structural_decisions: []
""",
        encoding="utf-8",
    )
    assert _validate_scars(scarred_feature, tmp_path) == []


# --- unit test: golden re-expression (task-5) proves budget doesn't hurt honesty ---

GOLDEN_TASK4 = (
    ROOT / "tests" / "fixtures" / "scar_reports" / "golden_task4_slot_form.yaml"
)

GOLDEN_REGISTRY = """entries:
  - id: doc-vs-runtime-obedience
    description: "instructions in docs are not enforced at runtime"
    first_recorded: "2026-01-01"
    applies_when: "an instruction surface assumes an agent will read a referenced file"
"""


def test_golden_task4_re_expression_validates_clean(
    feature_dir: Path, tmp_path: Path
) -> None:
    """Named contract source: validate_format.py's emitted output (golden ->
    zero findings). This is task-5's proof that the historical worst-case
    scar report (232 lines, task-4-scar.yaml, only-read source) can be
    re-expressed in the current slot form within every budget the validator
    enforces, without losing any honest content — see this feature's
    golden-re-expression.md for the full traceability table.
    """
    scar_dir = feature_dir / "scar-reports"
    scar_dir.mkdir()
    (scar_dir / "task-4-scar.yaml").write_text(
        GOLDEN_TASK4.read_text(encoding="utf-8"), encoding="utf-8"
    )
    (tmp_path / ".samsara").mkdir(exist_ok=True)
    (tmp_path / ".samsara" / "systemic-scars.yaml").write_text(
        GOLDEN_REGISTRY, encoding="utf-8"
    )
    findings = _validate_scars(feature_dir, tmp_path)
    assert findings == [], (
        f"golden re-expression fixture is not validator-clean: {findings}"
    )


# --- death test: budget-number drift between schema declaration and validator ---


def test_implement_budget_constants_match_schema_declaration() -> None:
    """Named contract source: skills/implement/templates/scar-schema.yaml's
    Budget section (task-2) is the single declared source of these five
    numbers; validate_format.py's module-level constants must equal them.
    Either side changing alone must redden this test (DC: budget drift)."""
    schema_text = (ROOT / "skills/implement/templates/scar-schema.yaml").read_text(
        encoding="utf-8"
    )
    import re as _re

    def _num(pattern: str) -> int:
        m = _re.search(pattern, schema_text)
        assert m is not None, f"schema Budget text no longer matches {pattern!r}"
        return int(m.group(1))

    assert _num(r"field ≤(\d+) chars") == implement_validator.BUDGET_FIELD_CHARS
    assert _num(r"where ≤(\d+)\)") == implement_validator.BUDGET_WHERE_CHARS
    assert _num(r"item ≤(\d+) lines") == implement_validator.BUDGET_ITEM_LINES
    assert (
        _num(r"narrative\s*\n#\s*≤(\d+) lines")
        == implement_validator.BUDGET_NARRATIVE_LINES
    )
    assert _num(r"report ≤(\d+) lines") == implement_validator.BUDGET_REPORT_LINES
    assert (
        _num(r"own ≤(\d+) lines-per-entry")
        == implement_validator.BUDGET_STRUCTURAL_ENTRY_LINES
    )


def test_implement_char_capped_field_names_match_schema_declaration() -> None:
    """Sibling drift test to the numbers above, same property in the other
    dimension: every field NAME validate_format.py char-caps
    (CHAR_CAPPED_FIELD_NAMES, itself derived from the tuples the check
    functions actually iterate — not a hand-copied duplicate) must appear in
    scar-schema.yaml's Budget block text. Schema dropping a capped field
    name, or the validator capping a field the schema never declared, both
    redden this test."""
    import re as _re

    schema_text = (ROOT / "skills/implement/templates/scar-schema.yaml").read_text(
        encoding="utf-8"
    )
    m = _re.search(r"# Budget —.*?\n#\n# legacy-invalid:", schema_text, _re.DOTALL)
    assert m is not None, "schema Budget block boundaries no longer match"
    budget_block = m.group(0)

    for field_name in implement_validator.CHAR_CAPPED_FIELD_NAMES:
        assert field_name in budget_block, (
            f"char-capped field {field_name!r} is enforced by validate_format.py "
            "but not declared in scar-schema.yaml's Budget block"
        )
