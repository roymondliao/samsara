"""Authority and reference contracts for Planning artifacts."""

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
PLANNING = ROOT / "skills" / "planning"
PRE_THINKING_TEMPLATE = (
    ROOT / "skills" / "pre-thinking" / "templates" / "pre-thinking.md"
)
SKILL = PLANNING / "SKILL.md"
FLOW = PLANNING / "flow.md"
PLAN = PLANNING / "templates" / "plan.md"
OVERVIEW = PLANNING / "templates" / "overview.md"
INDEX = PLANNING / "templates" / "index.yaml"
ACCEPTANCE = PLANNING / "templates" / "acceptance.yaml"
TASK = PLANNING / "task-format.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_death__planning_has_one_executable_owner() -> None:
    skill = _read(SKILL)

    assert FLOW.is_file()
    assert "`flow.md` is the sole owner of executable procedure" in skill
    assert "If this summary conflicts with `flow.md`, `flow.md` wins." in skill
    assert len(skill.split("---", 2)[-1].split()) < 500


def test_death__pre_thinking_exposes_stable_planning_references() -> None:
    template = _read(PRE_THINKING_TEMPLATE)

    assert "**Decision ID:** <PT-D1>" in template
    assert "**Decision ID:** <PT-S1>" in template
    assert "**Decision ID:** PT-CI" in template
    assert "**Contract ID:** PT-EVAL" in template


def test_death__planning_artifacts_name_authority_and_projection_roles() -> None:
    plan = _read(PLAN)
    overview = _read(OVERVIEW)

    assert "Planning judgment owner" in plan
    assert "Source refs:" in plan
    assert "Derived implementation projection" in overview
    assert "Do not add or revise decisions here" in overview
    assert "source_ref:" in overview
    assert "single source of seam declarations" not in overview.lower()
    assert "## Death Cases Summary" not in overview
    assert "## File Map" not in overview


def test_death__index_is_a_reference_graph_not_a_prose_copy() -> None:
    index = _read(INDEX)

    for field in (
        "sources:",
        "task_file:",
        "planning_refs:",
        "decision_refs:",
        "acceptance_refs:",
    ):
        assert field in index


def test_death__task_is_work_order_not_implement_workflow() -> None:
    task = _read(TASK)

    for heading in (
        "## Goal",
        "## Source References",
        "## Constraints",
        "## Assumptions to Verify",
    ):
        assert heading in task

    for forbidden in (
        "## Implementation Steps",
        "## Expected Scar Report Items",
        "Write scar report",
        "Report back (do not commit)",
    ):
        assert forbidden not in task


def test_death__acceptance_requires_evidence_not_default_verification() -> None:
    acceptance = _read(ACCEPTANCE)

    assert "source_refs:" in acceptance
    assert "not_applicable:" in acceptance
    assert "coverage_type: verified" not in acceptance


def test_death__yaml_templates_parse_without_forcing_optional_entries() -> None:
    index = yaml.safe_load(_read(INDEX))
    acceptance = yaml.safe_load(_read(ACCEPTANCE))

    assert index["tasks"][0]["anchors"] == []
    assert acceptance["not_applicable"] == []
