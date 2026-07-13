"""Death contracts for Iteration-owned semantic entry triage."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
IMPLEMENT = ROOT / "skills" / "implement" / "SKILL.md"
ITERATION = ROOT / "skills" / "iteration" / "flow.md"
INDEX_TEMPLATE = ROOT / "skills" / "planning" / "templates" / "index.yaml"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def section(text: str, heading: str) -> str:
    start = text.index(heading)
    rest = text[start + len(heading) :]
    end = rest.find("\n## ")
    return rest if end == -1 else rest[:end]


def test_iteration_is_the_only_entry_triage_owner() -> None:
    implement_transition = section(read(IMPLEMENT), "## Transition")
    iteration = read(ITERATION)

    assert "samsara:iteration" in implement_transition
    assert "Entry Triage" in implement_transition
    assert "signal_lost >= 5" not in implement_transition
    assert "cross-task pattern" not in implement_transition
    assert "## Entry Triage" in iteration
    assert "sole owner" in section(iteration, "## Entry Triage").lower()


def test_entry_triage_is_cheap_and_rounds_are_conditional() -> None:
    entry = " ".join(section(read(ITERATION), "## Entry Triage").split()).lower()

    assert "every completed implementation" in entry
    assert "triage-only" in entry
    assert "does not start fix rounds" in entry
    assert "skip_rounds" in entry
    assert "fix_rounds" in entry


def test_signal_lost_is_observation_not_eligibility_gate() -> None:
    iteration = read(ITERATION)
    entry = " ".join(section(iteration, "## Entry Triage").split()).lower()

    assert "signal_lost >= 5" not in f"{iteration}\n{read(IMPLEMENT)}"
    assert "never decides whether an item deserves repair" in entry
    for purpose in ("describe", "prioritize", "compare", "stagnation"):
        assert purpose in entry


def test_semantic_cross_task_classification_is_not_literal_only() -> None:
    entry = " ".join(section(read(ITERATION), "## Entry Triage").split()).lower()

    assert "same underlying cause" in entry
    assert "shared boundary" in entry
    assert "wording differs" in entry
    assert "literal comparison" not in entry


def test_unknown_never_silently_skips() -> None:
    entry = " ".join(section(read(ITERATION), "## Entry Triage").split()).lower()

    assert "unknown" in entry
    assert "never skip" in entry
    assert "parse" in entry and "evaluator" in entry
    assert "human" in entry and "auto-gatekeeper" in entry


def test_every_triage_outcome_leaves_a_reversible_durable_record() -> None:
    entry = " ".join(section(read(ITERATION), "## Entry Triage").split()).lower()
    index = read(INDEX_TEMPLATE)

    for token in (
        "status: in_progress",
        "route",
        "round",
        "signal_lost",
        "evaluator",
        "reason",
        "reversible",
    ):
        assert token in entry
    assert "index.yaml" in entry
    assert "iteration_entry:" in index


def test_skip_rounds_requires_evaluator_pass_and_no_actionable_items() -> None:
    entry = " ".join(section(read(ITERATION), "## Entry Triage").split()).lower()

    assert "primary evaluator" in entry and "passes" in entry
    assert "no actionable" in entry and "remains" in entry
    assert "re_review_signal" in entry and "owner" in entry


def test_implement_auto_gate_no_longer_owns_iteration_entry() -> None:
    auto = section(read(IMPLEMENT), "## Auto Mode Gate")

    assert "implementation execution-mode selection" in auto
    assert "implementation completion gate" not in auto
    assert "iteration-entry criteria" not in auto
