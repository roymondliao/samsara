"""Contracts for Implement execution-mode consistency and safe parallel waves."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
IMPLEMENT = ROOT / "skills" / "implement" / "SKILL.md"


def test_mode_a_is_guarded_not_forbidden() -> None:
    skill = IMPLEMENT.read_text(encoding="utf-8")
    normalized = " ".join(skill.split()).lower()

    assert "(a) subagent parallel" in normalized
    assert "dag-ready" in normalized
    assert "declared write scopes" in normalized
    assert "shared mutation surface" in normalized
    assert "unfinished task" in normalized
    assert (
        "dispatch multiple implementer subagents in parallel (file conflicts)"
        not in normalized
    )
    assert "never dispatch a parallel wave without proving" in normalized


def test_parallel_does_not_change_commit_granularity() -> None:
    skill = IMPLEMENT.read_text(encoding="utf-8")
    normalized = " ".join(skill.split())

    assert "Do not commit per-task" in normalized
    assert "Commit once after all tasks complete" in normalized
    assert "initial task execution only" in normalized
    assert "Iteration Fix Re-entry" in skill
    assert "per-fix commit" in normalized
