"""Authority and artifact contracts for the Fast-track side route."""

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "skills" / "fast-track" / "SKILL.md"
TEMPLATE = ROOT / "skills" / "fast-track" / "templates" / "fast-track.yaml"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_death__fast_track_requires_evidence_not_line_count() -> None:
    skill = _read(SKILL)
    normalized = " ".join(skill.split()).lower()

    assert "line count is only a signal" in normalized
    assert "unresolved design question" in normalized
    assert "damage radius" in normalized
    assert "shared mutation surface" in normalized
    assert "read before writing" in normalized


def test_death__fast_track_has_no_unconsumed_scar_lifecycle() -> None:
    skill = _read(SKILL)
    template = _read(TEMPLATE)

    for retired in ("scar_tag", "scar_items", "[scar:none]", "[scar:n items]"):
        assert retired not in skill.lower()
        assert retired not in template.lower()


def test_death__fast_track_review_uses_domain_authority_and_evidence() -> None:
    skill = _read(SKILL)
    normalized = " ".join(skill.split()).lower()

    assert "domain router" in normalized
    assert "domain reference" in normalized
    assert "fixed c5-c8 subset" in normalized
    assert "evidence refs" in normalized
    assert "unknown" in normalized


def test_death__fast_track_preserves_yin_side_challenge() -> None:
    skill = _read(SKILL)
    normalized = " ".join(skill.split()).lower()

    assert "## yin-side lens" in skill.lower()
    assert "what makes this change look smaller than it is" in normalized
    assert "who detects the failure first" in normalized
    assert "how far does damage spread" in normalized
    assert "which assumption makes this change appear safe" in normalized
    assert "fallback" in normalized
    assert "can anything be deleted" in normalized
    assert "are names honest" in normalized


def test_unit__fast_track_template_has_compact_lifecycle_shape() -> None:
    parsed = yaml.safe_load(_read(TEMPLATE))

    assert {
        "type",
        "status",
        "description",
        "source_refs",
        "entry",
        "acceptance",
        "death_evidence",
        "verification",
        "review",
        "files_changed",
        "escalation",
    } <= set(parsed)
    assert {
        "authority",
        "risk_evidence",
        "affected_surfaces",
        "structural_impact",
        "unknowns",
    } <= set(parsed["entry"])
    assert {
        "domains",
        "reference_refs",
        "evidence_refs",
        "findings",
        "unknowns",
    } <= set(parsed["review"])


def test_death__fast_track_skill_owns_format_validation() -> None:
    skill = _read(SKILL)

    assert "scripts/validate_format.py" in skill
    assert "format only" in skill.lower()
