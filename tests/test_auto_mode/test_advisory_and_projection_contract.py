"""Death contracts for Gatekeeper advice and workflow-owned projections."""

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
GATEKEEPER = ROOT / "agents" / "auto-gatekeeper.md"
LEVEL_ANALYSIS = ROOT / "skills" / "level-analysis" / "SKILL.md"
RESEARCH = ROOT / "skills" / "research" / "SKILL.md"
AUTOPSY = ROOT / "skills" / "research" / "templates" / "problem-autopsy.md"
README = ROOT / "README.md"
README_ZH = ROOT / "README.zh-TW.md"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_death__level_analysis_is_advice_not_gate_authority() -> None:
    gatekeeper = read(GATEKEEPER)
    analysis = read(LEVEL_ANALYSIS)

    assert "invoke `samsara:level-analysis`" in gatekeeper
    assert "comparable options" in gatekeeper
    assert "advisory" in gatekeeper.lower()
    assert "final decision" in gatekeeper.lower()

    assert "advisory" in analysis.lower()
    assert "does not choose a gate decision" in analysis
    assert "evidence | assumption | unknown" in analysis
    assert "No evidence" in analysis
    assert "unsupported timeline" in analysis


def test_death__level_analysis_preserves_domain_and_level_guidance() -> None:
    analysis = read(LEVEL_ANALYSIS)

    for domain in (
        "Software Development",
        "AI/ML/Deep Learning",
        "Infrastructure/Cloud/DevOps",
        "Data Engineering",
        "Security",
        "Product/System Design",
    ):
        assert domain in analysis
    for role in (
        "Software Engineer",
        "AI/ML Research Engineer",
        "DevOps/Platform Engineer",
        "Data Engineer / Data Architect",
        "Security Engineer",
        "Systems Architect",
    ):
        assert role in analysis

    for heading in (
        "Senior Level Perspective",
        "Staff Level Perspective",
        "Principal Level Perspective",
    ):
        assert heading in analysis
    for criterion in (
        "Technical Analysis",
        "Best Practices",
        "Immediate Concerns",
        "Systemic View",
        "Cross-Team Impact",
        "Technical Strategy",
        "Strategic Vision",
        "Industry Context",
        "Build vs Buy vs Partner",
    ):
        assert criterion in analysis


def test_death__level_analysis_frontmatter_matches_skill_contract() -> None:
    text = read(LEVEL_ANALYSIS)
    frontmatter = yaml.safe_load(text.split("---", 2)[1])

    assert set(frontmatter) == {"name", "description"}
    assert frontmatter["description"].startswith("Use when")


def test_death__level_analysis_is_visible_in_public_overviews() -> None:
    for overview in (read(README), read(README_ZH)):
        assert "`samsara:level-analysis`" in overview


def test_death__research_projects_decisions_without_copying_the_log() -> None:
    research = read(RESEARCH)
    autopsy = read(AUTOPSY)
    normalized = " ".join(research.split())

    assert "Gatekeeper writes only `auto-decisions.md`" in normalized
    assert "Research applies the returned conclusion" in normalized
    assert "does not copy `reason`, `uncertainty`, or decision metadata" in normalized
    assert "auto-decisions.md#decision-NNN" in research
    assert "## decision_refs" in autopsy
    for gate_id in (
        "research.problem-source",
        "research.do-not-solve",
        "research.damage-recipient",
        "research.done-state",
    ):
        assert gate_id in autopsy
