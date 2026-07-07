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


def test_implement_dangling_systemic_ref_is_a_finding(
    scarred_feature: Path, tmp_path: Path
) -> None:
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
        "scars:\n  real-id:\n    description: x\n", encoding="utf-8"
    )
    findings = _validate_scars(scarred_feature, tmp_path)
    assert any("systemic-ref" in f and "no-such-id" in f for f in findings)


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
