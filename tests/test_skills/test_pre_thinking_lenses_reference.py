from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_pre_thinking_lenses_are_skill_local_reference():
    """Contract: lenses.md belongs to pre-thinking, its only live consumer."""
    root_reference = ROOT / "references" / "lenses.md"
    skill_reference = ROOT / "skills" / "pre-thinking" / "references" / "lenses.md"

    assert not root_reference.exists(), (
        "lenses.md has only the pre-thinking skill as a live consumer; keeping it "
        "in repo-root references/ makes it look shared."
    )
    assert skill_reference.exists(), (
        "pre-thinking's default lens list must live with the pre-thinking skill."
    )
    assert "## Default lenses" in skill_reference.read_text(encoding="utf-8")

    for relative_path in (
        "skills/pre-thinking/SKILL.md",
        "skills/pre-thinking/flow.md",
    ):
        content = (ROOT / relative_path).read_text(encoding="utf-8")
        assert "skill-local `references/lenses.md`" in content
