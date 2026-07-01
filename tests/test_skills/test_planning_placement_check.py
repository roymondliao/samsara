"""Doc-contract tests for the planning-side placement consistency gate (A4 / Task 1).

ISSUE-001: a plan can decide a placement/ownership fact in `Key Decisions`
(e.g. "shared, not samsara-exclusive") and then contradict it in the `File Map`
paths, with no check between the two independent sections. Task 1 adds Gate 1 to
`skills/planning/SKILL.md`: a hard-STOP File-Map<->Key-Decisions consistency step
plus an anti-bias prompt, scoped to placement/ownership decisions only.

Issue-001 / Task 3 lesson: unguarded doc rules silently rot. These tests assert
the STOP step is written, enforcing, and correctly scoped — not that the runtime
agent obeys it (doc-presence != runtime obedience; deferred to dogfood).

The tests assert behavioral tokens, not exact prose.
"""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _consistency_section(planning: str) -> str:
    """Return the File Map Consistency Check section body, scoped so token
    assertions cannot be satisfied by unrelated intro prose elsewhere in the
    skill (the whole-file-find trap from the implementer-contract lesson)."""
    # anchor on the heading's unique tail, not the first textual occurrence — the
    # dot graph also names the step, and a bare find() would grab the graph node
    # label. "— STOP Gate" appears only in the heading, so this is heading-unique
    # AND step-number-agnostic (survives a renumber of the step).
    marker = "File Map Consistency Check — STOP Gate"
    start = planning.find(marker)
    assert start != -1, "planning SKILL.md has no 'File Map Consistency Check' step"
    rest = planning[start + len(marker) :]
    # section ends at the next top-level heading
    end = rest.find("\n## ")
    return rest if end == -1 else rest[:end]


def test_dc2_consistency_check_is_a_stop_gate_not_advisory() -> None:
    """DC-2 (soft check): the step must STOP / block proceeding to task
    decomposition on a genuine contradiction — advisory wording alone
    ('consider', 'may want to') must not silently impersonate a hard gate."""
    section = _consistency_section(read("skills/planning/SKILL.md"))

    assert "STOP" in section, "consistency check must use hard-STOP language"
    lowered = section.lower()
    assert "do not proceed" in lowered
    assert "task decomposition" in lowered


def test_dc3_scoped_to_placement_ownership_not_all_key_decisions() -> None:
    """DC-3 (over-broad scope): the check must be scoped to placement/ownership
    decisions, and must NOT require every Key Decision to map to a path (that
    fires on path-irrelevant decisions -> noise -> the whole gate gets skipped)."""
    planning = read("skills/planning/SKILL.md")
    section = _consistency_section(planning)
    lowered = section.lower()

    assert "placement" in lowered
    assert "ownership" in lowered
    # the over-broad phrasing that turns the gate into noise
    assert "every key decision must map to a path" not in planning.lower()
    # non-placement decisions are explicitly out of scope (three-state honesty)
    assert "out of scope" in lowered


def test_dc4_anti_bias_prose_is_distinct_from_the_stop_gate() -> None:
    """DC-4 (anti-bias without gate): the STOP consistency directive and the
    anti-bias prompt must both be present as DISTINCT directives inside the step —
    the anti-bias line alone (no STOP check) does not satisfy the gate, and the
    STOP alone (no anti-bias) does not either."""
    section = _consistency_section(read("skills/planning/SKILL.md"))
    lowered = section.lower()

    # two distinct bolded directives must both exist inside the same step:
    # the hard STOP...
    assert "**stop on" in lowered, "no bolded STOP directive in the step"
    # ...and a separate anti-bias prompt.
    assert "**anti-bias:**" in lowered, "no bolded anti-bias directive in the step"

    # distinctness is structural, not positional: the two directives live on
    # different lines (the anti-bias directive is its own paragraph, not the
    # STOP directive reworded). This reddens if they ever collapse into one line.
    stop_lines = [ln for ln in section.splitlines() if "**STOP on" in ln]
    anti_lines = [ln for ln in section.splitlines() if "**Anti-bias:**" in ln]
    assert stop_lines and anti_lines
    assert stop_lines[0] != anti_lines[0]

    # the anti-bias directive itself must carry the "derive paths from Key
    # Decisions" instruction — asserted on the directive line, not the whole file,
    # so moving the reference out of the anti-bias prose reddens the test.
    anti = anti_lines[0].lower()
    assert "derive" in anti
    assert "key decisions" in anti


def test_stop_gate_precedes_task_decomposition_step() -> None:
    """The STOP must sit before Task Decomposition, or it cannot prevent wrong
    paths from being baked into task files."""
    planning = read("skills/planning/SKILL.md")

    # anchor on the heading tail (unique to the section heading), not the first
    # "File Map Consistency Check" occurrence, which is the dot graph node label.
    check_pos = planning.find("File Map Consistency Check — STOP Gate")
    decomp_pos = planning.find("## Step 4: Task Decomposition")
    assert check_pos != -1
    assert decomp_pos != -1
    assert check_pos < decomp_pos, "consistency STOP must precede task decomposition"
