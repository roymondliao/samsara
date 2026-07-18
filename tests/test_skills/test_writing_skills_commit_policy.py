"""Contract for disclosing observable workflow behavior in commit history."""

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
WRITING_SKILLS = ROOT / "skills" / "writing-skills" / "SKILL.md"
GRAPHVIZ_CONVENTIONS = ROOT / "skills" / "writing-skills" / "graphviz-conventions.dot"


def test_unit__frontmatter_is_trigger_only() -> None:
    text = WRITING_SKILLS.read_text(encoding="utf-8")
    frontmatter = yaml.safe_load(text.split("---", 2)[1])
    description = frontmatter["description"]

    assert set(frontmatter) == {"name", "description"}
    assert description.startswith("Use when")
    assert "TDD" not in description
    assert "death-first" not in description.lower()


def test_unit__optional_graph_reference_resolves() -> None:
    text = WRITING_SKILLS.read_text(encoding="utf-8")

    assert GRAPHVIZ_CONVENTIONS.name in text
    assert GRAPHVIZ_CONVENTIONS.is_file()


def test_death__behavior_changes_require_commit_body_disclosure() -> None:
    text = WRITING_SKILLS.read_text(encoding="utf-8")
    normalized = " ".join(text.split()).lower()

    assert "behavior change:" in normalized
    for token in ("route", "gate", "required field", "observable workflow behavior"):
        assert token in normalized
    assert "pure rewording" in normalized
