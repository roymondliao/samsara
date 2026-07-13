"""Death contracts for scar-owned feature iteration state."""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[2]
SCAR_SCHEMA = ROOT / "skills" / "implement" / "templates" / "scar-schema.yaml"
ITERATION_SKILL = ROOT / "skills" / "iteration" / "SKILL.md"
ITERATION_FLOW = ROOT / "skills" / "iteration" / "flow.md"
ITERATION_LOG_TEMPLATE = (
    ROOT / "skills" / "iteration" / "templates" / "iteration-log.yaml"
)
VALIDATE_SKILL = ROOT / "skills" / "validate-and-ship" / "SKILL.md"
IMPLEMENT_DISPATCH = ROOT / "skills" / "implement" / "dispatch-template.md"


def _load(script: Path, name: str):
    previous = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec = importlib.util.spec_from_file_location(name, script)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        return module
    finally:
        sys.dont_write_bytecode = previous


implement_validator = _load(
    ROOT / "skills" / "implement" / "scripts" / "validate_format.py",
    "iteration_lifecycle_implement_validator",
)
planning_validator = _load(
    ROOT / "skills" / "planning" / "scripts" / "validate_format.py",
    "iteration_lifecycle_planning_validator",
)


def _write_scar(tmp_path: Path, items: str) -> Path:
    scar = tmp_path / "task-1-scar.yaml"
    scar.write_text(
        f"""task_id: task-1
completion_status: done_with_concerns
known_shortcuts:
{items}
silent_failure_conditions: []
assumptions_made: []
debt_registered: true
debt_location: src/example.py:10
structural_decisions: []
""",
        encoding="utf-8",
    )
    return scar


def _scar_findings(scar: Path, tmp_path: Path) -> list[str]:
    return implement_validator.validate_scar(
        scar,
        known_ids={"task-1"},
        seams=set(),
        registry=None,
        repo_root=tmp_path,
    )


def test_death__duplicate_file_scoped_scar_ids_are_rejected(tmp_path: Path) -> None:
    scar = _write_scar(
        tmp_path,
        """  - scar_id: SC-1
    what: "first wound"
    bites_when: "the first path runs"
    where: "src/example.py:10"
    status: open
    iteration: null
  - scar_id: SC-1
    what: "second wound"
    bites_when: "the second path runs"
    where: "src/example.py:20"
    status: open
    iteration: null""",
    )

    findings = _scar_findings(scar, tmp_path)

    assert any("scar-id" in finding and "duplicate" in finding for finding in findings)


def test_death__accepted_item_requires_signal_owner_rationale_and_evidence(
    tmp_path: Path,
) -> None:
    scar = _write_scar(
        tmp_path,
        """  - scar_id: SC-1
    what: "accepted without a review trigger"
    bites_when: "the dependency changes"
    where: "src/example.py:10"
    status: accepted
    iteration:
      round: 1
      action: accept
      evidence_refs: []""",
    )

    findings = _scar_findings(scar, tmp_path)

    for field in ("rationale", "re_review_signal", "owner", "evidence_refs"):
        assert any(
            "scar-lifecycle" in finding and field in finding for finding in findings
        )


@pytest.mark.parametrize(
    ("status", "iteration", "missing_fields"),
    [
        (
            "deferred",
            """      round: 1
      action: defer
      evidence_refs: [\"PT-EVAL\"]""",
            ("target", "resume_when", "owner"),
        ),
        (
            "blocked",
            """      round: 1
      action: block
      evidence_refs: [\"review-record.md#fix-1\"]""",
            ("blocker", "owner"),
        ),
    ],
)
def test_death__nonresolved_dispositions_require_resume_evidence(
    tmp_path: Path,
    status: str,
    iteration: str,
    missing_fields: tuple[str, ...],
) -> None:
    scar = _write_scar(
        tmp_path,
        f"""  - scar_id: SC-1
    what: "wound awaiting a durable disposition"
    bites_when: "the dependency changes"
    where: "src/example.py:10"
    status: {status}
    iteration:
{iteration}""",
    )

    findings = _scar_findings(scar, tmp_path)

    for field in missing_fields:
        assert any(
            "scar-lifecycle" in finding and field in finding for finding in findings
        )


def test_death__resolved_item_requires_resolution(tmp_path: Path) -> None:
    scar = _write_scar(
        tmp_path,
        """  - scar_id: SC-1
    what: "wound marked fixed without saying what changed"
    bites_when: "the old path runs"
    where: "src/example.py:10"
    status: resolved
    iteration: null""",
    )

    findings = _scar_findings(scar, tmp_path)

    assert any(
        "scar-lifecycle" in finding and "resolution" in finding for finding in findings
    )


def test_unit__complete_current_lifecycle_shapes_are_clean(tmp_path: Path) -> None:
    scar = _write_scar(
        tmp_path,
        """  - scar_id: SC-1
    what: "accepted with an observable trigger"
    bites_when: "the dependency changes"
    where: "src/example.py:10"
    status: accepted
    iteration:
      round: 1
      action: accept
      rationale: "repair would violate current scope"
      re_review_signal: "dependency version changes"
      owner: "service maintainer"
      evidence_refs: ["PT-EVAL"]""",
    )

    findings = _scar_findings(scar, tmp_path)

    assert not any(
        "scar-id" in finding or "scar-lifecycle" in finding for finding in findings
    )


def test_unit__legacy_item_without_lifecycle_fields_remains_readable(
    tmp_path: Path,
) -> None:
    scar = _write_scar(
        tmp_path,
        """  - what: "legacy wound"
    bites_when: "the old path runs"
    where: "src/example.py:10""",
    )

    findings = _scar_findings(scar, tmp_path)

    assert not any(
        "scar-id" in finding or "scar-lifecycle" in finding for finding in findings
    )


def test_death__iteration_rationale_cannot_hide_unbounded_prose_on_one_line(
    tmp_path: Path,
) -> None:
    scar = _write_scar(
        tmp_path,
        f"""  - scar_id: SC-1
    what: "accepted with an overlong rationale"
    bites_when: "the dependency changes"
    where: "src/example.py:10"
    status: accepted
    iteration:
      round: 1
      action: accept
      rationale: "{"x" * 201}"
      re_review_signal: "dependency version changes"
      owner: "service maintainer"
      evidence_refs: ["PT-EVAL"]""",
    )

    findings = _scar_findings(scar, tmp_path)

    assert any(
        "length-budget" in finding and "rationale" in finding for finding in findings
    )


def test_death__iteration_entry_shape_is_mechanically_validated(
    tmp_path: Path,
) -> None:
    feature = tmp_path / "changes" / "feature"
    feature.mkdir(parents=True)
    (feature / "overview.md").write_text("# Overview\n", encoding="utf-8")
    (feature / "index.yaml").write_text(
        """feature: x
status: done
iteration_entry:
  status: ready_for_validation
tasks: []
""",
        encoding="utf-8",
    )

    findings = planning_validator.validate(feature)

    assert any("iteration-entry" in finding for finding in findings)


def test_unit__complete_iteration_entry_shape_is_clean(tmp_path: Path) -> None:
    feature = tmp_path / "changes" / "feature"
    feature.mkdir(parents=True)
    (feature / "overview.md").write_text("# Overview\n", encoding="utf-8")
    (feature / "index.yaml").write_text(
        """feature: x
status: done
iteration_entry:
  status: ready_for_validation
  route: skip_rounds
  round: 0
  evaluator: pass
  signal_lost: 0
  stagnation_count: 0
  reason: "formats clean; evaluator passed; no actionable items"
  last_commit: abcdef1
  reversible: true
tasks: []
""",
        encoding="utf-8",
    )

    assert planning_validator.validate(feature) == []


def test_death__boolean_is_not_a_valid_iteration_count(tmp_path: Path) -> None:
    feature = tmp_path / "changes" / "feature"
    feature.mkdir(parents=True)
    (feature / "overview.md").write_text("# Overview\n", encoding="utf-8")
    (feature / "index.yaml").write_text(
        """feature: x
status: done
iteration_entry:
  status: in_progress
  route: fix_rounds
  round: true
  evaluator: fail
  signal_lost: 1
  stagnation_count: 0
  reason: "fix required"
  last_commit: null
  reversible: true
tasks: []
""",
        encoding="utf-8",
    )

    findings = planning_validator.validate(feature)

    assert any(
        "iteration-entry" in finding and "round" in finding for finding in findings
    )


def test_death__ready_checkpoint_requires_evaluator_pass(tmp_path: Path) -> None:
    feature = tmp_path / "changes" / "feature"
    feature.mkdir(parents=True)
    (feature / "overview.md").write_text("# Overview\n", encoding="utf-8")
    (feature / "index.yaml").write_text(
        """feature: x
status: done
iteration_entry:
  status: ready_for_validation
  route: unknown
  round: 0
  evaluator: unknown
  signal_lost: 1
  stagnation_count: 0
  reason: "evaluator unavailable"
  last_commit: abcdef1
  reversible: true
tasks: []
""",
        encoding="utf-8",
    )

    findings = planning_validator.validate(feature)

    assert any(
        "iteration-entry" in finding and "ready_for_validation" in finding
        for finding in findings
    )


def test_death__scar_is_the_only_new_iteration_state_artifact() -> None:
    assert ITERATION_FLOW.is_file(), "Iteration needs one executable flow authority"
    assert not ITERATION_LOG_TEMPLATE.exists(), (
        "new iteration-log production duplicates scar-owned item state"
    )
    live_instructions = (ITERATION_SKILL, ITERATION_FLOW, VALIDATE_SKILL)
    for instruction in live_instructions:
        text = instruction.read_text(encoding="utf-8").lower()
        assert "iteration-log.yaml" not in text
        assert "iteration log" not in text

    combined = "\n".join(
        instruction.read_text(encoding="utf-8") for instruction in live_instructions
    ).lower()
    assert "scar reports are the item-level ssot" in combined


def test_death__iteration_checkpoint_uses_yaml_structure_not_dot_notation() -> None:
    live_instructions = (ITERATION_SKILL, ITERATION_FLOW, VALIDATE_SKILL)
    for instruction in live_instructions:
        text = instruction.read_text(encoding="utf-8").lower()
        assert "index.yaml.iteration_entry" not in text
        assert "iteration_entry.status" not in text

    skill = ITERATION_SKILL.read_text(encoding="utf-8").lower()
    validate = VALIDATE_SKILL.read_text(encoding="utf-8").lower()
    assert "`iteration_entry` mapping in `index.yaml`" in skill
    assert "`status` field under `iteration_entry` in `index.yaml`" in validate

    flow = ITERATION_FLOW.read_text(encoding="utf-8")
    blocks = re.findall(r"```yaml\n(.*?)\n```", flow, re.DOTALL)
    checkpoint = next(
        yaml.safe_load(block) for block in blocks if "iteration_entry:" in block
    )
    entry = checkpoint["iteration_entry"]
    assert isinstance(entry, dict)
    assert {
        "status",
        "route",
        "round",
        "evaluator",
        "signal_lost",
        "stagnation_count",
        "reason",
        "last_commit",
        "reversible",
    } <= entry.keys()


def test_death__resume_uses_durable_artifacts_not_conversation_memory() -> None:
    flow = ITERATION_FLOW.read_text(encoding="utf-8").lower()

    for token in ("index.yaml", "scar-reports/", "git history"):
        assert token in flow
    assert "resume" in flow
    assert "conversation" in flow


def test_death__iteration_consumes_review_record_as_evidence_not_item_state() -> None:
    flow = ITERATION_FLOW.read_text(encoding="utf-8").lower()
    dispatch = IMPLEMENT_DISPATCH.read_text(encoding="utf-8").lower()

    assert "`changes/<feature>/review-record.md`" in flow
    for token in ("reviewer verdict", "reasoning", "arbitration"):
        assert token in flow
    assert "does not own scar lifecycle state" in flow
    assert "iteration consumes" in dispatch
    assert "no aggregation-time consumer reads `review-record.md`" not in dispatch


def test_death__validate_consumes_final_scar_dispositions() -> None:
    failure_budget = VALIDATE_SKILL.read_text(encoding="utf-8").lower()

    for status in ("resolved", "accepted", "deferred", "open", "blocked"):
        assert f"`{status}`" in failure_budget
    assert "`iteration: null`" in failure_budget
    assert "never means resolved" in failure_budget


def test_death__transition_requires_committed_clean_state() -> None:
    flow = ITERATION_FLOW.read_text(encoding="utf-8").lower()

    assert "commit" in flow
    assert "working tree" in flow
    assert "clean" in flow
    assert "before" in flow and "validate-and-ship" in flow


def test_unit__schema_declares_stable_dual_key_lifecycle() -> None:
    schema = SCAR_SCHEMA.read_text(encoding="utf-8").lower()

    for token in ("scar_id", "status: open", "iteration: null", "file-scoped"):
        assert token in schema
    assert "never renumber" in schema
    assert "original" in schema and "immutable" in schema
