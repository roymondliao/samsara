from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SKILLS_DIR = ROOT / "skills"

BOOTSTRAP = SKILLS_DIR / "samsara-bootstrap" / "SKILL.md"
EARLY_STAGE_SKILLS = {
    "research": SKILLS_DIR / "research" / "SKILL.md",
    "pre-thinking": SKILLS_DIR / "pre-thinking" / "SKILL.md",
    "planning": SKILLS_DIR / "planning" / "SKILL.md",
}

LATER_STAGE_SKILLS = {
    "implement": SKILLS_DIR / "implement" / "SKILL.md",
    "iteration": SKILLS_DIR / "iteration" / "SKILL.md",
    "security-privacy-review": SKILLS_DIR / "security-privacy-review" / "SKILL.md",
    "validate-and-ship": SKILLS_DIR / "validate-and-ship" / "SKILL.md",
}

ALL_WORKFLOW_SKILLS = {
    **EARLY_STAGE_SKILLS,
    **LATER_STAGE_SKILLS,
}

REQUIRED_WORKFLOW_STAGES = {
    "research",
    "pre-thinking",
    "planning",
    "implement",
    "iteration",
    "security-privacy-review",
    "validate-and-ship",
}


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def section(text: str, heading: str) -> str:
    marker = f"## {heading}"
    assert marker in text, f"Missing required section: {marker}"
    tail = text.split(marker, 1)[1]
    return tail.split("\n## ", 1)[0]
