"""Planning invariants for contract-bound unit tests."""

from __future__ import annotations

import ast
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EVALUATOR_SOURCE = (
    ROOT / "tests" / "test_contract_bound_tests" / "test_planning_test_contract.py"
)
TASK_FORMAT = ROOT / "skills" / "planning" / "task-format.md"
PLANNING_SKILL = ROOT / "skills" / "planning" / "SKILL.md"
HISTORICAL_TASK_WITHOUT_SECTION = (
    ROOT / "changes" / "2026-04-21_security-privacy-review" / "tasks" / "task-1.md"
)


def read_task_format() -> str:
    return TASK_FORMAT.read_text(encoding="utf-8")


def read_planning_skill() -> str:
    return PLANNING_SKILL.read_text(encoding="utf-8")


def test_task_template_requires_unit_test_contract_source():
    text = read_task_format()
    assert "unit test contract" in text.lower()
    assert re.search(
        r"unit test contract[^.\n]{0,160}(must|required|observable|contract source)",
        text,
        re.IGNORECASE,
    ), "task template must require an observable unit-test contract source"


def test_planning_skill_names_contract_source_during_decomposition():
    text = read_planning_skill()
    assert re.search(
        r"unit[- ]test contract source|contract is named upstream|name each task",
        text,
        re.IGNORECASE,
    ), "planning decomposition must name the unit-test contract source"


def test_planning_evaluator_does_not_walk_historical_change_tasks():
    source = EVALUATOR_SOURCE.read_text(encoding="utf-8")
    tree = ast.parse(source)
    forbidden_calls: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            attr = node.func.attr
            if attr in {"glob", "rglob", "iterdir", "scandir"}:
                forbidden_calls.append(f".{attr}(")
            if isinstance(node.func.value, ast.Name):
                base = node.func.value.id
                if base == "os" and attr in {"walk", "listdir", "scandir"}:
                    forbidden_calls.append(f"os.{attr}(")
                if base == "glob" and attr == "glob":
                    forbidden_calls.append("glob.glob(")
    assert not forbidden_calls, (
        "planning evaluator must read named template files only, not walk changes/: "
        f"{sorted(set(forbidden_calls))}"
    )


def test_known_historical_task_can_lack_unit_test_contract_section():
    historical = HISTORICAL_TASK_WITHOUT_SECTION.read_text(encoding="utf-8")
    assert "death test" in historical.lower()
    assert "unit test contract" not in historical.lower()
