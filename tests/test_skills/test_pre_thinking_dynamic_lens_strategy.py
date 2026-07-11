"""Contracts for dynamic multi-lens strategy derivation."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "skills" / "pre-thinking" / "SKILL.md"
FLOW = ROOT / "skills" / "pre-thinking" / "flow.md"
TEMPLATE = ROOT / "skills" / "pre-thinking" / "templates" / "pre-thinking.md"


def _read(path: Path) -> str:
    return " ".join(path.read_text(encoding="utf-8").split())


def test_death__lens_strategy_is_dynamic_many_to_many() -> None:
    """Lens count emerges from assumptions and evidence surfaces, not a quota."""
    skill = _read(SKILL)
    flow = _read(FLOW)
    template = _read(TEMPLATE)
    combined = f"{skill} {flow} {template}"

    assert "dynamic multi-lens evidence strategy" in skill
    assert "Exact procedures and write formats: `flow.md`" in skill
    assert "decision-relevant, not-confident assumptions" in flow
    assert "distinct evidence surfaces" in flow
    assert "not a one-to-one mapping" in flow

    assert "not-confident-assumption count" not in combined
    assert "One lens may cover multiple assumptions" in flow
    assert "one assumption may require multiple lenses" in flow


def test_death__lens_rationale_is_recorded_before_dispatch() -> None:
    """Dynamic strategy choices must be inspectable before results are known."""
    flow = _read(FLOW)
    template = _read(TEMPLATE)

    assert "Before dispatch, record" in flow
    assert "**Assumptions covered:**" in template
    assert "**Evidence surface:**" in template
    assert "**Why this lens:**" in template
