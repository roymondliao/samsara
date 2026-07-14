"""
Doc-contract guard for Task 3 (security-privacy-review 折入 validate-and-ship
成 Step 0 STOP gate): `skills/security-privacy-review/` is deleted and its
gate is folded into `skills/validate-and-ship/SKILL.md` as a Step 0 STOP
gate that runs before any other validation step. Routing skills
(samsara-bootstrap, implement, iteration) must point at validate-and-ship
directly, never at the deleted skill.

These are DOC-PRESENCE / ARTIFACT-SHAPE tests — there is no runtime code in
this task (see .samsara/systemic-scars.yaml `doc-instruction-no-code-
enforcement`: nothing in this repo executes `git diff` or blocks a commit;
the guard here is that the DOCUMENT preserves the gate's semantics, not that
an agent is mechanically forced to obey them).

Death cases guarded (see task-3.md "Death Test Requirements"):
  DC1: Step 0 gate folded in but moved AFTER (or dropped from before)
       Remaining Exposure Check — structural position, index_of comparison,
       not label presence.
  DC2: "unknown != pass" clause disappears during the fold — unknown could
       silently become an implicit pass.
  DC3: "full diff re-review (not just the fix delta)" clause disappears —
       fix loop could silently narrow its re-review scope.
  DC4: auto mode's "capability-absent / unknown / failing -> high-
       uncertainty reject, must not proceed" clause disappears or is
       reworded to allow proceeding.
  DC5: samsara-bootstrap/SKILL.md still names `samsara:security-privacy-
       review` — a dangling routing-graph node pointing at a deleted skill.
  DC6: implement/SKILL.md or iteration/SKILL.md still instructs invoking
       `samsara:security-privacy-review` — a dangling transition target.

Unit-test contract sources (see task-3.md "Unit Test Contract"):
  - validate-and-ship SKILL.md's Step 0 section: the 7 concept-tokens named
    in task-3.md's Context list 1-7 (documented artifact shape).
  - samsara-bootstrap SKILL.md's routing dot-graph: node set (no
    security_review node) + edge set (implement/iteration connect directly
    to validate).
  - implement/iteration SKILL.md's Transition section: next-skill name is
    `samsara:validate-and-ship`, never the deleted skill.

All directional (require/prohibit) assertions are polarity-bound per
references/test-contract.md rule 2 (presence-not-polarity): every
directional predicate has a permanent wrong-direction decoy fixture proving
the SAME predicate function reports the decoy's claim as absent/present in
the opposite direction, and a clause-bounded (non-DOTALL) proximity window
per the task's stated test lesson (fixed 20-40 char windows, `[^.!?\\n]`
bounded, never a large DOTALL window).
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # tests/test_skills/ -> repo root
VALIDATE = ROOT / "skills" / "validate-and-ship" / "SKILL.md"
BOOTSTRAP = ROOT / "skills" / "samsara-bootstrap" / "SKILL.md"
IMPLEMENT = ROOT / "skills" / "implement" / "SKILL.md"
ITERATION = ROOT / "skills" / "iteration" / "SKILL.md"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Section extractors
# ---------------------------------------------------------------------------


def _step0_section(text: str) -> str:
    start = text.find("## Step 0: Security & Privacy Gate")
    assert start != -1, (
        "validate-and-ship SKILL.md has no '## Step 0: Security & Privacy Gate' section"
    )
    rest = text[start:]
    end = rest.find("\n## ", 1)
    assert end != -1, (
        "validate-and-ship SKILL.md Step 0 section is not bounded by another '## ' heading"
    )
    return rest[:end]


def _auto_mode_gate_section(text: str) -> str:
    start = text.find("## Auto Mode Gate")
    assert start != -1, "file has no '## Auto Mode Gate' section"
    rest = text[start:]
    end = rest.find("\n## ", 1)
    return rest if end == -1 else rest[:end]


def _transition_section(text: str) -> str:
    start = text.find("## Transition")
    assert start != -1, "file has no '## Transition' section"
    rest = text[start:]
    end = rest.find("\n## ", 1)
    return rest if end == -1 else rest[:end]


# ---------------------------------------------------------------------------
# Polarity-bound predicates (production assertions AND their permanent
# wrong-direction decoy tests call the SAME function).
# ---------------------------------------------------------------------------

_NEGATION_EN = re.compile(r"\bnot\b|\bnever\b|\bwithout\b|\bno longer\b")


def step0_precedes_remaining_exposure(text: str) -> bool:
    """True iff '## Step 0: Security & Privacy Gate' occurs (structural
    position, index_of) strictly before '### 1. Remaining Exposure Check' in
    the same document. False if either marker is missing, or if Step 0
    occurs at or after Remaining Exposure Check."""
    step0_idx = text.find("## Step 0: Security & Privacy Gate")
    exposure_idx = text.find("### 1. Remaining Exposure Check")
    if step0_idx == -1 or exposure_idx == -1:
        return False
    return step0_idx < exposure_idx


def step0_declares_unknown_never_pass(section_lower: str) -> bool:
    """True iff the Step 0 section ties 'unknown' to a negation ('never' /
    'not') within a clause-bounded gap, and that negation is itself within
    a clause-bounded gap of 'pass'. Clause-bounded (`[^.!?\\n]`) — never
    DOTALL — per the task's stated test lesson."""
    m = re.search(
        r"\bunknown\b[^.!?\n]{0,40}(never|not)[^.!?\n]{0,30}\bpass\b", section_lower
    )
    return m is not None


def step0_requires_full_diff_refresh(section_lower: str) -> bool:
    """True iff the fix loop ties 'full diff' directly (clause-bounded gap)
    to a 'not just the fix delta' qualifier, in that order."""
    m = re.search(r"full diff[^.!?\n]{0,40}not just the fix delta", section_lower)
    return m is not None


def auto_gate_rejects_step0_uncertainty(section_lower: str) -> bool:
    """True iff the Auto Mode Gate section (a) records a high-uncertainty
    `reject` for Step 0 uncertainty, (b) names 'unknown' as one of the
    triggering conditions, and (c) explicitly states auto mode must not
    proceed past Step 0 under that condition. All three must hold — a
    decoy that records the reject label without also blocking progression
    is the exact silent-failure this guards against."""
    return (
        "high-uncertainty `reject`" in section_lower
        and "unknown" in section_lower
        and re.search(r"must not proceed[^.!?\n]{0,40}step 0", section_lower)
        is not None
    )


def names_deleted_security_skill(text: str) -> bool:
    """True iff the text still names the deleted `samsara:security-privacy-
    review` skill anywhere (dangling routing-graph node / transition
    target)."""
    return "samsara:security-privacy-review" in text


# Permanent wrong-direction / hostile decoys.

_EXPOSURE_BEFORE_STEP0_DECOY = (
    "## Something\n\n### 1. Remaining Exposure Check\nRead Scar items.\n\n"
    "## Step 0: Security & Privacy Gate（STOP）\nToo late, already validating.\n"
)
_MISSING_STEP0_DECOY = (
    "## Something\n\n### 1. Remaining Exposure Check\nRead Scar items.\n"
)

_UNKNOWN_EVENTUALLY_PASS_DECOY = (
    "review results include pass, fail, and unknown. unknown review results "
    "eventually become a pass once retried, so the gate can continue."
)
_UNKNOWN_NEVER_PASS_REAL = (
    "unknown: review could not complete (timeout, partial result, tool error). "
    "unknown is never treated as pass. route retry / self-confirm / stop."
)

_FIX_DELTA_ONLY_DECOY = (
    "re-run the review on the fix delta only, not the full diff — this keeps "
    "the re-review fast."
)
_FULL_DIFF_REAL = (
    "re-run the review on the full diff, not just the fix delta — a fix can "
    "introduce a new issue elsewhere in the same diff."
)

_AUTO_LABEL_ONLY_DECOY = (
    "absent capability or an unknown review result records a high-uncertainty "
    "`reject`, but auto mode may still continue toward remaining exposure "
    "while noting the gap in the ship manifest."
)
_AUTO_BLOCKS_REAL = (
    "unknown result, timeout, partial result, or tool error: record "
    "high-uncertainty `reject`. if review result is unknown, the gatekeeper "
    "must not proceed past step 0 to remaining exposure."
)

_DANGLING_SKILL_DECOY = "invoke `samsara:security-privacy-review` skill.\n"


# ---------------------------------------------------------------------------
# Death tests
# ---------------------------------------------------------------------------


def test_death__step0_gate_precedes_remaining_exposure_check() -> None:
    """DC1 — structural position (index_of), not label presence. If Step 0
    is moved after Remaining Exposure Check, or dropped, this goes RED.
    """
    text = read(VALIDATE)
    assert step0_precedes_remaining_exposure(text), (
        "validate-and-ship SKILL.md does not place '## Step 0: Security & "
        "Privacy Gate' before '### 1. Remaining Exposure Check' — the STOP gate "
        "could run after (or not run before) validation begins, silently "
        "shipping without a security review."
    )


def test_death__step0_order_decoys_are_detected_as_wrong() -> None:
    assert step0_precedes_remaining_exposure(_EXPOSURE_BEFORE_STEP0_DECOY) is False, (
        "The decoy with Remaining Exposure Check BEFORE Step 0 was reported as "
        "correctly ordered — the structural position guard has regressed."
    )
    assert step0_precedes_remaining_exposure(_MISSING_STEP0_DECOY) is False, (
        "The decoy with Step 0 entirely missing was reported as correctly "
        "ordered — a deleted gate must never pass this guard."
    )


def test_death__step0_unknown_is_never_treated_as_pass() -> None:
    """DC2 — if the 'unknown != pass' clause disappears, this goes RED."""
    step0 = _step0_section(read(VALIDATE)).lower()
    assert step0_declares_unknown_never_pass(step0), (
        "validate-and-ship SKILL.md Step 0 no longer states that an 'unknown' "
        "review result is never treated as pass — a timeout/partial/tool-"
        "error result could silently ship as if it passed review."
    )


def test_death__unknown_never_pass_decoys_are_detected() -> None:
    assert step0_declares_unknown_never_pass(_UNKNOWN_EVENTUALLY_PASS_DECOY) is False, (
        "The 'unknown eventually becomes a pass' decoy was reported as "
        "correctly declaring unknown != pass — the negation-window guard has "
        "regressed."
    )
    assert step0_declares_unknown_never_pass(_UNKNOWN_NEVER_PASS_REAL) is True, (
        "sanity: the real 'unknown is never treated as pass' phrasing should "
        "satisfy the predicate."
    )


def test_death__step0_fix_loop_requires_full_diff_rereview() -> None:
    """DC3 — if the fix loop narrows to fix-delta-only re-review, this goes
    RED."""
    step0 = _step0_section(read(VALIDATE)).lower()
    assert step0_requires_full_diff_refresh(step0), (
        "validate-and-ship SKILL.md Step 0 fix loop no longer requires "
        "re-reviewing the FULL diff (not just the fix delta) — a fix could "
        "silently introduce a new issue that is never re-checked."
    )


def test_death__full_diff_rereview_decoys_are_detected() -> None:
    assert step0_requires_full_diff_refresh(_FIX_DELTA_ONLY_DECOY) is False, (
        "The 'fix delta only, not the full diff' decoy (reversed order, "
        "opposite behavior) was reported as requiring full-diff re-review — "
        "the phrase-order guard has regressed."
    )
    assert step0_requires_full_diff_refresh(_FULL_DIFF_REAL) is True, (
        "sanity: the real 'full diff, not just the fix delta' phrasing should "
        "satisfy the predicate."
    )


def test_death__auto_mode_rejects_step0_uncertainty_and_blocks_progression() -> None:
    """DC4 — if auto mode's capability-absent/unknown/failing -> high-
    uncertainty reject clause disappears, OR the reject stops actually
    blocking progression past Step 0, this goes RED."""
    auto_section = _auto_mode_gate_section(read(VALIDATE)).lower()
    assert auto_gate_rejects_step0_uncertainty(auto_section), (
        "validate-and-ship SKILL.md Auto Mode Gate no longer ties Step 0 "
        "uncertainty (capability-absent / unknown / failing) to a blocking "
        "high-uncertainty `reject` that prevents proceeding past Step 0 — "
        "auto mode could silently ship despite an unresolved security gate."
    )


def test_death__auto_reject_label_only_decoy_is_detected_as_not_blocking() -> None:
    assert auto_gate_rejects_step0_uncertainty(_AUTO_LABEL_ONLY_DECOY) is False, (
        "The decoy that records a high-uncertainty `reject` label but still "
        "lets auto mode continue toward Remaining Exposure Check was reported as "
        "correctly blocking — the label-vs-behavior guard has regressed."
    )
    assert auto_gate_rejects_step0_uncertainty(_AUTO_BLOCKS_REAL) is True, (
        "sanity: the real clause (reject + 'must not proceed past step 0') "
        "should satisfy the predicate."
    )


def test_death__bootstrap_no_longer_names_deleted_security_skill() -> None:
    """DC5 — a dangling routing-graph node pointing at the deleted skill."""
    text = read(BOOTSTRAP)
    assert not names_deleted_security_skill(text), (
        "samsara-bootstrap SKILL.md still names `samsara:security-privacy-"
        "review` — the routing graph has a dangling node pointing at a "
        "deleted skill."
    )


def test_death__implement_no_longer_invokes_deleted_security_skill() -> None:
    """DC6 (implement half)."""
    text = read(IMPLEMENT)
    assert not names_deleted_security_skill(text), (
        "implement SKILL.md still instructs invoking `samsara:security-"
        "privacy-review` — a dangling transition target pointing at a "
        "deleted skill."
    )


def test_death__iteration_no_longer_invokes_deleted_security_skill() -> None:
    """DC6 (iteration half)."""
    text = read(ITERATION)
    assert not names_deleted_security_skill(text), (
        "iteration SKILL.md still instructs invoking `samsara:security-"
        "privacy-review` — a dangling transition target pointing at a "
        "deleted skill."
    )


def test_death__dangling_skill_decoy_is_detected_as_present() -> None:
    assert names_deleted_security_skill(_DANGLING_SKILL_DECOY) is True, (
        "The decoy containing 'invoke `samsara:security-privacy-review` "
        "skill.' was reported as not naming the deleted skill — the "
        "dangling-reference guard has regressed."
    )


def test_death__security_skill_directory_is_deleted() -> None:
    """The standalone skill directory must not exist after the fold-in —
    leaving it behind would give agents two competing gates to discover."""
    old_dir = ROOT / "skills" / "security-privacy-review"
    assert not old_dir.exists(), (
        "skills/security-privacy-review/ still exists after folding its gate "
        "into validate-and-ship — two competing security gates could be "
        "discovered by an agent, one of which is stale."
    )


# ---------------------------------------------------------------------------
# Unit tests (contract-bound, artifact-shape)
# ---------------------------------------------------------------------------


def test_unit__step0_section_covers_all_seven_semantics() -> None:
    """Contract source: documented artifact shape — validate-and-ship
    SKILL.md's Step 0 section must name all 7 concept-tokens from task-3.md
    Context list items 1-7. A behavior-preserving refactor (reword
    surrounding prose, reorder unrelated bullets) keeps every assertion
    green; dropping any one of the 7 semantics during compression turns the
    matching assertion red.
    """
    step0 = _step0_section(read(VALIDATE)).lower()

    # 1. diff computation + empty-diff/base-branch edge-case gate
    assert "git diff <base-branch>...head" in step0, (
        "Step 0 missing the diff computation command"
    )
    assert "empty diff" in step0, "Step 0 missing the empty-diff edge case"
    assert "base branch" in step0, (
        "Step 0 missing the cannot-determine-base-branch edge case"
    )

    # 2. no built-in capability -> visible degradation gate
    assert "visible degradation" in step0, (
        "Step 0 missing the visible-degradation (not silent skip) capability gate"
    )

    # 3. three-state result: pass / fail / unknown
    assert "**pass**" in step0, "Step 0 missing the Pass result state"
    assert "**fail**" in step0, "Step 0 missing the Fail result state"
    assert "**unknown**" in step0, "Step 0 missing the Unknown result state"

    # 4. fail -> severity list -> fix selection -> fix loop -> round counting safety valve
    for severity in ("critical", "high", "medium", "low"):
        assert severity in step0, f"Step 0 missing severity level: {severity}"
    assert "round counter" in step0, "Step 0 missing round counting"
    assert "round 3" in step0, "Step 0 missing the round-3 safety-valve threshold"

    # 5. accepted risk carries forward to ship manifest
    assert "accepted_risks" in step0, (
        "Step 0 missing the accepted-risk carry-forward to ship-manifest.yaml"
    )

    # 7. Red Flags: platform-agnostic
    assert "platform-agnostic" in step0, (
        "Step 0 missing the platform-agnostic Red Flags constraint"
    )


def test_unit__step0_auto_mode_gate_covers_sixth_semantic() -> None:
    """Contract source: documented artifact shape — semantic 6 (auto mode
    capability-absent/unknown/partial/failing -> reject; accepted risk
    invalid in auto mode) lives in the Auto Mode Gate section, not Step 0
    body."""
    auto_section = _auto_mode_gate_section(read(VALIDATE)).lower()
    assert "partial" in auto_section, (
        "Auto Mode Gate missing 'partial' as a Step 0 uncertainty trigger"
    )
    assert "invalid in auto mode" in auto_section, (
        "Auto Mode Gate no longer states accepted risk is invalid in auto "
        "mode for Step 0"
    )


def test_unit__bootstrap_routing_has_no_security_review_stage() -> None:
    """The ordered routing contract must not restore the folded stage."""
    text = read(BOOTSTRAP)
    assert "samsara:security-privacy-review" not in text, (
        "samsara-bootstrap routing still declares a standalone security review stage"
    )


def test_unit__bootstrap_routing_requires_iteration_entry_before_validate() -> None:
    """Every full workflow reaches validation through Iteration entry triage."""
    text = read(BOOTSTRAP).lower()
    assert (
        "research -> pre-thinking -> planning -> implement -> iteration -> validate-and-ship"
        in text
    ), "samsara-bootstrap routing has no iteration -> validate-and-ship path"
    assert "implement -> validate" not in text


def test_unit__bootstrap_routing_notes_step0_gate() -> None:
    """The ordered routing contract keeps security inside validation."""
    text = read(BOOTSTRAP)
    assert (
        "`validate-and-ship` includes the security and privacy Step 0 gate." in text
    ), (
        "Bootstrap routing does not state that validate-and-ship includes "
        "the security and privacy Step 0 gate"
    )


def test_unit__implement_transition_targets_iteration_entry() -> None:
    """Implement hands scars to Iteration before validation/security gates."""
    transition = _transition_section(read(IMPLEMENT))
    assert "samsara:iteration" in transition, (
        "implement SKILL.md Transition section no longer hands off to "
        "samsara:iteration Entry Triage"
    )
    assert "samsara:validate-and-ship" not in transition
    assert "samsara:security-privacy-review" not in transition, (
        "implement SKILL.md Transition section still names the deleted "
        "samsara:security-privacy-review skill"
    )


def test_unit__iteration_transition_targets_validate_and_ship() -> None:
    """Contract source: iteration SKILL.md '## Transition' section —
    documented workflow contract naming the next skill."""
    transition = _transition_section(read(ITERATION))
    assert "samsara:validate-and-ship" in transition, (
        "iteration SKILL.md Transition section no longer names "
        "samsara:validate-and-ship as the next skill"
    )
    assert "samsara:security-privacy-review" not in transition, (
        "iteration SKILL.md Transition section still names the deleted "
        "samsara:security-privacy-review skill"
    )


def test_unit__iteration_auto_mode_gate_proceed_targets_validate_and_ship() -> None:
    """Contract source: iteration SKILL.md '## Auto Mode Gate' section's
    `proceed` decision target (documented workflow contract)."""
    auto_section = _auto_mode_gate_section(read(ITERATION))
    m = re.search(r"`proceed`\s*—\s*invoke\s*`([^`]+)`", auto_section)
    assert m is not None, (
        "iteration SKILL.md Auto Mode Gate has no '`proceed` — invoke `<skill>`' line"
    )
    assert m.group(1) == "samsara:validate-and-ship", (
        f"iteration SKILL.md Auto Mode Gate 'proceed' target is "
        f"{m.group(1)!r}, expected 'samsara:validate-and-ship'"
    )
