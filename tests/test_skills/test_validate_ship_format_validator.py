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


def _run(feature: Path) -> subprocess.CompletedProcess[str]:
    assert VALIDATOR.is_file(), "Validate & Ship must own a format validator"
    return subprocess.run(
        [
            sys.executable,
            str(VALIDATOR),
            str(feature),
            "--repo-root",
            str(ROOT),
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
