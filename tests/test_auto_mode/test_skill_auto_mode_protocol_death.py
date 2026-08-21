"""
Death tests for Task 4 (Auto Mode Gate 去重 — canonical 入
references/auto-mode.md, 6 skills 留指針).

Before this task, each of the 6 workflow skills (research, pre-thinking,
planning, implement, iteration, validate-and-ship) repeated ~80% identical
dispatch/append-only/decision-value boilerplate in its own "## Auto Mode
Gate" section. This task moves the general protocol into
`references/auto-mode.md`'s new "## Stage Gate Protocol" section and
shrinks each skill's section to a pointer + stage-specific content.

Death cases guarded here (see task-4.md "Death Test Requirements"):
  DC1: references/auto-mode.md's Stage Gate Protocol is missing the
       semantics of any of the four decision values (proceed / revise /
       reject / accept_gap) — every skill would silently lose the
       definition it points at.
  DC2: validate-and-ship's stage-specific inline behavior (the double
       decision-trace check, and the Step 0 auto-overrides list) is
       dropped during the pointer-ization.
  DC3: iteration's pointer section drops the "gate covers all decision
       points" list (triage / blocked-fix / round continuation / safety
       valve).
  DC4 (anti-duplication): a skill's Auto Mode Gate section re-embeds the
       canonical decision-value definitions in full instead of pointing at
       them — the exact rot this task exists to remove could silently grow
       back.

These are DOC-PRESENCE / ARTIFACT-SHAPE tests (see .samsara/systemic-scars.
yaml `doc-vs-runtime-obedience`: nothing here executes the gate; the guard
is that the DOCUMENT still names the required semantics).

Polarity-bound assertions follow references/test-contract.md rule 2
(presence-not-polarity): every directional predicate used for a death case
has a permanent wrong-direction decoy fixture, and every proximity check
uses a clause-bounded (non-DOTALL) window per the project's stated test
lesson.
"""

import re

from tests.test_auto_mode.test_protocol_helpers import (
    AUTO_MODE_REFERENCE,
    EARLY_STAGE_SKILLS,
    LATER_STAGE_SKILLS,
    REQUIRED_WORKFLOW_STAGES,
    read,
    section,
)


# ---------------------------------------------------------------------------
# Polarity-bound predicates (production assertions AND their permanent
# wrong-direction decoy tests call the SAME function).
# ---------------------------------------------------------------------------


def protocol_defines_all_four_decision_values(protocol_lower: str) -> bool:
    """True iff the Stage Gate Protocol section names all four decision
    values with their backticked form. False if any one is missing."""
    return all(
        token in protocol_lower
        for token in ("`proceed`", "`revise`", "`reject`", "`accept_gap`")
    )


def protocol_proceed_means_continue(protocol_lower: str) -> bool:
    """True iff `proceed` is tied (clause-bounded) to 'continue'."""
    return re.search(r"`proceed`[^.!?\n]{0,80}continue", protocol_lower) is not None


def protocol_revise_means_rerun_same_gate(protocol_lower: str) -> bool:
    """True iff `revise` is tied (clause-bounded) to re-running the SAME
    gate on a revised artifact — not merely 'something changes'."""
    return (
        re.search(r"`revise`[^.!?\n]{0,120}(revised|re-runs)", protocol_lower)
        is not None
    )


def protocol_reject_means_stop(protocol_lower: str) -> bool:
    """True iff `reject` is tied (clause-bounded) to stopping the run."""
    return re.search(r"`reject`[^.!?\n]{0,80}stop", protocol_lower) is not None


def protocol_accept_gap_keeps_gap_visible(protocol_lower: str) -> bool:
    """True iff `accept_gap` is tied (clause-bounded) to keeping the gap
    visible rather than silently dropping it."""
    return (
        re.search(r"`accept_gap`[^.!?\n]{0,120}(gap|visible)", protocol_lower)
        is not None
    )


def has_double_trace_check(auto_section_lower: str) -> bool:
    """True iff the section names BOTH a pre-final-decision trace check
    ('prior gate entries') AND a post-final-append trace check ('after
    appending the final validation decision'). Either alone is not the
    double check the task requires."""
    return (
        "prior gate entries" in auto_section_lower
        and re.search(
            r"after (?:the gatekeeper )?append(?:s|ing) the final validation decision",
            auto_section_lower,
        )
        is not None
    )


def has_step0_auto_overrides(auto_section_lower: str) -> bool:
    """True iff all 6 Step 0 auto-override decision points are named."""
    required = (
        "empty diff",
        "base branch",
        "no built-in security review capability",
        "unknown result",
        "fail result",
        "accepted risk",
    )
    return all(term in auto_section_lower for term in required)


def has_iteration_decision_point_list(auto_section_lower: str) -> bool:
    """True iff all 4 iteration-internal decision points are named."""
    required = (
        "triage",
        "blocked-fix handling",
        "round continuation",
        "safety valve",
    )
    return all(term in auto_section_lower for term in required)


# Verbatim canonical decision-value definitions (references/auto-mode.md
# Stage Gate Protocol). Any ONE of these appearing verbatim in a skill's own
# Auto Mode Gate section is a sign the canonical text was re-embedded rather
# than pointed at.
_CANONICAL_DECISION_DEFINITIONS = (
    "continue to whatever comes next, as a human confirmation would",
    "the artifact must be revised, then the same gate re-runs on it",
    "no later gate may treat a `reject` as `proceed`",
    "the gap must stay visible downstream",
)


def reembeds_canonical_decision_definitions(auto_section_lower: str) -> bool:
    """True iff a skill's Auto Mode Gate section contains ANY canonical
    decision-value definition VERBATIM — a sign the section re-embeds the
    full canonical definitions instead of pointing at them."""
    return any(
        definition in auto_section_lower
        for definition in _CANONICAL_DECISION_DEFINITIONS
    )


# Permanent wrong-direction / hostile decoys.

_MISSING_ACCEPT_GAP_DECOY = (
    "- `proceed` — continue.\n"
    "- `revise` — the artifact must be revised, then the same gate runs "
    "again.\n"
    "- `reject` — stop the run.\n"
)

_PROCEED_NO_CONTINUE_DECOY = (
    "`proceed` — the stage logs the decision and waits for the next session."
)
_REVISE_NO_RERUN_DECOY = (
    "`revise` — the workflow notes the concern and moves on regardless."
)
_REJECT_NO_STOP_DECOY = "`reject` — the workflow records disapproval but keeps running."
_ACCEPT_GAP_SILENT_DECOY = (
    "`accept_gap` — the stage continues and the note is discarded once read."
)

_SINGLE_TRACE_CHECK_DECOY = (
    "before the final validation decision, validate prior gate entries in "
    "the append-only decision trace. the gatekeeper appends the final "
    "decision and the run completes."
)
_DOUBLE_TRACE_CHECK_REAL = (
    "before the final validation decision, validate prior gate entries in "
    "the append-only decision trace. after appending the final validation "
    "decision, run the trace check again."
)

_STEP0_OVERRIDES_MISSING_ACCEPTED_RISK_DECOY = (
    "step 0 auto overrides: empty diff -> reject unless expected; base "
    "branch cannot be determined -> reject; no built-in security review "
    "capability -> reject; unknown result -> reject; fail result -> revise "
    "or reject."
)
_STEP0_OVERRIDES_COMPLETE_REAL = (
    "step 0 auto overrides: empty diff -> reject unless expected; base "
    "branch cannot be determined -> reject; no built-in security review "
    "capability -> reject; unknown result -> reject; fail result -> revise "
    "or reject; accepted risk -> invalid, always reject."
)

_ITERATION_MISSING_SAFETY_VALVE_DECOY = (
    "decision points: triage of remaining items, blocked-fix handling, and "
    "round continuation after signal_lost changes."
)
_ITERATION_COMPLETE_REAL = (
    "decision points: triage of remaining items, blocked-fix handling, "
    "round continuation after signal_lost changes, and safety valve "
    "decisions when round limits trigger."
)

_REEMBED_DECOY = (
    "`revise` — the artifact must be revised, then the same gate re-runs "
    "on it; see also references/auto-mode.md."
)
_POINTER_ONLY_REAL = (
    "canonical protocol: references/auto-mode.md stage gate protocol — "
    "dispatch, the append-only decision log, and what proceed/revise/"
    "reject/accept_gap mean all live there."
)


# ---------------------------------------------------------------------------
# DC1 — canonical Stage Gate Protocol completeness
# ---------------------------------------------------------------------------


def _stage_gate_protocol() -> str:
    return section(read(AUTO_MODE_REFERENCE), "Stage Gate Protocol").lower()


def test_death__stage_gate_protocol_defines_all_four_decision_values() -> None:
    protocol = _stage_gate_protocol()
    assert protocol_defines_all_four_decision_values(protocol), (
        "SILENT FAILURE [AUTO-MODE-DEDUP-1]: references/auto-mode.md's Stage "
        "Gate Protocol no longer names all four decision values "
        "(proceed/revise/reject/accept_gap) — every one of the 6 skills "
        "pointing at it would silently lose that definition at once."
    )


def test_death__missing_decision_value_decoy_is_detected() -> None:
    assert (
        protocol_defines_all_four_decision_values(_MISSING_ACCEPT_GAP_DECOY.lower())
        is False
    ), (
        "The decoy missing `accept_gap` was reported as defining all four "
        "decision values — the completeness guard has regressed."
    )


def test_death__stage_gate_protocol_proceed_means_continue() -> None:
    protocol = _stage_gate_protocol()
    assert protocol_proceed_means_continue(protocol), (
        "SILENT FAILURE [AUTO-MODE-DEDUP-2]: Stage Gate Protocol's `proceed` "
        "is no longer tied to continuing the workflow — a skill could "
        "record `proceed` and every stage pointing at this definition would "
        "silently stop meaning 'go on'."
    )


def test_death__proceed_no_continue_decoy_is_detected() -> None:
    assert protocol_proceed_means_continue(_PROCEED_NO_CONTINUE_DECOY) is False, (
        "The decoy where `proceed` merely 'waits for the next session' was "
        "reported as meaning continue — the polarity guard has regressed."
    )


def test_death__stage_gate_protocol_revise_means_rerun_same_gate() -> None:
    protocol = _stage_gate_protocol()
    assert protocol_revise_means_rerun_same_gate(protocol), (
        "SILENT FAILURE [AUTO-MODE-DEDUP-3]: Stage Gate Protocol's `revise` "
        "no longer requires the SAME gate to re-run on the revised artifact "
        "— a stage could treat `revise` as a no-op and silently proceed "
        "anyway."
    )


def test_death__revise_no_rerun_decoy_is_detected() -> None:
    assert protocol_revise_means_rerun_same_gate(_REVISE_NO_RERUN_DECOY) is False, (
        "The decoy where `revise` just 'moves on regardless' was reported "
        "as requiring a re-run — the polarity guard has regressed."
    )


def test_death__stage_gate_protocol_reject_means_stop() -> None:
    protocol = _stage_gate_protocol()
    assert protocol_reject_means_stop(protocol), (
        "SILENT FAILURE [AUTO-MODE-DEDUP-4]: Stage Gate Protocol's `reject` "
        "no longer stops the auto run — a rejected gate could silently let "
        "the workflow continue as if nothing happened."
    )


def test_death__reject_no_stop_decoy_is_detected() -> None:
    assert protocol_reject_means_stop(_REJECT_NO_STOP_DECOY) is False, (
        "The decoy where `reject` 'keeps running' was reported as stopping "
        "the run — the polarity guard has regressed."
    )


def test_death__stage_gate_protocol_accept_gap_keeps_gap_visible() -> None:
    protocol = _stage_gate_protocol()
    assert protocol_accept_gap_keeps_gap_visible(protocol), (
        "SILENT FAILURE [AUTO-MODE-DEDUP-5]: Stage Gate Protocol's "
        "`accept_gap` no longer requires the gap to stay visible downstream "
        "— an accepted gap could be silently forgotten by the next stage."
    )


def test_death__accept_gap_silent_decoy_is_detected() -> None:
    assert protocol_accept_gap_keeps_gap_visible(_ACCEPT_GAP_SILENT_DECOY) is False, (
        "The decoy where the accepted gap note 'is discarded once read' was "
        "reported as keeping the gap visible — the polarity guard has "
        "regressed."
    )


# ---------------------------------------------------------------------------
# DC2 — validate-and-ship stage-specific inline behavior survives
# ---------------------------------------------------------------------------


def _validate_auto_section_lower() -> str:
    return section(
        read(LATER_STAGE_SKILLS["validate-and-ship"]), "Auto Mode Gate"
    ).lower()


def test_death__validate_and_ship_keeps_double_decision_trace_check() -> None:
    auto_section = _validate_auto_section_lower()
    assert has_double_trace_check(auto_section), (
        "SILENT FAILURE [AUTO-MODE-DEDUP-6]: validate-and-ship's Auto Mode "
        "Gate no longer runs BOTH the pre-final-decision trace check and "
        "the post-final-append trace check — a malformed final entry could "
        "silently ship without ever being caught."
    )


def test_death__single_trace_check_decoy_is_detected_as_incomplete() -> None:
    assert has_double_trace_check(_SINGLE_TRACE_CHECK_DECOY) is False, (
        "The decoy with only the pre-final trace check (no post-append "
        "re-check) was reported as having the double check — the guard has "
        "regressed."
    )
    assert has_double_trace_check(_DOUBLE_TRACE_CHECK_REAL) is True, (
        "sanity: the real double-trace-check phrasing should satisfy the predicate."
    )


def test_death__validate_and_ship_keeps_step0_auto_overrides() -> None:
    auto_section = _validate_auto_section_lower()
    assert has_step0_auto_overrides(auto_section), (
        "SILENT FAILURE [AUTO-MODE-DEDUP-7]: validate-and-ship's Auto Mode "
        "Gate dropped one or more of the 6 Step 0 auto-override decision "
        "points during pointer-ization — an auto run could silently fall "
        "back to no defined behavior for that case."
    )


def test_death__step0_overrides_missing_accepted_risk_decoy_is_detected() -> None:
    assert (
        has_step0_auto_overrides(_STEP0_OVERRIDES_MISSING_ACCEPTED_RISK_DECOY) is False
    ), (
        "The decoy missing the 'accepted risk' override was reported as "
        "complete — the coverage guard has regressed."
    )
    assert has_step0_auto_overrides(_STEP0_OVERRIDES_COMPLETE_REAL) is True, (
        "sanity: the real complete override list should satisfy the predicate."
    )


# ---------------------------------------------------------------------------
# DC3 — iteration's full decision-point list survives
# ---------------------------------------------------------------------------


def test_death__iteration_keeps_all_four_decision_points() -> None:
    auto_section = section(
        read(LATER_STAGE_SKILLS["iteration"]), "Auto Mode Gate"
    ).lower()
    assert has_iteration_decision_point_list(auto_section), (
        "SILENT FAILURE [AUTO-MODE-DEDUP-8]: iteration's Auto Mode Gate no "
        "longer names all 4 internal decision points (triage / blocked-fix "
        "handling / round continuation / safety valve) — an auto run could "
        "silently skip the gate for whichever point is missing."
    )


def test_death__iteration_missing_safety_valve_decoy_is_detected() -> None:
    assert (
        has_iteration_decision_point_list(_ITERATION_MISSING_SAFETY_VALVE_DECOY)
        is False
    ), (
        "The decoy missing 'safety valve' was reported as covering all "
        "iteration decision points — the coverage guard has regressed."
    )
    assert has_iteration_decision_point_list(_ITERATION_COMPLETE_REAL) is True, (
        "sanity: the real complete decision-point list should satisfy the predicate."
    )


# ---------------------------------------------------------------------------
# DC4 — anti-duplication: no skill re-embeds canonical decision definitions
# ---------------------------------------------------------------------------


def test_death__no_skill_reembeds_canonical_decision_definitions() -> None:
    for stage, path in {**EARLY_STAGE_SKILLS, **LATER_STAGE_SKILLS}.items():
        auto_section = section(read(path), "Auto Mode Gate").lower()
        assert not reembeds_canonical_decision_definitions(auto_section), (
            "SILENT FAILURE [AUTO-MODE-DEDUP-9]: "
            f"{stage}'s Auto Mode Gate re-embeds the canonical `revise` "
            "decision-value definition verbatim instead of pointing at "
            "references/auto-mode.md — the exact duplication this task "
            "removed could silently grow back and diverge from canonical "
            "over time."
        )


def test_death__reembed_decoy_is_detected_as_present() -> None:
    assert reembeds_canonical_decision_definitions(_REEMBED_DECOY.lower()) is True, (
        "The decoy that pastes the full canonical `revise` definition "
        "verbatim was reported as NOT re-embedding — the anti-duplication "
        "guard has regressed."
    )
    assert (
        reembeds_canonical_decision_definitions(_POINTER_ONLY_REAL.lower()) is False
    ), (
        "sanity: a real pointer-only section (no verbatim canonical "
        "definition) should not be flagged as re-embedding."
    )


# ---------------------------------------------------------------------------
# Existing coverage guards kept from before Task 4 (unaffected by
# pointer-ization — the stage set itself did not change).
# ---------------------------------------------------------------------------


class TestResearchExecutionModeDeath:
    def test_research_requires_workflow_mode_selection_before_interrogation(self):
        text = read(EARLY_STAGE_SKILLS["research"])
        mode_section = section(text, "Step 0: Execution Mode Selection")

        required = (
            "Before Step 1",
            "`human-in-the-loop`",
            "`auto`",
            "Execution mode:",
            "If the user does not choose",
            "Execution mode? Choose `human-in-the-loop` or `auto`.",
            "1-kickoff.md",
        )
        for term in required:
            assert term in mode_section, (
                "SILENT FAILURE [AUTO-MODE-1]: Research can interrogate "
                f"without an explicit execution mode contract. Missing {term!r}."
            )

    def test_research_marks_persistent_config_out_of_scope(self):
        text = read(EARLY_STAGE_SKILLS["research"])
        mode_section = section(text, "Step 0: Execution Mode Selection").lower()

        assert "persistent config" in mode_section
        assert "out of scope" in mode_section


class TestEarlyWorkflowAutoGateDeath:
    def test_early_stage_auto_gates_point_to_canonical_protocol(self):
        for stage, path in EARLY_STAGE_SKILLS.items():
            auto_section = section(read(path), "Auto Mode Gate")

            assert "references/auto-mode.md" in auto_section, (
                "SILENT FAILURE [AUTO-MODE-2]: "
                f"{stage}'s Auto Mode Gate no longer points at the "
                "canonical Stage Gate Protocol — an agent reading only this "
                "skill could re-invent, or silently skip, the dispatch/log "
                "contract."
            )
            assert "Stage Gate Protocol" in auto_section, (
                f"{stage}'s Auto Mode Gate does not name the Stage Gate "
                "Protocol section it points at."
            )

    def test_early_stage_auto_gates_name_workflow_prompt_source(self):
        for stage, path in EARLY_STAGE_SKILLS.items():
            auto_section = section(read(path), "Auto Mode Gate")

            assert "workflow_prompt" in auto_section, (
                "SILENT FAILURE [AUTO-MODE-4]: "
                f"{stage}'s Auto Mode Gate no longer names which prompt is "
                "this stage's workflow_prompt."
            )

    def test_early_stage_auto_gates_do_not_pause_for_human_confirmation(self):
        for stage, path in EARLY_STAGE_SKILLS.items():
            auto_section = section(read(path), "Auto Mode Gate")

            prohibited = (
                "AskUserQuestion",
                "request_user_input",
                "human confirmation",
                "user confirmation",
            )
            found = [term for term in prohibited if term in auto_section]
            assert not found, (
                "SILENT FAILURE [AUTO-MODE-5]: "
                f"{stage} auto gate can still pause for human input: {found}."
            )


class TestLaterWorkflowAutoGateDeath:
    def test_later_stage_auto_gates_point_to_canonical_protocol(self):
        for stage, path in LATER_STAGE_SKILLS.items():
            auto_section = section(read(path), "Auto Mode Gate")

            assert "references/auto-mode.md" in auto_section, (
                "SILENT FAILURE [AUTO-MODE-6]: "
                f"{stage}'s Auto Mode Gate no longer points at the "
                "canonical Stage Gate Protocol."
            )
            assert "Stage Gate Protocol" in auto_section, (
                f"{stage}'s Auto Mode Gate does not name the Stage Gate "
                "Protocol section it points at."
            )

    def test_later_stage_auto_gates_name_workflow_prompt_source(self):
        for stage, path in LATER_STAGE_SKILLS.items():
            auto_section = section(read(path), "Auto Mode Gate")

            assert "workflow_prompt" in auto_section, (
                "SILENT FAILURE [AUTO-MODE-7]: "
                f"{stage}'s Auto Mode Gate no longer names this stage's "
                "workflow_prompt source."
            )

    def test_later_stage_auto_gates_do_not_pause_for_human_confirmation(self):
        for stage, path in LATER_STAGE_SKILLS.items():
            auto_section = section(read(path), "Auto Mode Gate")

            prohibited = (
                "AskUserQuestion",
                "request_user_input",
                "human confirmation",
                "user confirmation",
                "human accept",
                "human accepted",
            )
            found = [term for term in prohibited if term in auto_section]
            assert not found, (
                "SILENT FAILURE [AUTO-MODE-8]: "
                f"{stage} auto gate can still pause for human input: {found}."
            )

    def test_security_unknown_records_high_uncertainty_reject(self):
        auto_section = section(
            read(LATER_STAGE_SKILLS["validate-and-ship"]), "Auto Mode Gate"
        )

        assert "high-uncertainty `reject`" in auto_section
        assert "unknown" in auto_section
        assert "must not proceed past Step 0" in auto_section

    def test_validate_and_ship_checks_auto_decisions_before_completion(self):
        auto_section = section(
            read(LATER_STAGE_SKILLS["validate-and-ship"]), "Auto Mode Gate"
        )

        assert "auto-decisions.md" in auto_section
        assert "completion" in auto_section
        assert "must fail validation" in auto_section

    def test_implement_auto_gate_covers_execution_mode_selection(self):
        auto_section = section(read(LATER_STAGE_SKILLS["implement"]), "Auto Mode Gate")

        assert "implementation strategy selection" in auto_section
        assert "implementation.strategy" in auto_section
        assert "Subagent parallel" in auto_section
        assert "Inline sequential" in auto_section

    def test_iteration_auto_gate_covers_internal_decision_points(self):
        auto_section = section(read(LATER_STAGE_SKILLS["iteration"]), "Auto Mode Gate")

        for term in (
            "triage",
            "blocked-fix handling",
            "round continuation",
            "safety valve",
        ):
            assert term in auto_section

    def test_security_auto_gate_overrides_internal_human_fallbacks(self):
        auto_section = section(
            read(LATER_STAGE_SKILLS["validate-and-ship"]), "Auto Mode Gate"
        )

        for term in (
            "empty diff",
            "base branch",
            "no built-in security review capability",
            "unknown result",
            "accepted risk",
        ):
            assert term in auto_section

    def test_validation_auto_gate_checks_trace_after_final_append(self):
        auto_section = section(
            read(LATER_STAGE_SKILLS["validate-and-ship"]), "Auto Mode Gate"
        )

        assert "prior gate entries" in auto_section
        assert (
            "after the Gatekeeper appends the final validation decision" in auto_section
        )


class TestPrimaryEvaluatorCoverageDeath:
    def test_auto_mode_evaluator_covers_every_required_workflow_stage(self):
        covered = set(EARLY_STAGE_SKILLS) | set(LATER_STAGE_SKILLS)

        assert covered == REQUIRED_WORKFLOW_STAGES, (
            "SILENT FAILURE [AUTO-EVALUATOR-1]: primary evaluator stage list drifted. "
            f"Missing: {sorted(REQUIRED_WORKFLOW_STAGES - covered)}; "
            f"Extra: {sorted(covered - REQUIRED_WORKFLOW_STAGES)}"
        )
