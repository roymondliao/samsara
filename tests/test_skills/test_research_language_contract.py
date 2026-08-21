"""Language-contract tests for the Research skill."""

import re

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RESEARCH = ROOT / "skills" / "research"
RESEARCH_SKILL = RESEARCH / "SKILL.md"
KICKOFF = RESEARCH / "templates" / "kickoff.md"
CJK = re.compile(r"[\u3400-\u9fff]")


def test_death__research_separates_executable_language_from_prompts() -> None:
    """Chinese is isolated to quoted philosophy and user-facing prompts."""
    violations: list[str] = []

    for path in RESEARCH.rglob("*.md"):
        for line_number, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            if CJK.search(line) and not line.lstrip().startswith(">"):
                violations.append(f"{path.relative_to(ROOT)}:{line_number}: {line}")

    assert violations == []


def test_death__research_separates_instruction_and_artifact_languages() -> None:
    """English instructions must not force English artifact prose."""
    skill = RESEARCH_SKILL.read_text(encoding="utf-8")
    kickoff = KICKOFF.read_text(encoding="utf-8")

    assert "Write artifact prose in the user's language." in skill
    assert "Keep template headings and schema keys in English." in skill
    assert not CJK.search(kickoff)


def test_death__research_translation_preserves_semantic_constraints() -> None:
    """English instructions retain the scope and force of the Chinese source."""
    skill = RESEARCH_SKILL.read_text(encoding="utf-8")
    normalized = re.sub(r"\s+", " ", skill)

    for constraint in (
        "Who could be harmed?",
        "Every difference is the first layer of translation loss.",
        "Every solution transfers cost.",
        "Strip all implementation shape",
        "what the code must essentially be to serve it",
        "below which",
        "The goal of subtraction is not fewer features",
        "real seams from someone else's territory",
        "use the same transition prompt to determine the next step",
    ):
        assert constraint in normalized, f"translated constraint missing: {constraint}"
