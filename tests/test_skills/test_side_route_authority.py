"""Cross-layer routing contracts for Fast-track and Debugging."""

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
BOOTSTRAP = ROOT / "skills" / "samsara-bootstrap" / "SKILL.md"
DEBUGGING = ROOT / "skills" / "debugging" / "SKILL.md"
BUG_REPORT = ROOT / "skills" / "debugging" / "templates" / "bug-report.yaml"
ROOT_CAUSE = ROOT / "skills" / "debugging" / "templates" / "root-cause.yaml"
FIX_SUMMARY = ROOT / "skills" / "debugging" / "templates" / "fix-summary.yaml"
ROOT_CAUSE_GUIDE = ROOT / "skills" / "debugging" / "root-cause-tracing.md"
RESEARCH = ROOT / "skills" / "research" / "SKILL.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_death__debugging_owns_diagnosis_not_repair() -> None:
    skill = _read(DEBUGGING)
    normalized = " ".join(skill.split()).lower()

    assert "debugging owns diagnosis" in normalized
    assert "does not implement the repair" in normalized
    assert "repair authorization" in normalized
    assert "invoke `samsara:fast-track`" in skill
    assert "invoke `samsara:research`" in skill
    assert "→ invoke `samsara:implement`" not in skill
    assert "fix-summary.yaml" not in skill
    assert not FIX_SUMMARY.exists()


def test_death__bootstrap_projects_the_debugging_routes_without_rewriting_them() -> (
    None
):
    bootstrap = _read(BOOTSTRAP)

    assert 'debugging -> fasttrack [label="bounded repair"]' in bootstrap
    assert 'debugging -> research [label="structural / wide / unknown"]' in bootstrap
    assert "debugging -> implement" not in bootstrap


def test_death__research_consumes_debugging_evidence_without_rewriting_it() -> None:
    research = " ".join(_read(RESEARCH).split())

    assert "bugfix/<bug>/bug-report.yaml" in research
    assert "bugfix/<bug>/root-cause.yaml" in research
    assert "do not restate the diagnosis" in research


def test_unit__debugging_templates_separate_observation_from_diagnosis() -> None:
    report = yaml.safe_load(_read(BUG_REPORT))
    cause = yaml.safe_load(_read(ROOT_CAUSE))

    assert {
        "schema_version",
        "bug",
        "failure",
        "impact",
        "containment",
        "unknowns",
    } <= set(report)
    assert {
        "schema_version",
        "bug_report_ref",
        "root_cause",
        "reproduction",
        "rot_path",
        "death_test",
        "repair",
    } <= set(cause)
    assert {
        "status",
        "hypothesis",
        "evidence_refs",
        "refuting_evidence",
        "why_hidden",
    } <= set(cause["root_cause"])
    assert {"authorized", "scope", "route", "rationale"} <= set(cause["repair"])


def test_death__debugging_skill_owns_format_validation() -> None:
    skill = _read(DEBUGGING)

    assert "scripts/validate_format.py" in skill
    assert "format only" in skill.lower()


def test_death__root_cause_reference_preserves_yin_side_diagnosis() -> None:
    guide = _read(ROOT_CAUSE_GUIDE)
    normalized = " ".join(guide.split()).lower()

    assert "why did the system allow this failure to look healthy" in normalized
    assert "the failure is the symptom" in normalized
    assert "detection system" in normalized
    assert "rot distance" in normalized
    assert "pretended to be healthy" in normalized
    assert "accomplice" in normalized
    assert "premature fix" in normalized
    assert "unknown" in normalized
