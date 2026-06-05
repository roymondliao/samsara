"""Workflow invariants for the implement orchestration skill."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "skills" / "implement" / "SKILL.md"


def read_skill() -> str:
    return SKILL.read_text(encoding="utf-8")


def test_process_graph_routes_contract_gate_between_death_and_unit_tests():
    text = read_skill()
    assert "death_test -> contract_gate" in text, (
        "workflow graph must route death tests into the Test Contract Gate"
    )
    assert "contract_gate -> unit_test" in text, (
        "workflow graph must route the Test Contract Gate into unit tests"
    )


def test_contract_reference_is_registered_as_support_file():
    assert "references/test-contract.md" in read_skill()
