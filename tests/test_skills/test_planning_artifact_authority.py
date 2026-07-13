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
TEST_CONTRACT = ROOT / "references" / "test-contract.md"


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


def test_death__planning_resolves_l1_refs_from_pre_thinking() -> None:
    """Refs-only handoff is safe only when Planning resolves the original entries."""
    flow = " ".join(_read(FLOW).split()).lower()

    assert "read the complete `pre-thinking.md`" in flow
    assert "resolve every l1 ref" in flow
    assert "exactly one `pt-ci`" in flow
    assert "every cited `pt-s*`" in flow


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


def test_death__planning_ids_have_stable_human_labels() -> None:
    flow = " ".join(_read(FLOW).replace("`", "").split())
    plan = _read(PLAN)
    task = _read(TASK)
    acceptance = yaml.safe_load(_read(ACCEPTANCE))

    assert "PL-D* (Planning Decision)" in flow
    assert "AC-* (Acceptance Contract Scenario)" in flow
    assert "ID (ID (canonical label))" in flow

    for artifact in (plan, task):
        assert "PL-D1 (<canonical planning label>)" in artifact
        assert "PT-D1 (<canonical decision label>)" in artifact
        assert "AC-1 (<canonical scenario label>)" in artifact

    assert acceptance["scenarios"][0]["label"] == "<semantic label>"


def test_death__machine_reference_arrays_remain_pure_ids() -> None:
    index = yaml.safe_load(_read(INDEX))
    acceptance = yaml.safe_load(_read(ACCEPTANCE))
    task = index["tasks"][0]

    assert task["planning_refs"] == ["PL-D1"]
    assert task["decision_refs"] == ["PT-D1", "PT-S1"]
    assert task["acceptance_refs"] == ["AC-1"]
    assert acceptance["evaluator_ref"] == "PT-EVAL"
    assert acceptance["scenarios"][0]["source_refs"] == ["PT-D1"]


def test_death__death_case_ids_are_explicitly_file_scoped() -> None:
    contract = " ".join(_read(TEST_CONTRACT).split())

    assert "`DC-*` (Death Case)" in contract
    assert "not an authority-graph key" in contract
    assert "never renumber or reuse" in contract
