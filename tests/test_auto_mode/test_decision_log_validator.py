"""Behavior tests for the compact append-only Auto decision log."""

from __future__ import annotations

import subprocess
import textwrap
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = (
    ROOT / "agents" / "auto-gatekeeper" / "scripts" / "validate_auto_decisions.py"
)


def entry(
    number: int = 1,
    *,
    gate_id: str = "research.problem-source",
    stage: str = "research",
    workflow_prompt: str = "Who shaped this problem?",
    answer: str = "The request and repository evidence shaped it.",
    decision: str = "proceed",
    action_type: str = "continue",
    gap: str = "null",
    supersedes: str = "null",
) -> str:
    decision_id = f"decision-{number:03d}"
    return textwrap.dedent(
        f"""\
        ## {decision_id} — {gate_id}

        ```yaml
        schema_version: 1
        decision_id: {decision_id}
        timestamp: "2026-07-15T12:00:00+08:00"
        decided_by: auto-gatekeeper
        stage: {stage}
        gate_id: {gate_id}
        workflow_prompt: "{workflow_prompt}"
        answer: "{answer}"
        decision: {decision}
        reason:
          - "The original request is explicit."
        evidence_refs:
          - "references/auto-mode.md#Stage Gate Protocol"
        uncertainty:
          level: low
          notes: none
        next_action:
          type: {action_type}
          target: "continue research"
        gap: {gap}
        supersedes: {supersedes}
        ```
        """
    )


def run_validator(feature_dir: Path, *extra: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            "uv",
            "run",
            "python",
            str(VALIDATOR),
            str(feature_dir),
            "--repo-root",
            str(ROOT),
            *extra,
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_compact_valid_log_passes(tmp_path: Path) -> None:
    feature = tmp_path / "feature"
    feature.mkdir()
    (feature / "auto-decisions.md").write_text(entry(), encoding="utf-8")

    result = run_validator(feature)

    assert result.returncode == 0, result.stdout + result.stderr


def test_append_candidate_validates_and_writes_once(tmp_path: Path) -> None:
    feature = tmp_path / "feature"
    feature.mkdir()
    log = feature / "auto-decisions.md"
    original = entry()
    log.write_text(original, encoding="utf-8")
    candidate = tmp_path / "candidate.md"
    candidate.write_text(
        entry(
            2,
            decision="revise",
            action_type="revise_and_rerun",
            supersedes="decision-001",
        ),
        encoding="utf-8",
    )

    result = run_validator(feature, "--append-candidate", str(candidate))

    assert result.returncode == 0, result.stdout + result.stderr
    updated = log.read_text(encoding="utf-8")
    assert updated.startswith(original)
    assert "decision-002" in updated
    assert "APPENDED" in result.stdout


def test_invalid_candidate_does_not_mutate_log(tmp_path: Path) -> None:
    feature = tmp_path / "feature"
    feature.mkdir()
    log = feature / "auto-decisions.md"
    original = entry()
    log.write_text(original, encoding="utf-8")
    candidate = tmp_path / "candidate.md"
    candidate.write_text(entry(), encoding="utf-8")

    result = run_validator(feature, "--append-candidate", str(candidate))

    assert result.returncode == 1
    assert log.read_text(encoding="utf-8") == original


def test_active_append_lock_fails_without_mutation(tmp_path: Path) -> None:
    feature = tmp_path / "feature"
    feature.mkdir()
    log = feature / "auto-decisions.md"
    original = entry()
    log.write_text(original, encoding="utf-8")
    (feature / ".auto-decisions.lock").write_text("another writer", encoding="utf-8")
    candidate = tmp_path / "candidate.md"
    candidate.write_text(
        entry(
            2,
            decision="revise",
            action_type="revise_and_rerun",
            supersedes="decision-001",
        ),
        encoding="utf-8",
    )

    result = run_validator(feature, "--append-candidate", str(candidate))

    assert result.returncode == 2
    assert "lock" in result.stdout.lower()
    assert log.read_text(encoding="utf-8") == original


def test_duplicate_id_and_heading_mismatch_fail(tmp_path: Path) -> None:
    feature = tmp_path / "feature"
    feature.mkdir()
    malformed = entry() + entry().replace("## decision-001", "## decision-002", 1)
    (feature / "auto-decisions.md").write_text(malformed, encoding="utf-8")

    result = run_validator(feature)

    assert result.returncode == 1
    assert "decision-id" in result.stdout.lower()


def test_accept_gap_requires_durable_gap(tmp_path: Path) -> None:
    feature = tmp_path / "feature"
    feature.mkdir()
    (feature / "auto-decisions.md").write_text(
        entry(decision="accept_gap", action_type="continue"),
        encoding="utf-8",
    )

    result = run_validator(feature)

    assert result.returncode == 1
    assert "accept-gap" in result.stdout.lower()


def test_reject_requires_stop_action(tmp_path: Path) -> None:
    feature = tmp_path / "feature"
    feature.mkdir()
    (feature / "auto-decisions.md").write_text(
        entry(decision="reject", action_type="continue"), encoding="utf-8"
    )

    result = run_validator(feature)

    assert result.returncode == 1
    assert "decision-action" in result.stdout.lower()


def test_validator_does_not_depend_on_ship_manifest(tmp_path: Path) -> None:
    source = VALIDATOR.read_text(encoding="utf-8")

    assert "ship-manifest.yaml" not in source
    assert "delivery.action" not in source
