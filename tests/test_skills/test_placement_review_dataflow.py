"""Doc-contract tests for the review-side placement gate + Key Decisions data
flow (A4 / Task 2).

The corruption signature (DC-1): agents/code-reviewer.md gains an Architectural
Placement review dimension, but the yin-reviewer dispatch never carries the plan's
Key Decisions — so the reviewer "checks placement" against nothing and silently
passes. The load-bearing assertion here is the DATA FLOW: Key Decisions must reach
the yin code-reviewer dispatch in BOTH skills/implement/dispatch-template.md AND
skills/iteration/SKILL.md. Implement-only is a FAIL (DC-5: iteration fixes reviewed
blind to placement).

Assertions target behavioral tokens (architectural placement, key decisions,
placement/ownership), not exact prose. Doc-presence != runtime judgement: these
guard that the wiring is WRITTEN, not that the reviewer judges placement correctly
at runtime (deferred to dogfood).

A second concern lives here too (added in Level-2 iteration): the three-state
placement protocol (matches/contradicts/out-of-scope) is stated by TWO independent
gates — the planning File Map Consistency Check and this reviewer dimension. The
parity tests below guard that the two gates do not drift apart in their state labels
or lose the cross-reference that keeps them aligned. This reads skills/planning
(PLANNING) in addition to the reviewer-dispatch files.
"""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

CODE_REVIEWER = "agents/code-reviewer.md"
IMPLEMENT_DISPATCH = "skills/implement/dispatch-template.md"
ITERATION = "skills/iteration/SKILL.md"
PLANNING = "skills/planning/SKILL.md"


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _section(text: str, marker: str, ends=("\n### ", "\n## ", "\n---")) -> str:
    """Return the body from `marker` up to the next section boundary, so token
    assertions cannot be satisfied by unrelated text elsewhere in the file."""
    start = text.find(marker)
    assert start != -1, f"marker not found: {marker!r}"
    rest = text[start + len(marker) :]
    cut = len(rest)
    for end in ends:
        i = rest.find(end)
        if i != -1:
            cut = min(cut, i)
    return rest[:cut]


def _yin_dispatch(dispatch_template: str) -> str:
    """The yin code-reviewer dispatch block only — NOT the code-quality block.
    Key Decisions belong in the yin dispatch (placement = plan-compliance = yin
    scope); asserting on the yin block guards against wiring the wrong reviewer."""
    return _section(
        dispatch_template, "### Yin reviewer", ends=("\n### Code Quality reviewer",)
    )


def _iteration_fix_section(iteration: str) -> str:
    return _section(iteration, "## Step 3: Fix", ends=("\n## Step 4",))


# --- DC-1: the corruption signature (Primary-evaluator core) ---


def test_dc1_key_decisions_reach_implement_yin_dispatch() -> None:
    """Implement-phase yin dispatch must carry the plan's Key Decisions, or the
    placement dimension checks against nothing."""
    yin = _yin_dispatch(read(IMPLEMENT_DISPATCH))
    lowered = yin.lower()

    assert "key decisions" in lowered
    assert "placement" in lowered


def test_dc5_key_decisions_reach_iteration_yin_dispatch() -> None:
    """DC-5 (iteration forgotten): the per-fix yin dispatch in iteration must ALSO
    carry Key Decisions — covering only implement leaves iteration-phase fixes
    reviewed blind to placement. This path is checked INDEPENDENTLY of implement."""
    fix_section = _iteration_fix_section(read(ITERATION))
    lowered = fix_section.lower()

    assert "key decisions" in lowered
    assert "placement" in lowered
    # tie the data flow to the yin reviewer specifically, not just anywhere in Step 3
    assert "code-reviewer" in lowered


def test_dc1_data_flow_present_in_both_paths_not_just_one() -> None:
    """The corruption signature is 'dimension exists but a dispatch path is blind'.
    Assert BOTH paths independently — one present + one absent must still FAIL."""
    implement_yin = _yin_dispatch(read(IMPLEMENT_DISPATCH)).lower()
    iteration_fix = _iteration_fix_section(read(ITERATION)).lower()

    assert "key decisions" in implement_yin, (
        "implement yin dispatch missing Key Decisions"
    )
    assert "key decisions" in iteration_fix, (
        "iteration yin dispatch missing Key Decisions"
    )


# --- Placement dimension present in the reviewer ---


def test_code_reviewer_has_architectural_placement_dimension() -> None:
    reviewer = read(CODE_REVIEWER)
    section = _section(reviewer, "Architectural Placement")
    lowered = section.lower()

    assert "placement" in lowered
    assert "ownership" in lowered
    # the reviewer must be told to check against the plan's Key Decisions
    assert "key decisions" in lowered


def test_placement_dimension_documents_three_state_out_of_scope() -> None:
    """Three-state honesty: a non-placement Key Decision is out of scope, not
    forced into matches/contradicts."""
    reviewer = read(CODE_REVIEWER)
    section = _section(reviewer, "Architectural Placement")
    lowered = section.lower()

    assert "out of scope" in lowered
    # and the reviewer must not silently pass when the dispatch carried no Key
    # Decisions — absence is itself a finding, not a pass
    assert "no key decisions" in lowered or "absent" in lowered


# --- Iteration fix: three-state DRY (Gate 1 / Gate 2 parity) ---


def _has_out_of_scope_bullet(section: str) -> bool:
    # Marked bet: both gates format the third-state label as a bold markdown
    # bullet (`- **out of scope**`). A format migration (italics, no emphasis)
    # would make this return False — read a failure as "label format changed OR
    # label drifted", not strictly a semantic drift.
    return any(
        ln.strip().lower().startswith("- **out of scope**")
        for ln in section.splitlines()
    )


def test_three_state_labels_consistent_across_both_gates() -> None:
    """Iteration fix (three-state DRY): the planning Gate 1 and reviewer Gate 2
    both classify placement into the SAME three states. The two gates are
    independent (defense-in-depth) but must not drift apart in the state labels,
    or a maintainer reading one gate mislearns the protocol. Guards the third
    state's bullet LABEL specifically — 'out of scope' already appears mid-sentence
    in both, so only the leading bullet label distinguishes drift."""
    planning_sec = _section(read(PLANNING), "File Map Consistency Check — STOP Gate")
    reviewer_sec = _section(read(CODE_REVIEWER), "Architectural Placement")

    for token in ("matches", "contradicts", "out of scope"):
        assert token in planning_sec.lower(), f"planning gate missing state: {token}"
        assert token in reviewer_sec.lower(), f"reviewer gate missing state: {token}"

    # third-state bullet label parity: both lead the third bullet with the same
    # label ("out of scope"), not a divergent synonym ("not a placement decision")
    assert _has_out_of_scope_bullet(planning_sec), "planning third-state label drifted"
    assert _has_out_of_scope_bullet(reviewer_sec), "reviewer third-state label drifted"


def test_reviewer_gate_cross_references_planning_gate() -> None:
    """The reviewer placement dimension must name the planning consistency check as
    the same protocol, so a maintainer changing one gate knows to align the other
    (the anti-drift anchor the DRY concern asked for, without a shared file)."""
    reviewer_sec = _section(read(CODE_REVIEWER), "Architectural Placement")
    assert "file map consistency check" in reviewer_sec.lower(), (
        "reviewer Architectural Placement section missing cross-reference to the "
        "planning File Map Consistency Check — the two gates can silently drift"
    )
