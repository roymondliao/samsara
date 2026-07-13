"""Contract tests for bootstrap routing scope and mode-selection order."""

import re

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BOOTSTRAP = ROOT / "skills" / "samsara-bootstrap" / "SKILL.md"
README = ROOT / "README.md"


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
    normalized = " ".join(prohibited.split())

    assert "no confirmation-bias implementation" in normalized
    assert "do not implement only the path that confirms the request" in normalized
    assert "when ___ does not hold, ___ happens" in normalized


def test_death__bootstrap_preserves_original_ambiguity_and_longevity_scope() -> None:
    text = BOOTSTRAP.read_text(encoding="utf-8")
    required = _section(text, "Required Agent Behavior").lower()
    step0 = _section(text, "STEP 0 — Prerequisites Before Implementation").lower()
    required = " ".join(required.split())
    step0 = " ".join(step0.split())

    assert "keep ambiguity visible" in required
    assert "consequential ambiguity" not in required
    assert "belongs only to the present moment" in step0
    assert "will no longer need to exist" in step0
    assert "lasting responsibility" not in step0


def test_death__bootstrap_has_explicit_human_mode_fallback() -> None:
    mode = _section(
        BOOTSTRAP.read_text(encoding="utf-8"), "Execution Mode Selection"
    ).lower()
    mode = " ".join(mode.split())

    assert "if the user does not choose" in mode
    assert "record `execution mode: human-in-the-loop` and proceed" in mode
    assert "unknown mode" in mode and "must never silently become `auto`" in mode


def test_death__production_failure_question_reaches_debugging() -> None:
    routing = _section(
        BOOTSTRAP.read_text(encoding="utf-8"), "Skill Matching (Mandatory)"
    )
    lower = routing.lower()
    rule2 = lower[
        lower.index("2. **non-workflow conversation") : lower.index(
            "3. **production failure"
        )
    ]
    rule2 = " ".join(rule2.split())

    assert "previously working behavior now failing" in rule2
    assert "production-failure report" in rule2
    assert 'label="production failure"' in lower
    assert 'label="system failure"' not in lower


def test_death__bootstrap_uses_one_ordered_routing_contract() -> None:
    """Ordered rules own behavior; the DOT graph is explicitly derived."""
    text = BOOTSTRAP.read_text(encoding="utf-8")
    routing = _section(text, "Skill Matching (Mandatory)")
    lower = routing.lower()

    assert "route requests in this order" in lower
    assert "stop at the first match" in lower
    ordered_markers = (
        "1. **explicit samsara skill command",
        "2. **non-workflow conversation",
        "3. **production failure",
        "4. **proven low-risk state-changing work",
        "5. **other state-changing feature work",
        "6. **unclear mutation authority",
    )
    positions = [lower.index(marker) for marker in ordered_markers]
    assert positions == sorted(positions)
    assert "### Derived Routing Graph" in routing
    assert "ordered rules above are canonical" in lower
    assert "do not infer conditions" in lower
    assert "```dot" in routing and "digraph samsara_routing" in routing
    assert not re.search(r"\bimplement\s*->\s*validate\b", routing)
    assert re.search(r"\bimplement\s*->\s*iteration\b", routing)
    assert re.search(r"\biteration\s*->\s*validate\b", routing)

    assert (
        "research -> pre-thinking -> planning -> implement -> iteration -> validate-and-ship"
        in lower
    )
    assert "every completed implement enters iteration" in lower
    assert "entry skills:" not in text.lower()
    assert "chain skills:" not in text.lower()


def test_death__readme_graph_is_a_derived_routing_overview() -> None:
    """Human visualization must identify its canonical executable source."""
    text = README.read_text(encoding="utf-8")
    workflow = _section(text, "Workflow")
    lower = workflow.lower()

    assert "derived overview" in lower
    assert "skills/samsara-bootstrap/skill.md" in lower
    assert "if this overview disagrees" in lower
    assert "read-only / explanation / meta-audit" in lower
    assert "research -> pre-thinking -> planning -> implement" in lower
