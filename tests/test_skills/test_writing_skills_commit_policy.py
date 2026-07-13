"""Contract for disclosing observable workflow behavior in commit history."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WRITING_SKILLS = ROOT / "skills" / "writing-skills" / "SKILL.md"


def test_death__behavior_changes_require_commit_body_disclosure() -> None:
    text = WRITING_SKILLS.read_text(encoding="utf-8")
    normalized = " ".join(text.split()).lower()

    assert "behavior change:" in normalized
    for token in ("route", "gate", "required field", "observable workflow behavior"):
        assert token in normalized
    assert "pure rewording" in normalized
