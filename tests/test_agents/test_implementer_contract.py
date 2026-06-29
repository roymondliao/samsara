"""
Doc-contract guard for two Karpathy-aligned implementer rules.

These are DOC-PRESENCE + ORDERING tests, not behavioral tests: an agent's
instruction file is its contract. Issue-001 and the codebase-map-churn Task 3
both proved that an unguarded doc rule silently rots — a later trim of the
file deletes it with no signal. These tests make that deletion go RED.

Rules guarded:
  A1 Dependency Hygiene — agents/implementer.md must PROHIBIT silently adding a
     dependency (ask stdlib / an existing dep first; record why one earns its place).
  A3 Read-Before-Write — agents/implementer.md Execution Order must contain a
     "read before you write" step, and it must be ORDERED BEFORE the death-test
     step (a death test written before reading the codebase asserts assumed, not
     real, conventions). Ordering is the contract, not mere presence.

Both rules must also reach INLINE mode (implement skill, mode C) where the agent
definition is not loaded, so skills/implement/SKILL.md must echo them.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # tests/test_agents/ -> repo root
IMPLEMENTER = ROOT / "agents" / "implementer.md"
IMPLEMENT_SKILL = ROOT / "skills" / "implement" / "SKILL.md"


# ---------------------------------------------------------------------------
# A1 — Dependency Hygiene
# ---------------------------------------------------------------------------


def test_death__dependency_hygiene_clause_present() -> None:
    """implementer.md must prohibit silent dependency addition (stdlib-first)."""
    text = IMPLEMENTER.read_text(encoding="utf-8").lower()
    assert "dependency" in text and ("standard library" in text or "stdlib" in text), (
        "implementer.md does not contain a dependency-hygiene rule. Karpathy VIII / "
        "the Samsara axiom applied to deps: before adding a dependency, ask whether "
        "stdlib or an existing dep already covers it. Without this clause an agent "
        "smuggles permanent external code into the manifest with no justification."
    )


def test_death__dependency_hygiene_reaches_inline_mode() -> None:
    """skills/implement/SKILL.md must echo dependency hygiene for inline mode (C)."""
    text = IMPLEMENT_SKILL.read_text(encoding="utf-8").lower()
    assert "dependency" in text and ("standard library" in text or "stdlib" in text), (
        "implement SKILL.md does not echo the dependency-hygiene rule. In inline "
        "mode the agents/implementer.md definition is not loaded, so the main agent "
        "must own this constraint via the skill — otherwise inline tasks skip it."
    )


# ---------------------------------------------------------------------------
# A3 — Read-Before-Write (presence AND ordering)
# ---------------------------------------------------------------------------

_READ_MARKER = "read before you write"
_DEATH_MARKER = "write death tests"


def _execution_order_section(text_lower: str) -> str:
    """Return the '## Execution Order' section body (until the next '## ' header).

    Scoping matters: the file's intro prose also says 'write death tests', so a
    whole-file search would compare the wrong positions. The ordering contract
    lives inside the Execution Order numbered list, so we search only there.
    """
    start = text_lower.find("## execution order")
    assert start != -1, "implementer.md has no '## Execution Order' section"
    rest = text_lower[start + len("## execution order") :]
    end = rest.find("\n## ")
    return rest if end == -1 else rest[:end]


def test_death__read_before_write_precedes_death_tests() -> None:
    """The read-before-write step MUST be ordered before the death-test step.

    This is the contract that matters: a death test written before the implementer
    has read the codebase asserts assumed conventions, not real ones. If a future
    edit reorders these (or drops the read step), this goes RED. Scoped to the
    Execution Order section so the intro prose's 'write death tests' is not matched.
    """
    section = _execution_order_section(IMPLEMENTER.read_text(encoding="utf-8").lower())
    read_idx = section.find(_READ_MARKER)
    death_idx = section.find(_DEATH_MARKER)
    assert read_idx != -1, (
        "read-before-write step missing from the Execution Order section"
    )
    assert death_idx != -1, (
        "'write death tests' step missing from the Execution Order section — "
        "the ordering contract cannot be verified."
    )
    assert read_idx < death_idx, (
        f"read-before-write (index {read_idx}) must precede the death-test step "
        f"(index {death_idx}) within Execution Order. A death test written before "
        "reading the codebase pins assumed conventions, not real ones."
    )


def test_death__read_before_write_reaches_inline_mode() -> None:
    """skills/implement/SKILL.md must echo read-before-write for inline mode (C)."""
    text = IMPLEMENT_SKILL.read_text(encoding="utf-8").lower()
    assert _READ_MARKER in text, (
        "implement SKILL.md does not echo the read-before-write rule. In inline mode "
        "the agent definition is not loaded; the main agent must own this constraint."
    )
