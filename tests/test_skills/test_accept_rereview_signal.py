"""Contracts for signal-driven risk acceptance across Iteration and shipping."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ITERATION_FLOW = ROOT / "skills" / "iteration" / "flow.md"
ITERATION_LOG_TEMPLATE = (
    ROOT / "skills" / "iteration" / "templates" / "iteration-log.yaml"
)
SCAR_SCHEMA = ROOT / "skills" / "implement" / "templates" / "scar-schema.yaml"
SHIP_GUIDE = ROOT / "skills" / "validate-and-ship" / "ship-manifest.md"
SHIP_TEMPLATE = (
    ROOT / "skills" / "validate-and-ship" / "templates" / "ship-manifest.yaml"
)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def section(text: str, heading: str, next_heading: str) -> str:
    start = text.index(heading)
    end = text.index(next_heading, start)
    return text[start:end]


def accept_requires_signal_owner(line: str) -> bool:
    lowered = line.lower()
    if re.search(r"\b(?:not|never|without)\b", lowered):
        return False
    return all(
        token in lowered
        for token in ("require", "rationale", "re_review_signal", "owner")
    )


def test_death__iteration_accept_is_signal_driven_not_calendar_driven() -> None:
    triage = section(
        read(ITERATION_FLOW),
        "## Step 2: Triage (Execution-Mode Gate)",
        "## Step 3: Fix (Per-Fix Commit)",
    )
    accept_line = next(line for line in triage.splitlines() if "`accept`" in line)

    assert accept_requires_signal_owner(accept_line)
    assert "evidence refs" in accept_line.lower()
    assert "expiry" not in accept_line.lower() and "expires" not in accept_line.lower()


def test_death__negated_signal_requirement_is_not_accepted() -> None:
    decoy = "- accept: require rationale; re_review_signal and owner are not required"
    assert accept_requires_signal_owner(decoy) is False


def test_unit__scar_schema_declares_the_accept_lifecycle_fields() -> None:
    schema = read(SCAR_SCHEMA).lower()

    assert "accepted:" in schema
    for token in ("rationale", "re_review_signal", "owner", "evidence_refs"):
        assert token in schema


def test_death__current_flow_has_no_legacy_log_migration_contract() -> None:
    restore = section(
        read(ITERATION_FLOW),
        "## Step 0: Restore Durable State",
        "## Entry Triage",
    ).lower()

    assert "expiry_date" not in restore
    assert "iteration-log" not in restore
    assert "iteration log" not in restore


def test_death__new_iteration_log_template_does_not_exist() -> None:
    assert not ITERATION_LOG_TEMPLATE.exists()


def test_death__ship_manifest_rule_requires_signal_and_owner_not_expiry() -> None:
    guide = read(SHIP_GUIDE)
    rule = section(
        guide,
        "## Evidence Rules",
        "## Operational Controls",
    ).lower()

    assert "human-only" in rule
    for token in ("requires", "rationale", "re_review_signal", "owner"):
        assert token in rule
    assert "signal-driven" in rule
    assert not re.search(r"must\s+have[^.!?\n]{0,30}expir", rule)


def test_unit__ship_manifest_template_has_signal_and_owner_fields() -> None:
    template = read(SHIP_TEMPLATE)

    for token in ("finding_ref:", "rationale:", "re_review_signal:", "owner:"):
        assert token in template
    assert not re.search(
        r"^\s*#?\s*(expires|expiry|expiry_date):", template, re.MULTILINE
    )
