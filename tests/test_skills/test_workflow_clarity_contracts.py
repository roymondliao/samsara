"""Contracts for unambiguous anchors and portable validator instructions."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCAR_GUIDE = ROOT / "skills" / "implement" / "scar-report.md"
SCAR_SCHEMA = ROOT / "skills" / "implement" / "templates" / "scar-schema.yaml"
IMPLEMENT = ROOT / "skills" / "implement" / "SKILL.md"
PLANNING_FLOW = ROOT / "skills" / "planning" / "flow.md"
VALIDATE = ROOT / "skills" / "validate-and-ship" / "SKILL.md"


def test_death__scar_guide_points_detail_to_go_elsewhere_anchor() -> None:
    guide = SCAR_GUIDE.read_text(encoding="utf-8").lower()
    guide = " ".join(guide.split())

    assert "destinations defined by the schema's `go-elsewhere` anchor" in guide
    assert "pointer defined by the schema's `direct-bullets` anchor" not in guide


def test_death__schema_anchor_has_no_zero_information_alias() -> None:
    schema = SCAR_SCHEMA.read_text(encoding="utf-8").lower()

    assert "# granularity-floor:" in schema
    assert "# granularity-floor (granularity floor):" not in schema


def test_death__validator_commands_do_not_assume_local_venv_or_source_tree() -> None:
    instructions = (IMPLEMENT, PLANNING_FLOW, VALIDATE)
    for instruction in instructions:
        text = instruction.read_text(encoding="utf-8").lower()
        assert "source .venv/bin/activate" not in text
        assert "uv run python" in text
        assert "installed skill directory" in text
