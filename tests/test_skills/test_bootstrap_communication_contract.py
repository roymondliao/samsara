"""Semantic guards for Bootstrap-owned user-facing communication."""

from pathlib import Path

from samsara_cli.converter.engine import ConversionEngine


ROOT = Path(__file__).resolve().parents[2]
BOOTSTRAP = ROOT / "skills" / "samsara-bootstrap" / "SKILL.md"
HEADING = "## User-facing Communication Contract"


def _contract(text: str) -> str:
    start = text.index(HEADING)
    rest = text[start:]
    end = rest.find("\n## ", len(HEADING))
    return rest if end == -1 else rest[:end]


def test_bootstrap_is_the_only_communication_authority() -> None:
    bootstrap = BOOTSTRAP.read_text(encoding="utf-8")
    assert bootstrap.count(HEADING) == 1

    competing = []
    for root in (ROOT / "skills", ROOT / "agents", ROOT / "references"):
        for path in root.rglob("*.md"):
            if path != BOOTSTRAP and HEADING in path.read_text(encoding="utf-8"):
                competing.append(path.relative_to(ROOT).as_posix())
    assert competing == []


def test_contract_uses_progressive_disclosure_by_request_shape() -> None:
    contract = _contract(BOOTSTRAP.read_text(encoding="utf-8")).lower()

    assert "progressive disclosure" in contract
    assert "command or status" in contract
    assert "explanation or review" in contract
    assert "completed change" in contract
    assert "blocked or unknown" in contract
    assert "changed files" in contract
    assert "verification" in contract
    assert "unresolved" in contract


def test_contract_preserves_human_semantics_before_machine_ids() -> None:
    contract = _contract(BOOTSTRAP.read_text(encoding="utf-8")).lower()

    assert "semantic label" in contract
    assert "bare id" in contract
    assert "machine" in contract
    assert "human-facing" in contract


def test_contract_does_not_trade_completeness_for_arbitrary_brevity() -> None:
    contract = _contract(BOOTSTRAP.read_text(encoding="utf-8")).lower()

    assert "fixed word" in contract
    assert "hard list" in contract
    assert "unsupported time estimate" in contract
    assert "uncertainty" in contract
    assert "destructive-action confirmation" in contract


def test_completion_rules_are_evidence_conditioned_not_filler_templates() -> None:
    text = BOOTSTRAP.read_text(encoding="utf-8")
    lower = text.lower()

    assert "this implementation can silently fail when: ___" not in lower
    assert "this design assumes ___ remains true" not in lower
    assert "owning artifact" in lower
    assert "decision-changing" in lower
    assert "do not invent" in lower


def test_codex_conversion_preserves_the_communication_contract(
    tmp_path: Path,
) -> None:
    output = tmp_path / "codex"
    ConversionEngine("codex").run(ROOT, output)

    converted = (
        output / ".agents/skills/samsara-samsara-bootstrap/SKILL.md"
    ).read_text(encoding="utf-8")
    assert HEADING in converted
    assert "progressive disclosure" in converted.lower()
