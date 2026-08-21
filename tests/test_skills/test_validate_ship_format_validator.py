"""Format contracts for Validate & Ship's durable evidence manifest."""

from __future__ import annotations

import copy
import subprocess
import sys

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = ROOT / "skills" / "validate-and-ship" / "scripts" / "validate_format.py"


def _head() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


def _valid_manifest() -> dict:
    head = _head()
    return {
        "feature": "validator-contract",
        "delivered_capability": {
            "summary": "Validate one evidence manifest.",
            "source_refs": ["AC-1"],
        },
        "snapshot": {"base_commit": head, "candidate_commit": head},
        "validation_status": "ready_for_delivery",
        "validation": {
            "next_finding_number": 1,
            "findings": [],
            "security_privacy": {
                "status": "pass",
                "scope_ref": f"{head}...{head}",
                "evidence_refs": ["review-record.md#security-pass"],
                "accepted_risks": [],
            },
            "remaining_exposure": {
                "status": "pass",
                "accepted_refs": ["scar-reports/task-1-scar.yaml#SC-1"],
                "deferred_refs": [],
                "open_refs": [],
                "blocked_refs": [],
            },
            "acceptance": {
                "status": "pass",
                "scenario_results": [
                    {
                        "scenario_ref": "AC-1",
                        "status": "pass",
                        "evidence_refs": ["tests/test_contract.py::test_contract"],
                    }
                ],
            },
            "primary_evaluator": {
                "evaluator_ref": "PT-EVAL",
                "status": "pass",
                "evidence_refs": ["review-record.md#primary-evaluator"],
            },
            "e2e": {
                "status": "not_applicable",
                "evidence_refs": ["acceptance.yaml#not_applicable"],
            },
            "reconciliation": {"status": "pass", "drift": []},
            "review_evidence": {
                "status": "pass",
                "evidence_refs": [
                    "review-record.md#task-1-yin",
                    "review-record.md#task-1-quality",
                ],
            },
        },
        "operational_controls": {
            "monitoring": {
                "status": "absent",
                "mechanism": None,
                "evidence_refs": [],
            },
            "rollback_or_disable": {
                "status": "not_applicable",
                "mechanism": None,
                "evidence_refs": [],
            },
        },
        "delivery": {
            "action": "keep_branch",
            "selected_by": "human",
            "decision_ref": None,
            "preparation": ["Keep the committed branch available for review."],
        },
    }


def _write_feature(tmp_path: Path, manifest: dict) -> Path:
    feature = tmp_path / "feature"
    scars = feature / "scar-reports"
    scars.mkdir(parents=True)
    (feature / "ship-manifest.yaml").write_text(
        yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8"
    )
    (feature / "acceptance.yaml").write_text(
        yaml.safe_dump({"scenarios": [{"id": "AC-1"}], "not_applicable": []}),
        encoding="utf-8",
    )
    (feature / "pre-thinking.md").write_text(
        "**Contract ID:** PT-EVAL\n", encoding="utf-8"
    )
    (feature / "2-plan.md").write_text(
        "### PL-D1: Contract boundary\n", encoding="utf-8"
    )
    (feature / "index.yaml").write_text(
        yaml.safe_dump(
            {
                "iteration_entry": {
                    "status": "ready_for_validation",
                    "last_commit": _head(),
                }
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    (feature / "review-record.md").write_text(
        "# security-pass\n# primary-evaluator\n# task-1-yin\n# task-1-quality\n",
        encoding="utf-8",
    )
    (scars / "task-1-scar.yaml").write_text(
        yaml.safe_dump(
            {
                "task_id": "task-1",
                "known_shortcuts": [
                    {
                        "scar_id": "SC-1",
                        "what": "Accepted fixture exposure",
                        "status": "accepted",
                    }
                ],
                "silent_failure_conditions": [],
                "assumptions_made": [],
                "structural_decisions": [],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    return feature


def _auto_decision(
    number: int,
    *,
    gate_id: str = "validation.delivery",
    answer: str = "keep_branch",
    supersedes: str = "null",
) -> str:
    decision_id = f"decision-{number:03d}"
    return f"""## {decision_id} — {gate_id}

```yaml
schema_version: 1
decision_id: {decision_id}
timestamp: "2026-07-15T12:00:00+08:00"
decided_by: auto-gatekeeper
stage: validation
gate_id: {gate_id}
workflow_prompt: "Choose the delivery action."
answer: "{answer}"
decision: proceed
reason:
  - "Validation is complete."
evidence_refs:
  - "ship-manifest.yaml#validation_status"
uncertainty:
  level: low
  notes: none
next_action:
  type: continue
  target: "{answer}"
gap: null
supersedes: {supersedes}
```
"""


def _run(feature: Path, repo_root: Path = ROOT) -> subprocess.CompletedProcess[str]:
    assert VALIDATOR.is_file(), "Validate & Ship must own a format validator"
    return subprocess.run(
        [
            sys.executable,
            str(VALIDATOR),
            str(feature),
            "--repo-root",
            str(repo_root),
        ],
        capture_output=True,
        text=True,
        check=False,
    )


def test_unit__valid_evidence_manifest_is_clean(tmp_path: Path) -> None:
    result = _run(_write_feature(tmp_path, _valid_manifest()))

    assert result.returncode == 0, result.stdout + result.stderr
    assert "FORMAT OK" in result.stdout


def test_death__ready_manifest_cannot_hide_open_exposure(tmp_path: Path) -> None:
    manifest = _valid_manifest()
    manifest["validation"]["remaining_exposure"]["open_refs"] = [
        "scar-reports/task-1-scar.yaml#SC-1"
    ]
    result = _run(_write_feature(tmp_path, manifest))

    assert result.returncode == 1
    assert "ready-for-delivery" in result.stdout.lower()
    assert "open_refs" in result.stdout


def test_death__available_control_requires_evidence(tmp_path: Path) -> None:
    manifest = _valid_manifest()
    manifest["operational_controls"]["monitoring"]["status"] = "available"
    result = _run(_write_feature(tmp_path, manifest))

    assert result.returncode == 1
    assert "monitoring" in result.stdout
    assert "mechanism" in result.stdout and "evidence_refs" in result.stdout


def test_death__auto_delivery_requires_decision_ref(tmp_path: Path) -> None:
    manifest = _valid_manifest()
    manifest["delivery"]["selected_by"] = "auto-gatekeeper"
    result = _run(_write_feature(tmp_path, manifest))

    assert result.returncode == 1
    assert "decision_ref" in result.stdout


def test_unit__auto_delivery_ref_matches_current_decision(tmp_path: Path) -> None:
    manifest = _valid_manifest()
    manifest["delivery"] = {
        "action": "keep_branch",
        "selected_by": "auto-gatekeeper",
        "decision_ref": "auto-decisions.md#decision-001",
        "preparation": [],
    }
    feature = _write_feature(tmp_path, manifest)
    (feature / "auto-decisions.md").write_text(_auto_decision(1), encoding="utf-8")

    result = _run(feature)

    assert result.returncode == 0, result.stdout + result.stderr


def test_death__auto_delivery_ref_rejects_answer_action_drift(
    tmp_path: Path,
) -> None:
    manifest = _valid_manifest()
    manifest["delivery"] = {
        "action": "merge",
        "selected_by": "auto-gatekeeper",
        "decision_ref": "auto-decisions.md#decision-001",
        "preparation": [],
    }
    feature = _write_feature(tmp_path, manifest)
    (feature / "auto-decisions.md").write_text(
        _auto_decision(1, answer="keep_branch"), encoding="utf-8"
    )

    result = _run(feature)

    assert result.returncode == 1
    assert "delivery-decision" in result.stdout
    assert "answer" in result.stdout


def test_death__auto_delivery_ref_rejects_wrong_gate(tmp_path: Path) -> None:
    manifest = _valid_manifest()
    manifest["delivery"] = {
        "action": "keep_branch",
        "selected_by": "auto-gatekeeper",
        "decision_ref": "auto-decisions.md#decision-001",
        "preparation": [],
    }
    feature = _write_feature(tmp_path, manifest)
    (feature / "auto-decisions.md").write_text(
        _auto_decision(1, gate_id="validation.security-result"), encoding="utf-8"
    )

    result = _run(feature)

    assert result.returncode == 1
    assert "delivery-decision" in result.stdout
    assert "validation.delivery" in result.stdout


def test_death__auto_delivery_ref_rejects_superseded_decision(
    tmp_path: Path,
) -> None:
    manifest = _valid_manifest()
    manifest["delivery"] = {
        "action": "keep_branch",
        "selected_by": "auto-gatekeeper",
        "decision_ref": "auto-decisions.md#decision-001",
        "preparation": [],
    }
    feature = _write_feature(tmp_path, manifest)
    (feature / "auto-decisions.md").write_text(
        _auto_decision(1)
        + "\n"
        + _auto_decision(2, answer="merge", supersedes="decision-001"),
        encoding="utf-8",
    )

    result = _run(feature)

    assert result.returncode == 1
    assert "delivery-decision" in result.stdout
    assert "superseded" in result.stdout


def test_death__dangling_authority_and_scar_refs_are_findings(tmp_path: Path) -> None:
    manifest = _valid_manifest()
    manifest["delivered_capability"]["source_refs"] = ["AC-404"]
    manifest["validation"]["remaining_exposure"]["accepted_refs"] = [
        "scar-reports/task-1-scar.yaml#SC-404"
    ]
    result = _run(_write_feature(tmp_path, manifest))

    assert result.returncode == 1
    assert "AC-404" in result.stdout
    assert "SC-404" in result.stdout


def test_death__invalid_yaml_is_cannot_validate(tmp_path: Path) -> None:
    feature = _write_feature(tmp_path, _valid_manifest())
    (feature / "ship-manifest.yaml").write_text("validation: [\n", encoding="utf-8")
    result = _run(feature)

    assert result.returncode == 2
    assert "CANNOT VALIDATE" in result.stdout


def test_death__ready_manifest_requires_every_mandatory_step_pass(
    tmp_path: Path,
) -> None:
    for step in (
        "security_privacy",
        "remaining_exposure",
        "acceptance",
        "primary_evaluator",
        "reconciliation",
        "review_evidence",
    ):
        manifest = copy.deepcopy(_valid_manifest())
        manifest["validation"][step]["status"] = "unknown"
        result = _run(_write_feature(tmp_path / step, manifest))
        assert result.returncode == 1
        assert step in result.stdout


def test_death__validation_finding_requires_stable_shape_and_locator(
    tmp_path: Path,
) -> None:
    manifest = _valid_manifest()
    manifest["validation_status"] = "blocked"
    manifest["delivery"] = {
        "action": "pending",
        "selected_by": None,
        "decision_ref": None,
        "preparation": [],
    }
    manifest["validation"]["findings"] = [
        {
            "id": "VF-1",
            "step": "acceptance",
            "result": "fail",
            "owner": "iteration",
            "observable_result": "AC-1 returned the wrong value.",
            "evidence_refs": [],
            "severity": None,
            "path": None,
            "location": None,
            "source_ref": None,
        }
    ]
    manifest["validation"]["next_finding_number"] = 2

    result = _run(_write_feature(tmp_path, manifest))

    assert result.returncode == 1
    assert "evidence_refs" in result.stdout
    assert "locator" in result.stdout


def test_unit__validation_finding_accepts_evidence_backed_path_without_severity(
    tmp_path: Path,
) -> None:
    manifest = _valid_manifest()
    manifest["validation_status"] = "blocked"
    manifest["validation"]["acceptance"]["status"] = "fail"
    manifest["delivery"] = {
        "action": "pending",
        "selected_by": None,
        "decision_ref": None,
        "preparation": [],
    }
    manifest["validation"]["findings"] = [
        {
            "id": "VF-1",
            "step": "acceptance",
            "result": "fail",
            "owner": "iteration",
            "observable_result": "AC-1 returned the wrong value.",
            "evidence_refs": ["tests/test_contract.py::test_contract"],
            "severity": None,
            "path": "src/contract.py",
            "location": "validate_result",
            "source_ref": None,
        }
    ]
    manifest["validation"]["next_finding_number"] = 2

    result = _run(_write_feature(tmp_path, manifest))

    assert result.returncode == 0, result.stdout + result.stderr


def test_death__ready_manifest_cannot_carry_return_findings(tmp_path: Path) -> None:
    manifest = _valid_manifest()
    manifest["validation"]["findings"] = [
        {
            "id": "VF-1",
            "step": "reconciliation",
            "result": "unknown",
            "owner": "planning",
            "observable_result": "PL-D1 no longer resolves.",
            "evidence_refs": ["2-plan.md#PL-D1"],
            "severity": None,
            "path": None,
            "location": None,
            "source_ref": "PL-D1",
        }
    ]
    manifest["validation"]["next_finding_number"] = 2

    result = _run(_write_feature(tmp_path, manifest))

    assert result.returncode == 1
    assert "ready-for-delivery" in result.stdout.lower()
    assert "findings" in result.stdout


def test_death__blocked_manifest_requires_a_durable_handoff_finding(
    tmp_path: Path,
) -> None:
    manifest = _valid_manifest()
    manifest["validation_status"] = "blocked"
    manifest["delivery"] = {
        "action": "pending",
        "selected_by": None,
        "decision_ref": None,
        "preparation": [],
    }

    result = _run(_write_feature(tmp_path, manifest))

    assert result.returncode == 1
    assert "blocked-handoff" in result.stdout
    assert "validation.findings" in result.stdout


def test_death__duplicate_validation_finding_ids_are_rejected(tmp_path: Path) -> None:
    manifest = _valid_manifest()
    manifest["validation_status"] = "blocked"
    finding = {
        "id": "VF-1",
        "step": "reconciliation",
        "result": "unknown",
        "owner": "planning",
        "observable_result": "PL-D1 no longer resolves.",
        "evidence_refs": ["2-plan.md#PL-D1"],
        "severity": None,
        "path": None,
        "location": None,
        "source_ref": "PL-D1",
    }
    manifest["validation"]["findings"] = [finding, copy.deepcopy(finding)]
    manifest["validation"]["next_finding_number"] = 2
    manifest["delivery"] = {
        "action": "pending",
        "selected_by": None,
        "decision_ref": None,
        "preparation": [],
    }

    result = _run(_write_feature(tmp_path, manifest))

    assert result.returncode == 1
    assert "duplicate" in result.stdout.lower()


def test_death__finding_number_must_advance_past_every_current_id(
    tmp_path: Path,
) -> None:
    manifest = _valid_manifest()
    manifest["validation_status"] = "blocked"
    manifest["validation"]["findings"] = [
        {
            "id": "VF-2",
            "step": "reconciliation",
            "result": "unknown",
            "owner": "planning",
            "observable_result": "PL-D1 no longer resolves.",
            "evidence_refs": ["2-plan.md#PL-D1"],
            "severity": None,
            "path": None,
            "location": None,
            "source_ref": "PL-D1",
        }
    ]
    manifest["validation"]["next_finding_number"] = 2
    manifest["delivery"] = {
        "action": "pending",
        "selected_by": None,
        "decision_ref": None,
        "preparation": [],
    }

    result = _run(_write_feature(tmp_path, manifest))

    assert result.returncode == 1
    assert "next_finding_number" in result.stdout
    assert "VF-2" in result.stdout


def test_death__finding_number_cannot_reset_after_findings_clear(
    tmp_path: Path,
) -> None:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "config", "user.email", "validator@example.com"],
        cwd=tmp_path,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Validator Test"],
        cwd=tmp_path,
        check=True,
    )
    (tmp_path / "README.md").write_text("fixture\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "commit", "-q", "-m", "fixture base"], cwd=tmp_path, check=True
    )
    base = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()

    manifest = _valid_manifest()
    manifest["snapshot"] = {"base_commit": base, "candidate_commit": base}
    manifest["validation"]["security_privacy"]["scope_ref"] = f"{base}...{base}"
    manifest["validation"]["next_finding_number"] = 5
    feature = _write_feature(tmp_path, manifest)
    (feature / "index.yaml").write_text(
        yaml.safe_dump(
            {
                "iteration_entry": {
                    "status": "ready_for_validation",
                    "last_commit": base,
                }
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    subprocess.run(["git", "add", "feature"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "commit", "-q", "-m", "preserve finding sequence"],
        cwd=tmp_path,
        check=True,
    )

    manifest["validation"]["next_finding_number"] = 1
    (feature / "ship-manifest.yaml").write_text(
        yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8"
    )

    result = _run(feature, tmp_path)

    assert result.returncode == 1
    assert "must not decrease" in result.stdout
    assert "5" in result.stdout and "1" in result.stdout
