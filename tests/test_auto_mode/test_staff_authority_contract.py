"""Death tests for Auto mode's Staff-level decision authority."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT / "references" / "auto-mode.md"
GATEKEEPER = ROOT / "agents" / "auto-gatekeeper.md"
RESEARCH = ROOT / "skills" / "research" / "SKILL.md"
CODEBASE_MAP = ROOT / "skills" / "codebase-map" / "SKILL.md"
IMPLEMENT = ROOT / "skills" / "implement" / "SKILL.md"
PRE_THINKING = ROOT / "skills" / "pre-thinking" / "SKILL.md"
PLANNING = ROOT / "skills" / "planning" / "SKILL.md"
ITERATION = ROOT / "skills" / "iteration" / "SKILL.md"
VALIDATE = ROOT / "skills" / "validate-and-ship" / "SKILL.md"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_gatekeeper_is_symmetric_workflow_arbiter_not_external_authority() -> None:
    reference = " ".join(read(REFERENCE).lower().split())

    assert "symmetric workflow arbiter" in reference
    assert "external execution authority" in reference
    assert "human consent" in reference
    assert "does not" in reference


def test_gatekeeper_keeps_write_edit_but_only_for_decision_log_and_candidate() -> None:
    gatekeeper = read(GATEKEEPER)
    normalized = " ".join(gatekeeper.split())
    frontmatter = gatekeeper.split("---", 2)[1]

    assert "  - Write" in frontmatter
    assert "  - Edit" in frontmatter
    assert "sole writer" in gatekeeper.lower()
    assert "auto-decisions.md" in gatekeeper
    assert "/tmp" in gatekeeper
    assert "Do not edit code, tests, or stage artifacts" in normalized


def test_gatekeeper_uses_map_for_breadth_and_live_code_for_truth() -> None:
    gatekeeper = read(GATEKEEPER).lower()

    assert "codebase-map" in gatekeeper
    assert "broad structural awareness" in gatekeeper
    assert "live code" in gatekeeper
    assert "live code wins" in gatekeeper
    assert "targeted" in gatekeeper


def test_research_routes_all_four_human_prompts_through_auto_gatekeeper() -> None:
    research = read(RESEARCH)

    for gate_id in (
        "research.problem-source",
        "research.do-not-solve",
        "research.damage-recipient",
        "research.done-state",
        "research.transition",
    ):
        assert gate_id in research
    assert "each Step 1 prompt" in research
    assert "samsara:auto-gatekeeper" in research


def test_codebase_map_has_human_and_auto_review_paths() -> None:
    codebase_map = read(CODEBASE_MAP)

    assert "codebase-map.update-strategy" in codebase_map
    assert "codebase-map.review" in codebase_map
    assert "`Execution mode: auto`" in codebase_map
    assert "samsara:auto-gatekeeper" in codebase_map


def test_implement_separates_execution_mode_from_execution_strategy() -> None:
    implement = read(IMPLEMENT)

    assert "## Execution Strategy Selection" in implement
    assert "implementation.strategy" in implement
    assert "implementation execution-mode selection" not in implement


def test_stage_projections_use_the_canonical_stable_gate_ids() -> None:
    stage_ids = {
        RESEARCH: (
            "research.problem-source",
            "research.do-not-solve",
            "research.damage-recipient",
            "research.done-state",
            "research.transition",
        ),
        CODEBASE_MAP: ("codebase-map.update-strategy", "codebase-map.review"),
        PRE_THINKING: (
            "pre-thinking.step5.<group>.<question>",
            "pre-thinking.evaluator",
            "pre-thinking.commitment",
        ),
        PLANNING: ("planning.transition",),
        IMPLEMENT: (
            "implementation.strategy",
            "implementation.review-arbitration.<task>.<round>",
        ),
        ITERATION: (
            "iteration.entry-unknown",
            "iteration.disposition.<scar-id>",
            "iteration.blocked-fix.<scar-id>",
            "iteration.round.<n>",
        ),
        VALIDATE: (
            "validation.empty-diff",
            "validation.base-branch",
            "validation.security-capability",
            "validation.security-result",
            "validation.security-risk",
            "validation.delivery",
        ),
    }
    canonical = read(REFERENCE)

    for path, gate_ids in stage_ids.items():
        projection = read(path)
        for gate_id in gate_ids:
            assert gate_id in canonical
            assert gate_id in projection
