"""Boundary tests for Pre-thinking consumption of Codebase Map state."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FLOW = ROOT / "skills" / "pre-thinking" / "flow.md"
MAP_SKILL = ROOT / "skills" / "codebase-map" / "SKILL.md"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def normalized(path: Path) -> str:
    return " ".join(read(path).split())


def test_pre_thinking_refreshes_on_sha_mismatch_without_a_feature_gate() -> None:
    flow = normalized(FLOW)

    assert "source.commit" in flow
    assert "committed Git `HEAD`" in flow
    assert "If `UPDATE_REQUIRED`, **auto-initiate** `samsara:codebase-map`" in flow
    assert "do not add a feature execution-mode gate" in flow
    assert "churn" not in flow.lower()
    assert "staleness_churn_threshold" not in flow


def test_failed_refresh_keeps_old_snapshot_identity_and_visible_gap() -> None:
    flow = normalized(FLOW)

    assert "If regeneration fails or aborts" in flow
    assert "do not claim completion" in flow
    assert "old map identified by its source commit" in flow
    assert "information gap" in flow
    assert "committed `HEAD`" in flow


def test_missing_or_unknown_map_requires_targeted_evidence_not_memory() -> None:
    flow = normalized(FLOW)

    assert "If `MISSING` or `UNKNOWN`" in flow
    assert "do not invent a map from memory" in flow
    assert "inspect affected files" in flow


def test_map_never_claims_authority_over_working_feature_changes() -> None:
    flow = normalized(FLOW)
    skill = normalized(MAP_SKILL)

    assert "The map describes committed code only" in flow
    assert "current working changes own the proposed feature" in flow
    assert "Never read or persist uncommitted" in skill
    assert "Feature workflows inspect their own working changes" in skill


def test_codebase_map_failure_does_not_advance_source_commit() -> None:
    skill = normalized(MAP_SKILL)

    assert "do not advance `source.commit`" in skill
    assert "Preserve the previous root manifest" in skill
