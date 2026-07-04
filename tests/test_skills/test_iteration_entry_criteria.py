"""
Doc-contract guard for Task 5 (iteration 資料驅動進入 + implement 轉場改寫 +
UI 清單措辭修正): implement/SKILL.md's `## Transition` section replaces the
old unconditional "(A) 進入 Iteration (B) Skip" prompt with a data-driven,
three-state branch — cross-task pattern OR `signal_lost >= 5` triggers a
gated recommendation to enter iteration; criteria-not-met AND all scars
parseable defaults to a reversible, recorded skip; ANY scar parse failure
forces an `unknown` result that must never take the default-skip path.
iteration/SKILL.md gets a short reference note pointing at implement's
Transition section as the sole canonical home for the entry criteria/
threshold, instead of re-deriving its own copy (this feature has already
caught the same canonical-vs-duplicate trap three times — see task-5.md
Architecture Context).

These are DOC-PRESENCE / ARTIFACT-SHAPE tests (see .samsara/systemic-scars.
yaml `doc-instruction-no-code-enforcement`: nothing in this repo executes
this branching logic; the guard is that the DOCUMENT preserves the
criteria's semantics and polarity, not that an agent is mechanically forced
to obey them).

Death cases guarded (see task-5.md "Death Test Requirements"):
  DC1: implement SKILL.md's "parse failure -> unknown -> must not skip"
       clause disappears or is reworded to allow the default-skip path —
       parse failures (undercounted signal_lost) could silently be treated
       as "no signal, safe to skip".
  DC2: the default-skip branch's one-line reversible record
       ("signal_lost=N、無 cross-task pattern，已 skip iteration（回覆可推翻）")
       disappears — the most dangerous shape of silent skip: one that leaves
       no visible, reversible trace at all.
  DC3: the OLD unconditional "(A) 進入 Iteration ... (B) Skip ..." prompt
       re-appears alongside the NEW three-state criteria — two competing
       decision protocols in the same document is a self-contradiction, not
       a migration in progress.
  DC4: Progress Tracking's old "Never update one without the other" wording
       regresses back in, re-asserting index.yaml and TaskCreate/TaskUpdate
       as equally load-bearing when the task's Key Decision is that
       index.yaml alone is the source of truth.

Unit-test contract sources (see task-5.md "Unit Test Contract"):
  - implement SKILL.md's `## Transition` section: the three-state branch
    clauses (criteria-met -> gate, criteria-not-met+parseable -> default
    skip + record, parse-failure -> unknown + forced gate) — documented
    workflow contract.
  - implement SKILL.md's `## Progress Tracking` section: the
    truth-vs-projection sentence (documented artifact shape).
  - iteration SKILL.md's new entry-criteria reference note: points at
    implement's Transition section as canonical, without restating the
    literal threshold value (documented artifact shape).

All directional (require/prohibit) assertions are polarity-bound per
references/test-contract.md rule 2 (presence-not-polarity): every
directional predicate has a permanent wrong-direction decoy fixture proving
the SAME predicate function reports the decoy's claim as absent/present in
the opposite direction, using a clause-bounded (non-DOTALL) proximity window
that also stops at Chinese sentence punctuation (。！？), never a large
DOTALL window, per the project's stated test lesson.
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # tests/test_skills/ -> repo root
IMPLEMENT = ROOT / "skills" / "implement" / "SKILL.md"
ITERATION = ROOT / "skills" / "iteration" / "SKILL.md"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Section extractors
# ---------------------------------------------------------------------------


def _section(text: str, heading: str, ends: tuple[str, ...] = ("\n## ",)) -> str:
    start = text.find(heading)
    assert start != -1, f"missing section heading: {heading!r}"
    rest = text[start:]
    end = -1
    for marker in ends:
        idx = rest.find(marker, len(heading))
        if idx != -1 and (end == -1 or idx < end):
            end = idx
    return rest if end == -1 else rest[:end]


def _transition_section(text: str) -> str:
    return _section(text, "## Transition")


def _progress_tracking_section(text: str) -> str:
    return _section(
        text, "## Progress Tracking", ends=("\n## Execution Mode Selection",)
    )


def _entry_criteria_section(text: str) -> str:
    return _section(
        text,
        "## Iteration-Entry Criteria (Reference)",
        ends=("\n## Process",),
    )


# Clause-bounded gap: stops at ASCII and Chinese sentence punctuation plus
# newline. Never a DOTALL window (project test lesson: boundary bleed).
_CLAUSE_GAP = r"[^。！？.!?\n]"


def _normalize_ws(text: str) -> str:
    """Collapse all whitespace runs (including markdown line-wrap
    newlines) to a single space, for plain multi-word phrase presence
    checks that must survive a behavior-preserving line-wrap reflow. Not
    used by the clause-bounded proximity predicates above, which
    deliberately treat newlines as clause boundaries."""
    return re.sub(r"\s+", " ", text)


# ---------------------------------------------------------------------------
# Polarity-bound predicates (production assertions AND their permanent
# wrong-direction decoy tests call the SAME function).
# ---------------------------------------------------------------------------


def unknown_forbids_default_skip(text: str) -> bool:
    """True iff 'unknown' is tied (clause-bounded) to an explicit
    prohibition token (不准/must not/never), which is itself tied
    (clause-bounded) to 'skip'. False if 'unknown' and 'skip' co-occur
    WITHOUT an explicit prohibition — that is exactly the silent-skip
    regression this guards against."""
    pattern = (
        rf"unknown{_CLAUSE_GAP}{{0,80}}(不准|must not|never){_CLAUSE_GAP}{{0,30}}skip"
    )
    return re.search(pattern, text) is not None


def default_skip_has_reversible_record(text: str) -> bool:
    """True iff the default-skip branch requires printing a one-line record
    that names BOTH 'skip iteration' having happened (已 skip iteration) AND
    that it is reversible (可推翻), in that order and clause-bounded. False
    if the skip proceeds without ever naming the reversible record."""
    pattern = rf"已\s*skip iteration{_CLAUSE_GAP}{{0,40}}可推翻"
    return re.search(pattern, text) is not None


_OLD_ENTER_MARKER = "(A) 進入 Iteration — 審視 feature-level scar items"
_OLD_SKIP_MARKER = "(B) Skip — 直接進入"
_NEW_CRITERIA_MARKER = "判準成立"


def has_old_and_new_transition_protocol_conflict(text: str) -> bool:
    """True iff BOTH the OLD unconditional two-choice prompt markers AND the
    NEW three-state criteria marker are present in the same text — two
    competing decision protocols coexisting is a documentation
    self-contradiction. False if only one (or neither) is present."""
    has_old = _OLD_ENTER_MARKER in text and _OLD_SKIP_MARKER in text
    has_new = _NEW_CRITERIA_MARKER in text
    return has_old and has_new


def has_legacy_never_update_phrase(text: str) -> bool:
    """True iff the literal legacy phrase 'Never update one without the
    other' is present."""
    return "Never update one without the other" in text


# Permanent wrong-direction / hostile decoys.

_UNKNOWN_ALLOWS_SKIP_DECOY = (
    "任何 scar report 解析失敗 -> 結果為 unknown，仍然可以直接 skip iteration，"
    "維持預設行為繼續進入 validate-and-ship。"
)
_UNKNOWN_FORBIDS_SKIP_REAL = (
    "任何 scar report 解析失敗 -> 結果為 unknown，不准 skip（解析失敗代表 "
    "signal_lost 可能被少算，unknown 不等於不需要 iteration）。"
)

_SKIP_NO_RECORD_DECOY = (
    "判準不成立，且全部 scar 可解析 -> 已 skip iteration，直接進入 "
    "validate-and-ship，不需要額外的紀錄。"
)
_SKIP_WITH_RECORD_REAL = (
    "判準不成立，且全部 scar 可解析 -> 預設 skip，印出：signal_lost=3、"
    "無 cross-task pattern，已 skip iteration（回覆可推翻）。"
)

_OLD_AND_NEW_CONFLICT_DECOY = (
    "(A) 進入 Iteration — 審視 feature-level scar items（cross-task patterns, "
    "system-level rot）\n(B) Skip — 直接進入 Validate & Ship\n\n"
    "判準成立（cross-task pattern 或 signal_lost >= 5）時才建議進入 iteration。"
)
_ONLY_NEW_CRITERIA_REAL = (
    "判準成立（cross-task pattern 或 signal_lost >= 5）時才建議進入 iteration。"
)
_ONLY_OLD_PROMPT_REAL = (
    "(A) 進入 Iteration — 審視 feature-level scar items（cross-task patterns, "
    "system-level rot）\n(B) Skip — 直接進入 Validate & Ship"
)


# ---------------------------------------------------------------------------
# Death tests
# ---------------------------------------------------------------------------


def test_death__transition_unknown_forbids_default_skip() -> None:
    """DC1 — if the 'parse failure -> unknown -> must not skip' clause
    disappears, this goes RED."""
    transition = _transition_section(read(IMPLEMENT))
    assert unknown_forbids_default_skip(transition), (
        "implement SKILL.md Transition section no longer forbids the "
        "default-skip path when scar parse failures make the result "
        "unknown — an undercounted signal_lost could silently be treated "
        "as 'no signal, safe to skip'."
    )


def test_death__unknown_forbids_skip_decoys_are_detected() -> None:
    assert unknown_forbids_default_skip(_UNKNOWN_ALLOWS_SKIP_DECOY) is False, (
        "The decoy where 'unknown' still allows skipping was reported as "
        "forbidding the default-skip path — the polarity guard has "
        "regressed."
    )
    assert unknown_forbids_default_skip(_UNKNOWN_FORBIDS_SKIP_REAL) is True, (
        "sanity: the real '不准 skip' phrasing tied to unknown should "
        "satisfy the predicate."
    )


def test_death__transition_default_skip_leaves_reversible_record() -> None:
    """DC2 — if the default-skip branch's one-line reversible record
    disappears, this goes RED."""
    transition = _transition_section(read(IMPLEMENT))
    assert default_skip_has_reversible_record(transition), (
        "implement SKILL.md Transition section's default-skip branch no "
        "longer requires a visible, reversible one-line record — this is "
        "the most dangerous shape of silent skip: one with no recorded "
        "trace at all."
    )


def test_death__default_skip_record_decoys_are_detected() -> None:
    assert default_skip_has_reversible_record(_SKIP_NO_RECORD_DECOY) is False, (
        "The decoy where skip proceeds with 'no additional record needed' "
        "was reported as leaving a reversible record — the guard has "
        "regressed."
    )
    assert default_skip_has_reversible_record(_SKIP_WITH_RECORD_REAL) is True, (
        "sanity: the real 已 skip iteration（回覆可推翻）phrasing should "
        "satisfy the predicate."
    )


def test_death__transition_has_no_old_and_new_protocol_conflict() -> None:
    """DC3 — the OLD unconditional prompt must not coexist with the NEW
    three-state criteria in the shipped document."""
    transition = _transition_section(read(IMPLEMENT))
    assert not has_old_and_new_transition_protocol_conflict(transition), (
        "implement SKILL.md Transition section carries BOTH the OLD "
        "unconditional '(A) 進入 Iteration / (B) Skip' prompt AND the NEW "
        "data-driven criteria — two competing decision protocols is a "
        "documentation self-contradiction, not a valid migration state."
    )


def test_death__old_and_new_conflict_decoy_is_detected() -> None:
    assert (
        has_old_and_new_transition_protocol_conflict(_OLD_AND_NEW_CONFLICT_DECOY)
        is True
    ), (
        "The decoy carrying both the old unconditional prompt and the new "
        "criteria marker was reported as NOT conflicting — the "
        "contradiction guard has regressed."
    )
    assert (
        has_old_and_new_transition_protocol_conflict(_ONLY_NEW_CRITERIA_REAL) is False
    ), (
        "sanity: text with ONLY the new criteria marker (no old prompt) "
        "must not be flagged as conflicting."
    )
    assert (
        has_old_and_new_transition_protocol_conflict(_ONLY_OLD_PROMPT_REAL) is False
    ), (
        "sanity: text with ONLY the old prompt (no new criteria marker) "
        "must not be flagged as conflicting."
    )


def test_death__progress_tracking_has_no_legacy_never_update_phrase() -> None:
    """DC4 — the old 'Never update one without the other' wording must not
    regress back in."""
    progress = _progress_tracking_section(read(IMPLEMENT))
    assert not has_legacy_never_update_phrase(progress), (
        "implement SKILL.md Progress Tracking section still carries the "
        "legacy 'Never update one without the other' phrase — this "
        "re-asserts index.yaml and TaskCreate/TaskUpdate as equally "
        "load-bearing, contradicting the Key Decision that index.yaml "
        "alone is the source of truth and the UI projection is best-effort."
    )


def test_death__legacy_never_update_phrase_decoy_is_detected() -> None:
    decoy = (
        "some text\nAlways update both together. Never update one without the other.\n"
    )
    assert has_legacy_never_update_phrase(decoy) is True, (
        "The decoy containing the literal legacy phrase was reported as "
        "absent — the legacy-phrase detector has regressed."
    )
    assert has_legacy_never_update_phrase("index.yaml 是唯一真實狀態") is False, (
        "sanity: the new truth/projection sentence (no legacy phrase) must "
        "not be flagged as containing it."
    )


# ---------------------------------------------------------------------------
# Unit tests (contract-bound, artifact-shape)
# ---------------------------------------------------------------------------


def test_unit__transition_criteria_met_branch_names_threshold_and_provenance() -> None:
    """Contract source: implement SKILL.md Transition section's 判準成立
    branch — documented workflow contract naming the two OR-ed trigger
    conditions and the threshold's provenance. A behavior-preserving
    refactor (reword surrounding prose) keeps this green; dropping the
    cross-task-pattern condition, the numeric threshold, or the provenance
    note turns it red.
    """
    transition = _transition_section(read(IMPLEMENT))
    flat = _normalize_ws(transition)

    idx_criteria = transition.find("判準成立")
    assert idx_criteria != -1, "Transition section has no 判準成立 branch marker"

    # The threshold clause must name BOTH trigger conditions.
    assert "cross-task pattern" in flat, (
        "Transition missing the cross-task pattern trigger condition"
    )
    assert "signal_lost >= 5" in flat, (
        "Transition missing the signal_lost >= 5 trigger condition"
    )

    # Threshold provenance must be named (Key Decision: rough historical
    # estimate, not a calibrated constant).
    assert "historical iteration-log data" in flat, (
        "Transition no longer names the threshold's historical-estimate provenance"
    )
    assert "not a calibrated constant" in flat, (
        "Transition no longer states the threshold is uncalibrated"
    )


def test_unit__transition_default_skip_branch_proceeds_directly_without_gate() -> None:
    """Contract source: implement SKILL.md Transition section's
    判準不成立 branch — documented workflow contract: this branch is
    deterministic (does not invoke the gate) and proceeds straight to
    validate-and-ship."""
    transition = _transition_section(read(IMPLEMENT))

    idx_not_met = transition.find("判準不成立")
    idx_parse_fail = transition.find("解析失敗")
    assert idx_not_met != -1, "Transition section has no 判準不成立 branch marker"
    assert idx_parse_fail != -1, (
        "Transition section has no 解析失敗 (parse failure) branch marker"
    )
    # Structural order: the deterministic-skip branch must be documented
    # BEFORE the parse-failure branch (matches the three-state list order:
    # criteria-met, criteria-not-met, parse-failure).
    assert idx_not_met < idx_parse_fail, (
        "Transition section documents the parse-failure branch before the "
        "default-skip branch — the three-state list order has drifted"
    )

    branch_text = transition[idx_not_met:idx_parse_fail]
    assert "deterministic" in branch_text, (
        "default-skip branch no longer states it is deterministic (no gate)"
    )
    assert "samsara:validate-and-ship" in branch_text, (
        "default-skip branch no longer proceeds directly to samsara:validate-and-ship"
    )


def test_unit__transition_unknown_branch_lists_parse_failures_and_forces_gate() -> None:
    """Contract source: implement SKILL.md Transition section's parse-
    failure (unknown) branch — documented workflow contract: it must list
    parse failures explicitly and force a gated choice between the two
    next skills, never fall back to the default-skip branch."""
    transition = _transition_section(read(IMPLEMENT))
    idx_parse_fail = transition.find("解析失敗")
    assert idx_parse_fail != -1, "Transition section has no 解析失敗 branch marker"

    branch_text = transition[idx_parse_fail:]
    assert "列出每個 parse" in branch_text, (
        "unknown branch no longer requires listing each parse failure"
    )
    assert "systemic_ref" in branch_text, (
        "unknown branch no longer names the dangling systemic_ref case"
    )
    assert "samsara:iteration" in branch_text, (
        "unknown branch no longer names samsara:iteration as a gated option"
    )
    assert "samsara:validate-and-ship" in branch_text, (
        "unknown branch no longer names samsara:validate-and-ship as a gated option"
    )


def test_unit__progress_tracking_states_truth_vs_projection_directionally() -> None:
    """Contract source: implement SKILL.md Progress Tracking section's
    truth/projection sentence — documented artifact shape naming
    index.yaml as sole source of truth and TaskCreate/TaskUpdate as a
    best-effort projection, with the DIRECTIONAL claim that only the
    truth's staleness is a process error."""
    progress = _progress_tracking_section(read(IMPLEMENT))

    assert "唯一真實狀態" in progress, (
        "Progress Tracking no longer names index.yaml as the sole source of truth"
    )
    assert "UI 投影" in progress, (
        "Progress Tracking no longer names TaskCreate/TaskUpdate as a UI projection"
    )

    # Directional pairing: projection staleness is explicitly NOT an error;
    # index.yaml staleness explicitly IS.
    assert re.search(r"投影未更新不構成流程錯誤", progress), (
        "Progress Tracking no longer states that a stale UI projection is "
        "NOT a process error"
    )
    assert re.search(r"index\.yaml 未更新是", progress), (
        "Progress Tracking no longer states that a stale index.yaml IS the "
        "process error"
    )


def test_unit__iteration_entry_criteria_reference_names_implement_transition_as_canonical() -> (
    None
):
    """Contract source: iteration SKILL.md's new '## Iteration-Entry
    Criteria (Reference)' section — documented artifact shape: it must name
    implement/SKILL.md's Transition section as the canonical location, and
    must NOT restate the literal threshold value (avoiding the two-place
    duplication trap named in task-5.md Architecture Context)."""
    entry_ref = _entry_criteria_section(read(ITERATION))

    assert "skills/implement/SKILL.md" in entry_ref, (
        "iteration SKILL.md's entry-criteria reference no longer names "
        "implement/SKILL.md as the canonical location"
    )
    assert "Transition" in entry_ref, (
        "iteration SKILL.md's entry-criteria reference no longer points at "
        "the Transition section specifically"
    )
    # Anti-duplication: the literal threshold value must not be re-derived
    # here — only implement's Transition section should carry it.
    assert "signal_lost >= 5" not in entry_ref, (
        "iteration SKILL.md's entry-criteria reference restates the "
        "literal 'signal_lost >= 5' threshold instead of pointing at "
        "implement's Transition section — this recreates the exact "
        "two-place duplication trap this feature has already caught three "
        "times"
    )


def test_unit__auto_mode_gate_workflow_prompt_reflects_conditional_gating() -> None:
    """Contract source: implement SKILL.md Auto Mode Gate section's
    `workflow_prompt` sources bullet — documented artifact shape. Must
    describe the completion gate as conditionally invoked (only on
    criteria-met or unknown), not unconditionally invoked on every
    completion, while still preserving the pre-existing execution-mode
    selection tokens the auto-mode protocol test suite locks
    (implementation execution-mode selection / Subagent parallel / Inline
    sequential)."""
    from tests.test_auto_mode.test_protocol_helpers import section

    auto_section = section(read(IMPLEMENT), "Auto Mode Gate")
    flat = _normalize_ws(auto_section)

    assert "only" in flat and "invoked when" in flat, (
        "Auto Mode Gate workflow_prompt no longer describes the completion "
        "gate as conditionally invoked"
    )
    assert "deterministic default-skip never invokes this gate" in flat, (
        "Auto Mode Gate workflow_prompt no longer states that the "
        "deterministic default-skip path never invokes the gate"
    )
    # Pre-existing tokens locked by tests/test_auto_mode/ must survive.
    assert "implementation execution-mode selection" in flat
    assert "Subagent parallel" in flat
    assert "Inline sequential" in flat
