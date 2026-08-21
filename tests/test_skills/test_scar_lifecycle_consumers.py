"""Death contracts for live consumers of the scar lifecycle write contract."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
IMPLEMENTER = ROOT / "agents" / "implementer.md"
YIN_REVIEWER = ROOT / "agents" / "code-reviewer.md"


def _section(text: str, start: str, end: str) -> str:
    start_at = text.index(start)
    end_at = text.index(end, start_at)
    return text[start_at:end_at]


def test_death__level1_leaves_unresolved_items_open_for_iteration() -> None:
    text = IMPLEMENTER.read_text(encoding="utf-8")
    level1 = _section(text, "## Self-Iteration", "## Self-Review").lower()
    normalized = " ".join(level1.split())

    assert "deferred_to_feature_iteration" not in level1
    assert "accepted_because" not in level1
    assert "`status: open`" in level1
    assert "`iteration: null`" in level1
    assert "iteration owns" in normalized


def test_death__implementer_reports_resolved_and_open_counts_only() -> None:
    text = IMPLEMENTER.read_text(encoding="utf-8")
    report = _section(text, "## Report Format", "Use DONE_WITH_CONCERNS")
    lowered = report.lower()

    assert "items resolved / items open" in lowered
    assert "items deferred" not in lowered


def test_death__structural_refusal_uses_structural_decisions_carrier() -> None:
    text = IMPLEMENTER.read_text(encoding="utf-8")
    honesty = _section(
        text,
        "## Structural Honesty",
        "## Global Thinking Channel",
    ).lower()

    assert "`structural_decisions`" in honesty
    assert "`narrative` or report-back" not in honesty


def test_death__yin_reviewer_challenges_all_open_reports() -> None:
    text = YIN_REVIEWER.read_text(encoding="utf-8")
    integrity = _section(text, "### 6. Scar Report Integrity", "### 7.").lower()

    assert "every item" in integrity
    assert "`status: open`" in integrity
    assert "`status: resolved`" in integrity
    assert "task scope" in integrity
    assert "defensive narrative" in integrity
    assert "every item is deferred" not in integrity
