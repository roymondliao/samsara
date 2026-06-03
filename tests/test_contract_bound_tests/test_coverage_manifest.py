"""Required live surfaces for contract-bound test instructions.

This test keeps the suite scoped to named live protocol surfaces. It intentionally
does not inspect prose shape or historical task artifacts.
"""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

REQUIRED_LIVE_PROTOCOL_SURFACES = {
    "reference": ROOT / "references" / "test-contract.md",
    "implementer": ROOT / "agents" / "implementer.md",
    "implement_skill": ROOT / "skills" / "implement" / "SKILL.md",
    "code_reviewer": ROOT / "agents" / "code-reviewer.md",
    "code_quality_reviewer": ROOT / "agents" / "code-quality-reviewer.md",
    "dispatch_template": ROOT / "skills" / "implement" / "dispatch-template.md",
    "task_format": ROOT / "skills" / "planning" / "task-format.md",
    "planning_skill": ROOT / "skills" / "planning" / "SKILL.md",
}


def test_required_protocol_surfaces_are_named_files():
    for role, path in REQUIRED_LIVE_PROTOCOL_SURFACES.items():
        assert path.is_file(), f"{role} protocol surface is missing: {path}"
        assert "changes" not in path.parts, (
            f"{role} must point at a live instruction/template file, not a "
            f"historical changes artifact: {path}"
        )


def test_manifest_roles_are_explicit_and_stable():
    assert set(REQUIRED_LIVE_PROTOCOL_SURFACES) == {
        "reference",
        "implementer",
        "implement_skill",
        "code_reviewer",
        "code_quality_reviewer",
        "dispatch_template",
        "task_format",
        "planning_skill",
    }
