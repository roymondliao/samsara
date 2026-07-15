"""Contract tests for non-overlapping Research artifact ownership."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RESEARCH_SKILL = ROOT / "skills" / "research" / "SKILL.md"
KICKOFF = ROOT / "skills" / "research" / "templates" / "kickoff.md"
AUTOPSY = ROOT / "skills" / "research" / "templates" / "problem-autopsy.md"
AUTOPSY_GUIDE = ROOT / "skills" / "research" / "problem-autopsy-guide.md"
AMBIGUOUS_GUIDE_NAME = ROOT / "skills" / "research" / "problem-autopsy.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _section(text: str, heading: str) -> str:
    """Return one Markdown section, excluding the next same-level heading."""
    start = text.index(f"## {heading}")
    end = text.find("\n## ", start + 1)
    return text[start:] if end == -1 else text[start:end]


def test_death__research_artifacts_have_non_overlapping_problem_ownership() -> None:
    """Kickoff references source analysis instead of rewriting it."""
    kickoff = _read(KICKOFF)
    autopsy = _read(AUTOPSY)

    assert "## Problem Source" in kickoff
    assert "`problem-autopsy.md`" in kickoff
    assert "## Problem Statement" not in kickoff
    assert "Damage recipients" not in kickoff

    for owned_section in (
        "## original_statement",
        "## reframed_statement",
        "## translation_delta",
        "## kill_conditions",
        "## damage_recipients",
    ):
        assert owned_section in autopsy


def test_death__research_instructions_name_each_artifact_owner() -> None:
    """Writers need one explicit source for source-analysis and handoff data."""
    skill = _read(RESEARCH_SKILL).lower()
    guide = _read(AUTOPSY_GUIDE).lower()

    assert "problem-autopsy.md owns" in skill
    assert "1-kickoff.md owns" in skill
    assert "do not restate" in skill
    assert "sole owner" in guide
    assert "1-kickoff.md" in guide and "must not duplicate" in guide


def test_death__research_guide_and_template_names_are_unambiguous() -> None:
    """Guide, source template, and generated artifact must not share a name."""
    skill = _read(RESEARCH_SKILL)

    assert AUTOPSY_GUIDE.is_file()
    assert AUTOPSY.is_file()
    assert not AMBIGUOUS_GUIDE_NAME.exists()
    assert "`problem-autopsy-guide.md`" in skill
    assert "`templates/problem-autopsy.md`" in skill


def test_death__research_writes_autopsy_before_kickoff() -> None:
    """A handoff must not be generated before the source artifact it cites."""
    skill = _read(RESEARCH_SKILL)

    assert "interrogate -> output_autopsy;" in skill
    assert "output_autopsy -> essence;" in skill
    assert "north_star -> output_kickoff;" in skill
    assert "output_kickoff -> gate;" in skill
    assert "output_kickoff -> output_autopsy;" not in skill

    output = _section(skill, "Output")
    assert output.index("**problem-autopsy.md**") < output.index("**1-kickoff.md**")


def test_death__problem_autopsy_records_missing_input_without_inference() -> None:
    """Required sections must expose evidence gaps instead of forcing claims."""
    guide = _read(AUTOPSY_GUIDE)
    autopsy = _read(AUTOPSY)
    marker = "Input incomplete; missing: <specific information or evidence>."

    assert "Address every section" in guide
    assert marker in guide
    assert "Do not infer" in guide
    assert "Each section must be filled" not in guide
    assert marker in autopsy
    assert "Do not invent" in autopsy


def test_death__kill_conditions_are_evidence_backed_not_quota_driven() -> None:
    """Kill-condition rigor comes from evidence, not a fixed item count."""
    skill = _read(RESEARCH_SKILL)
    guide = _read(AUTOPSY_GUIDE)
    autopsy_section = _section(_read(AUTOPSY), "kill_conditions")
    normalized_skill = " ".join(skill.split())
    normalized_guide = " ".join(guide.split())

    assert "at least two" not in f"{skill}\n{guide}".lower()
    assert "supported by the available evidence" in normalized_skill
    assert "supported by the available evidence" in normalized_guide
    assert "Do not invent" in normalized_skill and "satisfy a count" in normalized_skill
    assert "Do not invent" in normalized_guide and "satisfy a count" in normalized_guide
    assert guide.count('  - condition: "If') == 1
    assert autopsy_section.count('- condition: "<when to abandon this>"') == 1
    assert "independently supported conditions" in autopsy_section


def test_death__north_star_values_expose_unknowns_and_their_basis() -> None:
    """Metric placeholders must not force unsupported baselines or targets."""
    skill = _read(RESEARCH_SKILL)
    north_star = _section(_read(KICKOFF), "North Star")

    assert "Do not infer metric values." in skill
    assert "Use `unknown`" in skill
    assert "current: <value | unknown>" in north_star
    assert "target: <value | unknown>" in north_star
    assert north_star.count("current_basis:") == 2
    assert north_star.count("target_basis:") == 2
    assert north_star.count("<measurement source | missing input>") == 2
    assert north_star.count("<decision rationale | missing input>") == 2
    assert "current: <value>" not in north_star
    assert "target: <value>" not in north_star


def test_death__kickoff_has_one_scope_authority() -> None:
    """Must-solve and out-of-scope facts must not drift across two sections."""
    kickoff = _read(KICKOFF)

    assert kickoff.count("## Scope Contract") == 1
    assert "## Boundary Scope" not in kickoff
    assert "\n## Scope\n" not in kickoff
    for token in (
        "What must be solved",
        "Areas involved",
        "Must-Have",
        "Nice-to-Have",
        "Not solved now",
        "Death condition",
    ):
        assert token in kickoff


def test_death__north_star_is_not_the_execution_evaluator() -> None:
    """Research owns outcome direction; Pre-thinking owns executable evaluation."""
    kickoff = _section(_read(KICKOFF), "North Star")
    normalized = " ".join(kickoff.split()).lower()

    assert "product outcome" in normalized
    assert "not `pt-eval`" in normalized
    assert "pre-thinking" in normalized


def test_death__research_transition_prompt_has_one_owner() -> None:
    """Human and auto modes must reference one canonical transition prompt."""
    skill = _read(RESEARCH_SKILL)
    transition = _section(skill, "Transition")
    auto_gate = " ".join(_section(skill, "Auto Mode Gate").split())
    prompt = (
        "「Research 完成。1-kickoff.md 和 problem-autopsy.md 已寫入 "
        "`changes/<feature>/`。確認後進入 Pre-thinking？」"
    )

    assert skill.count(prompt) == 1
    assert prompt in transition
    assert "`workflow_prompt` sources and gate IDs" in auto_gate
    assert "`research.transition` uses the exact prompt in `## Transition`" in auto_gate
    assert "do not restate it here" in auto_gate
