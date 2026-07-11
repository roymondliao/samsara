"""Contract tests for bootstrap routing scope and mode-selection order."""

import re

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BOOTSTRAP = ROOT / "skills" / "samsara-bootstrap" / "SKILL.md"


def _section(text: str, heading: str) -> str:
    start = text.index(f"## {heading}")
    rest = text[start:]
    end = rest.find("\n## ", len(f"## {heading}"))
    return rest if end == -1 else rest[:end]


def test_death__bootstrap_does_not_route_every_conversation_into_workflow() -> None:
    """Read-only and meta requests must not trigger workflow by possibility."""
    text = BOOTSTRAP.read_text(encoding="utf-8")
    matching = _section(text, "Skill Matching (Mandatory)").lower()

    assert "before any response" not in matching
    assert "1% chance" not in matching
    assert "read-only" in matching and "meta-audit" in matching
    assert re.search(r"handle directly;\s+do not\s+invoke", matching)


def test_death__bootstrap_selects_mode_before_first_research_invocation() -> None:
    """Research entry has one order and reuses an existing session mode."""
    text = BOOTSTRAP.read_text(encoding="utf-8")
    mode = _section(text, "Execution Mode Selection").lower()
    matching = _section(text, "Skill Matching (Mandatory)").lower()

    assert "before invoking `samsara:research`" in mode
    assert "already records `execution mode:`" in mode
    assert "do not ask again" in mode
    assert "select execution mode first" in matching


def test_death__bootstrap_separates_executable_language_from_philosophy() -> None:
    """Executable rules use English; Chinese remains only in the core axiom."""
    text = BOOTSTRAP.read_text(encoding="utf-8")
    cjk_lines = {
        line.strip()
        for line in text.splitlines()
        if re.search(r"[\u3400-\u9fff]", line)
    }

    assert cjk_lines == {
        "# Samsara — 向死而驗",
        "**存在即責任，無責任即無存在。**",
    }
    assert "## Language Contract" in text
    assert "Executable instructions use English" in text
    assert "Do not duplicate a rule in multiple languages" in text


def test_death__bootstrap_preserves_confirmation_bias_prohibition() -> None:
    """Translation must retain both the prohibition and its failure branch."""
    text = BOOTSTRAP.read_text(encoding="utf-8")
    prohibited = _section(text, "Prohibited Agent Behavior").lower()

    assert "no confirmation-bias implementation" in prohibited
    assert "do not implement only the path that confirms the request" in prohibited
    assert "when its premise does not hold" in prohibited
