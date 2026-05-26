from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_template_does_not_predeclare_completion_sections() -> None:
    template = read("skills/pre-thinking/templates/pre-thinking.md")

    assert "## Step B" not in template
    assert "## Step C" not in template


def test_pre_thinking_requires_agent_evaluable_contract() -> None:
    skill = read("skills/pre-thinking/SKILL.md")
    flow = read("skills/pre-thinking/flow.md")
    combined = skill + "\n" + flow

    assert "agent-evaluable" in combined
    assert "Primary evaluator" in combined
    assert "Agent can perform it by" in combined
    assert "Pass signal" in combined
    assert "Fail signal" in combined
    assert "Feedback loop" in combined
    assert "Evaluation is never optional" in combined


def test_return_to_research_cannot_pass_planning_guard() -> None:
    planning = read("skills/planning/SKILL.md")

    assert "Decision: Proceed" in planning
    assert "Decision: Accept gap" in planning
    assert "Decision: Return to Research" in planning
    assert "do not proceed" in planning.lower()


def test_planning_consumes_design_and_evaluation_contract() -> None:
    planning = read("skills/planning/SKILL.md")

    assert "Pre-thinking Commitments Consumed" in planning
    assert "System design constraints" in planning
    assert "Primary evaluator" in planning
    assert "Feedback loop" in planning


def test_downstream_skills_use_primary_evaluator_as_feedback_source() -> None:
    for path in [
        "skills/validate-and-ship/SKILL.md",
        "skills/iteration/SKILL.md",
        "skills/debugging/SKILL.md",
    ]:
        content = read(path)
        assert "Primary evaluator" in content, path
        assert "Feedback loop" in content, path


def test_fixture_chain_routes_research_to_pre_thinking() -> None:
    research = read("tests/fixtures/source/skills/research/SKILL.md")

    assert "samsara:pre-thinking" in research
    assert "samsara:planning" not in research


def test_fixture_contains_pre_thinking_skill() -> None:
    assert (ROOT / "tests/fixtures/source/skills/pre-thinking/SKILL.md").exists()
