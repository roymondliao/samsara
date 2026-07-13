"""Behavior contracts for the Planning authority-graph validator."""

import importlib.util

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_PATH = ROOT / "skills" / "planning" / "scripts" / "validate_format.py"


def _load_validator():
    spec = importlib.util.spec_from_file_location("planning_validator", VALIDATOR_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_feature(root: Path) -> None:
    (root / "tasks").mkdir()
    (root / "pre-thinking.md").write_text(
        "\n".join(
            (
                "### Domain core identity (codebase-craft)",
                "**Decision ID:** PT-CI",
                "**Canonical label:** demo-domain",
                "### Decision: storage-boundary",
                "**Decision ID:** PT-D1",
                "#### Seam: demo-boundary",
                "**Decision ID:** PT-S1",
                "### Evaluation Contract",
                "**Contract ID:** PT-EVAL",
                "**Canonical label:** evaluation-contract",
            )
        ),
        encoding="utf-8",
    )
    (root / "2-plan.md").write_text(
        """# Plan: demo
## Source Contract
- Evaluation: PT-EVAL (evaluation-contract)
## Planning Decisions
### PL-D1: boundary
Source refs:
- PT-D1 (storage-boundary)
- PT-S1 (demo-boundary)
## Acceptance Mapping
- AC-1 (reject-invalid-input) → task-1 — planning ref: PL-D1 (boundary)
""",
        encoding="utf-8",
    )
    (root / "acceptance.yaml").write_text(
        """feature: demo
evaluator_ref: PT-EVAL
scenarios:
  - id: AC-1
    label: reject-invalid-input
    type: death_path
    source_refs: [PT-D1]
    given: x
    when: y
    then: [z]
not_applicable: []
""",
        encoding="utf-8",
    )
    (root / "overview.md").write_text(
        """# Overview: demo
> Derived implementation projection.
## Core Identity Projection
- source_ref: PT-CI
  consequence: keep the boundary
## Real Seams Projection
- seam: demo-boundary
  source_ref: PT-S1
  source: pre-thinking.md#demo-boundary
  what: demo boundary
  evidence: domain-essential
  planned: task-1
""",
        encoding="utf-8",
    )
    (root / "index.yaml").write_text(
        """feature: demo
status: pending
sources:
  pre_thinking: pre-thinking.md
  plan: 2-plan.md
  acceptance: acceptance.yaml
  overview: overview.md
tasks:
  - id: task-1
    task_file: tasks/task-1.md
    title: demo
    status: pending
    planning_refs: [PL-D1]
    decision_refs: [PT-D1, PT-S1]
    acceptance_refs: [AC-1]
    depends_on: []
    seam: demo-boundary
    affects: []
    anchors: []
""",
        encoding="utf-8",
    )
    (root / "tasks" / "task-1.md").write_text(
        """# Task 1: demo
**Task ID:** task-1
## Source References
- Planning: PL-D1 (boundary)
- Design: PT-D1 (storage-boundary), PT-S1 (demo-boundary)
- Acceptance: AC-1 (reject-invalid-input)
- Seam: demo-boundary
## Files
- Modify: `src/demo.py`
""",
        encoding="utf-8",
    )


def test_reference_graph_clean_fixture_passes(tmp_path: Path) -> None:
    _write_feature(tmp_path)
    assert _load_validator().validate(tmp_path) == []


def test_source_paths_are_live_references_not_labels(tmp_path: Path) -> None:
    _write_feature(tmp_path)
    for original, relocated in (
        ("pre-thinking.md", "design-authority.md"),
        ("2-plan.md", "planning-judgment.md"),
        ("acceptance.yaml", "behavior-contract.yaml"),
        ("overview.md", "dispatch-projection.md"),
    ):
        (tmp_path / original).rename(tmp_path / relocated)

    index = (tmp_path / "index.yaml").read_text(encoding="utf-8")
    index = (
        index.replace("pre-thinking.md", "design-authority.md")
        .replace("2-plan.md", "planning-judgment.md")
        .replace("acceptance.yaml", "behavior-contract.yaml")
        .replace("overview.md", "dispatch-projection.md")
    )
    (tmp_path / "index.yaml").write_text(index, encoding="utf-8")

    assert _load_validator().validate(tmp_path) == []


def test_missing_upstream_decision_ref_is_a_finding(tmp_path: Path) -> None:
    _write_feature(tmp_path)
    index = (tmp_path / "index.yaml").read_text(encoding="utf-8")
    (tmp_path / "index.yaml").write_text(
        index.replace("PT-D1, PT-S1", "PT-D404, PT-S1"), encoding="utf-8"
    )

    findings = _load_validator().validate(tmp_path)
    assert any(
        "decision-ref" in finding and "PT-D404" in finding for finding in findings
    )


def test_missing_task_file_and_acceptance_ref_are_findings(tmp_path: Path) -> None:
    _write_feature(tmp_path)
    (tmp_path / "tasks" / "task-1.md").unlink()
    index = (tmp_path / "index.yaml").read_text(encoding="utf-8")
    (tmp_path / "index.yaml").write_text(
        index.replace("AC-1", "AC-404"), encoding="utf-8"
    )

    findings = _load_validator().validate(tmp_path)
    assert any("task-file" in finding for finding in findings)
    assert any(
        "acceptance-ref" in finding and "AC-404" in finding for finding in findings
    )


def test_missing_declared_write_scope_is_a_finding(tmp_path: Path) -> None:
    _write_feature(tmp_path)
    task = tmp_path / "tasks" / "task-1.md"
    task.write_text(
        task.read_text(encoding="utf-8").split("## Files", 1)[0],
        encoding="utf-8",
    )

    findings = _load_validator().validate(tmp_path)
    assert any("task-write-scope" in finding for finding in findings)


def test_wrong_human_label_is_a_drift_finding(tmp_path: Path) -> None:
    _write_feature(tmp_path)
    task = tmp_path / "tasks" / "task-1.md"
    task.write_text(
        task.read_text(encoding="utf-8").replace(
            "PT-D1 (storage-boundary)", "PT-D1 (request-routing)"
        ),
        encoding="utf-8",
    )

    findings = _load_validator().validate(tmp_path)
    assert any(
        "ref-label-drift" in finding and "PT-D1" in finding for finding in findings
    )


def test_bare_human_ref_is_a_missing_label_finding(tmp_path: Path) -> None:
    _write_feature(tmp_path)
    task = tmp_path / "tasks" / "task-1.md"
    task.write_text(
        task.read_text(encoding="utf-8").replace("AC-1 (reject-invalid-input)", "AC-1"),
        encoding="utf-8",
    )

    findings = _load_validator().validate(tmp_path)
    assert any(
        "ref-label-missing" in finding and "AC-1" in finding for finding in findings
    )


def test_duplicate_authority_id_is_a_finding(tmp_path: Path) -> None:
    _write_feature(tmp_path)
    pre_thinking = tmp_path / "pre-thinking.md"
    pre_thinking.write_text(
        pre_thinking.read_text(encoding="utf-8")
        + "\n### Decision: duplicate-boundary\n**Decision ID:** PT-D1\n",
        encoding="utf-8",
    )
    plan = tmp_path / "2-plan.md"
    plan.write_text(
        plan.read_text(encoding="utf-8") + "\n### PL-D1: duplicate-planning-boundary\n",
        encoding="utf-8",
    )

    findings = _load_validator().validate(tmp_path)
    assert any(
        "authority-id" in finding and "duplicate `PT-D1`" in finding
        for finding in findings
    )
    assert any(
        "authority-id" in finding and "duplicate `PL-D1`" in finding
        for finding in findings
    )


def test_dependency_cycle_is_a_finding(tmp_path: Path) -> None:
    _write_feature(tmp_path)
    index = (tmp_path / "index.yaml").read_text(encoding="utf-8")
    second = """
  - id: task-2
    task_file: tasks/task-2.md
    title: second
    status: pending
    planning_refs: [PL-D1]
    decision_refs: [PT-D1]
    acceptance_refs: [AC-1]
    depends_on: [task-1]
    seam: demo-boundary
    affects: []
    anchors: []
"""
    index = index.replace("depends_on: []", "depends_on: [task-2]") + second
    (tmp_path / "index.yaml").write_text(index, encoding="utf-8")
    (tmp_path / "tasks" / "task-2.md").write_text(
        "**Task ID:** task-2\n- Planning: PL-D1 (boundary)\n"
        "- Design: PT-D1 (storage-boundary)\n"
        "- Acceptance: AC-1 (reject-invalid-input)\n"
        "## Files\n- Modify: `src/second.py`\n",
        encoding="utf-8",
    )

    findings = _load_validator().validate(tmp_path)
    assert any("depends-cycle" in finding for finding in findings)
