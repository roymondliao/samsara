"""Evaluator for the implement ORCHESTRATION skill's Test Contract Gate (Task 3).

`skills/implement/SKILL.md` sequences every implementer run: STEP 0 → death tests →
unit tests → scar report. It is the orchestration surface, so it must stay LEAN —
it POINTS to `references/test-contract.md` rather than re-pasting the catalog. But
lean must not mean hollow: the skill must make a Test Contract Gate mandatory and
place it BEFORE unit tests are written, name BOTH red-flag poles (over-fit AND
silent-green), state that unit tests assert contracts not implementation details,
and preserve the load-bearing death-test-first ordering.

Death tests run BEFORE the unit tests and target SILENT failure paths — the ones
that stay GREEN while the orchestration is hollow:

  DC1 The skill sequences "Write unit tests" with NO Test Contract Gate before it →
      implementers write brittle/tautological unit tests that pass review.
  DC2 The skill guards the over-fit pole (brittleness) but NOT the silent-green
      pole → tautological tests stay green when behavior breaks.
  DC3 The skill omits references/test-contract.md from Support Files → the gate
      points at a protocol the dispatched implementer cannot find (dangling gate).
  DC4 The gate is added but placed AFTER unit tests → worthless; the tautological
      test is already on disk by the time the gate runs.
  DC5 The Test Contract Gate displaces the death-test-first rule → death tests no
      longer come first; the load-bearing ordering silently rots.
  DC-DESYNC A "three"/"三問" STEP 0 count survives after task-2 made STEP 0 four →
      the skill's digraph + execution order desync from the agent.
  DC-DECOY The new SKILL-surface concept tokens are green-by-construction (key on
      the bare word "gate") → they can never go red.

Each death test names the silent-failure mode it pins; that failure mode IS this
death test's contract, so (per the protocol) it is allowed to be exact here.
"""

from __future__ import annotations

from pathlib import Path

from tests.test_contract_bound_tests._contract_tokens import (
    BRITTLENESS_FILTER,
    CONTRACT_PRINCIPLE_AND_POINTER,
    CONTRACT_REFERENCE_SUPPORT_FILE,
    DEATH_TEST_FIRST,
    GATE_BEFORE_UNIT,
    SILENT_GREEN_GUARD,
    STEP_CONTRACT_GATE,
    STEP_DEATH_TEST,
    STEP_UNIT_TEST,
    TEST_CONTRACT_GATE,
)
from tests.test_contract_bound_tests._token_lib import (
    concept_present,
    concepts_covered_by,
    missing_concepts,
    numbered_steps,
    pinned_heading_offenders,
    step_index_of_concept,
)

ROOT = Path(__file__).resolve().parents[2]
# Intentional anchor: this path literal pins the orchestration skill under test.
# It is a load-bearing constant (the evaluator is meaningless against any other
# file), parallel to the documented path-literal token in
# CONTRACT_REFERENCE_SUPPORT_FILE. A move of skills/implement/SKILL.md is a
# single-line change here.
SKILL = ROOT / "skills" / "implement" / "SKILL.md"


# The execution-order heading is a DECLARED anchor: the structural ordering parser
# scopes itself to the numbered list under this heading. If the heading is renamed,
# the ordering test must report "section not found — heading may have been renamed",
# NOT a misleading "step missing". Declared here so the anchor is single-source.
EXECUTION_ORDER_HEADING = "## per-task execution order"


def execution_order_steps():
    """Return the numbered steps of SKILL.md's Per-Task Execution Order section.

    Scoped to the execution-order section so we order the IMPLEMENTER step list, not
    the main-agent bookkeeping steps that follow. Fails LOUD (raises via assert in
    the caller) if the declared heading is absent — a renamed heading must not be
    read as "steps in order".
    """
    text = read_skill()
    lines = text.splitlines()
    start = next(
        (
            i
            for i, ln in enumerate(lines)
            if ln.strip().lower().startswith(EXECUTION_ORDER_HEADING)
        ),
        None,
    )
    if start is None:
        return None
    # Stop at the next H2 so we do not absorb the main-agent numbered steps under a
    # later heading into the implementer ordering.
    end = next(
        (j for j in range(start + 1, len(lines)) if lines[j].startswith("## ")),
        len(lines),
    )
    section = "\n".join(lines[start:end])
    return numbered_steps(section)


# Declared/commented anchor for the Support Files heading. Single-sourced so both the
# death test and the unit test scope to the SAME section and an honest "renamed
# heading" message is possible. If the heading is renamed in SKILL.md, change it
# HERE — the tests then fail with an explicit "heading may have been renamed" message
# rather than a misleading "path missing".
SUPPORT_FILES_HEADING = "## support files"


def support_files_section() -> str | None:
    """Return the text of SKILL.md's Support Files section, or None if the declared
    heading is absent (renamed/removed). None is a LOUD signal — callers must
    distinguish it from "path missing from the section", never silently treat a
    renamed heading as an empty section.
    """
    lines = read_skill().splitlines()
    start = next(
        (
            i
            for i, ln in enumerate(lines)
            if ln.strip().lower().startswith(SUPPORT_FILES_HEADING)
        ),
        None,
    )
    if start is None:
        return None
    # Section ends at the next H2 heading (anti-brittle: the section may grow or
    # shrink; scan to the next '## ' rather than a fixed window).
    end = next(
        (j for j in range(start + 1, len(lines)) if lines[j].startswith("## ")),
        len(lines),
    )
    return "\n".join(lines[start:end])


def read_skill() -> str:
    return SKILL.read_text(encoding="utf-8")


# --- Death tests -----------------------------------------------------------


class TestContractGateMandatoryDeath:
    def test_skill_names_a_test_contract_gate(self):
        # DEATH [DC1-NO-GATE]: the skill sequences unit tests but never names a Test
        # Contract Gate. With no gate, an implementer dispatched by this skill writes
        # brittle/tautological unit tests that then pass review — the exact gap the
        # feature exists to close. We only run this once the skill actually mentions
        # unit tests (it does, throughout the execution order).
        text = read_skill()
        assert "unit test" in text.lower(), (
            "precondition: SKILL.md must orchestrate unit tests for this gate to "
            "have an anchor; the skill structure changed unexpectedly."
        )
        for key, tokens in TEST_CONTRACT_GATE.items():
            assert concept_present(text, tokens), (
                f"SILENT FAILURE [DC1-NO-GATE]: SKILL.md sequences unit tests but "
                f"does not name the Test Contract Gate concept '{key}'. Without the "
                f"gate, dispatched implementers write brittle/tautological unit "
                f"tests that pass review."
            )

    def test_gate_runs_before_unit_tests(self):
        # DEATH [DC4-GATE-MISPLACED]: a gate placed AFTER unit tests are written is
        # worthless — the tautological test is already on disk. The skill must state
        # the gate runs BEFORE writing unit tests.
        text = read_skill()
        for key, tokens in GATE_BEFORE_UNIT.items():
            assert concept_present(text, tokens), (
                f"SILENT FAILURE [DC4-GATE-MISPLACED]: SKILL.md does not place the "
                f"Test Contract Gate BEFORE unit tests (concept '{key}'). A gate "
                f"that runs after the unit test is written cannot prevent a "
                f"tautological test from landing on disk."
            )


class TestStructuralOrderingDeath:
    """The load-bearing ordering assertion: POSITION, not label text.

    A presence token ("Test Contract Gate (before unit tests)") proves the gate is
    MENTIONED. It cannot prove the gate physically precedes the unit-test step: a
    future author can move the gate below the unit-test step and keep the label, and
    every presence token still passes. So here we parse the numbered execution-order
    step list and assert the POSITIONAL invariant death < gate < unit. The synthetic
    misplaced-order death test below proves this check goes RED when the gate is
    moved after unit tests — which a presence token never would.
    """

    def test_death_before_gate_before_unit_structurally(self):
        # DEATH [DC4-GATE-MISPLACED, structural]: assert ORDER by position in the
        # numbered step list, independent of the step's label wording.
        steps = execution_order_steps()
        assert steps is not None, (
            "SILENT FAILURE [DC4-NO-EXEC-SECTION]: the Per-Task Execution Order "
            "section was not found — its heading may have been renamed. The "
            "structural ordering invariant cannot be checked, so a misplaced gate "
            "would go undetected."
        )
        death_i = step_index_of_concept(steps, STEP_DEATH_TEST)
        gate_i = step_index_of_concept(steps, STEP_CONTRACT_GATE)
        unit_i = step_index_of_concept(steps, STEP_UNIT_TEST)
        assert death_i is not None, (
            "SILENT FAILURE: no numbered step writes death tests; the death-test "
            "step may have been removed or reworded out of recognition."
        )
        assert gate_i is not None, (
            "SILENT FAILURE: no numbered step runs the Test Contract Gate."
        )
        assert unit_i is not None, "SILENT FAILURE: no numbered step writes unit tests."
        assert death_i < gate_i < unit_i, (
            f"SILENT FAILURE [DC4-GATE-MISPLACED, structural]: execution-order "
            f"positions are death={death_i}, gate={gate_i}, unit={unit_i}. The "
            f"invariant is death < gate < unit. A presence token would still pass "
            f"here; the POSITION shows the gate is not actually before unit tests."
        )

    def test_structural_check_reddens_on_synthetic_misplaced_gate(self):
        # MUTATE-TO-RED: construct a SYNTHETIC execution list where the gate is placed
        # AFTER the unit-test step (label preserved) and assert the structural check
        # catches it. This is the proof a presence token cannot give: the same label
        # text, wrong position, must go RED.
        misplaced = (
            "1. STEP 0 — answer the prerequisite questions\n"
            "2. Write death tests — silent failure paths first\n"
            "3. Run death tests — verify red\n"
            "4. Write unit tests — author the unit tests\n"
            "5. **Test Contract Gate (before unit tests)** — run the contract gate "
            "from references/test-contract.md\n"
            "6. Run unit tests — verify red\n"
        )
        steps = numbered_steps(misplaced)
        death_i = step_index_of_concept(steps, STEP_DEATH_TEST)
        gate_i = step_index_of_concept(steps, STEP_CONTRACT_GATE)
        unit_i = step_index_of_concept(steps, STEP_UNIT_TEST)
        assert death_i is not None and gate_i is not None and unit_i is not None
        # The misplaced list keeps the gate LABEL, so a presence token would pass.
        # The structural invariant must FAIL (gate is after unit here).
        assert not (death_i < gate_i < unit_i), (
            "The structural ordering check did NOT redden on a synthetic list with "
            "the gate placed after the unit-test step. The check is asserting the "
            "label, not the position — it cannot enforce the ordering invariant."
        )

    def test_structural_check_passes_on_real_skill(self):
        # The same check that reddens on the synthetic misplaced list must PASS on the
        # real SKILL.md (mutate-to-red is only meaningful if the real doc is green).
        steps = execution_order_steps()
        assert steps is not None
        death_i = step_index_of_concept(steps, STEP_DEATH_TEST)
        gate_i = step_index_of_concept(steps, STEP_CONTRACT_GATE)
        unit_i = step_index_of_concept(steps, STEP_UNIT_TEST)
        assert death_i is not None and gate_i is not None and unit_i is not None
        assert death_i < gate_i < unit_i


class TestBothPolesFlaggedDeath:
    def test_overfit_pole_flagged(self):
        # DEATH [DC1-OVERFIT]: the skill must name the over-fit / brittle red flag.
        text = read_skill()
        for key, tokens in BRITTLENESS_FILTER.items():
            assert concept_present(text, tokens), (
                f"SILENT FAILURE [DC1-OVERFIT]: SKILL.md does not flag the over-fit "
                f"pole concept '{key}'. Brittle unit tests pass review."
            )

    def test_silent_green_pole_flagged(self):
        # DEATH [DC2-SILENT-GREEN]: flagging brittleness ALONE is the trap. If the
        # silent-green pole is not also flagged, implementers write tautological
        # tests that stay green when behavior breaks. The task explicitly requires
        # the skill to fail review if it prevents over-fit tests but omits the
        # silent-green flag.
        text = read_skill()
        for key, tokens in SILENT_GREEN_GUARD.items():
            assert concept_present(text, tokens), (
                f"SILENT FAILURE [DC2-SILENT-GREEN]: SKILL.md flags brittleness but "
                f"not the silent-green pole concept '{key}'. Tautological tests stay "
                f"green when behavior breaks."
            )


class TestSupportFileRegisteredDeath:
    def test_reference_registered_as_support_file(self):
        # DEATH [DC3-DANGLING-GATE]: if references/test-contract.md is absent from
        # the Support Files section, the gate points at a protocol the dispatched
        # implementer cannot locate via the skill's own file index. We assert the
        # path appears WITHIN the Support Files section, not merely somewhere in the
        # document — a passing mention elsewhere does not register it as a support
        # file an implementer is told to read.
        section = support_files_section()
        # Honest failure: distinguish "heading renamed / section absent" from "path
        # missing FROM the section". A misleading "section absent" message when the
        # heading was merely renamed would send a future author hunting the wrong bug.
        assert section is not None, (
            f"SILENT FAILURE [DC3-NO-SUPPORT-SECTION]: no section matching the "
            f"declared anchor '{SUPPORT_FILES_HEADING}' was found in SKILL.md. The "
            f"heading may have been RENAMED (update SUPPORT_FILES_HEADING), or the "
            f"section was removed. Either way the contract reference cannot be "
            f"registered as a support file."
        )
        for key, tokens in CONTRACT_REFERENCE_SUPPORT_FILE.items():
            assert concept_present(section, tokens), (
                f"SILENT FAILURE [DC3-DANGLING-GATE]: the Support Files section EXISTS "
                f"but does not register the contract reference (concept '{key}'). The "
                f"Test Contract Gate would point at a protocol the dispatched "
                f"implementer cannot find via the skill's own file index."
            )


class TestDeathTestFirstPreservedDeath:
    def test_death_test_first_ordering_preserved(self):
        # DEATH [DC5-ORDERING-ROT]: adding a Test Contract Gate must NOT displace the
        # load-bearing death-test-first rule. If the skill stops stating that death
        # tests come before unit tests (or that the order cannot be swapped), the
        # ordering silently rots — the whole point of the framework.
        text = read_skill()
        for key, tokens in DEATH_TEST_FIRST.items():
            assert concept_present(text, tokens), (
                f"SILENT FAILURE [DC5-ORDERING-ROT]: SKILL.md no longer preserves the "
                f"death-test-first concept '{key}'. The Test Contract Gate displaced "
                f"the load-bearing 'death test before unit test' ordering."
            )


class TestStepZeroCountDesyncDeath:
    def test_no_three_questions_desync_survives(self):
        # DEATH [DC-DESYNC]: task-2 made STEP 0 four questions in agents/implementer.md.
        # SKILL.md had two stale references ("STEP 0 前置三問", "answer the three
        # prerequisite questions"). A single surviving "three"/"三問" occurrence means
        # the orchestration claims three while the agent answers four — a silent
        # count desync nobody is alerted to.
        text = read_skill()
        lower = text.lower()
        forbidden_en = ["three questions", "three prerequisite"]
        survivors = [p for p in forbidden_en if p in lower]
        assert "三問" not in text, (
            "SILENT FAILURE [DC-DESYNC]: SKILL.md still contains '三問'. STEP 0 is now "
            "four questions; a surviving 'three' occurrence desyncs the count from "
            "agents/implementer.md."
        )
        assert not survivors, (
            f"SILENT FAILURE [DC-DESYNC]: SKILL.md still contains {survivors}. STEP 0 "
            f"is now four prerequisite questions; a surviving 'three' occurrence "
            f"desyncs the orchestration from the agent."
        )


class TestNewConceptsAreNotGreenByConstructionDeath:
    """DC-DECOY: the new SKILL-surface tokens must be able to go RED.

    The disease this feature kills is a token that matches any document because it
    keys on a common word. The implement skill mentions several unrelated "gate"s
    (Execution strategy gate, Completion gate, Auto Mode Gate) and "before"/"unit
    test" everywhere. We construct hostile decoy prose that sprinkles in those exact
    words WITHOUT the test-contract concept and assert EVERY new concept is reported
    missing. Any concept covered here is green-by-construction and must be tightened.
    """

    def test_new_concepts_fail_on_hostile_decoy(self):
        decoy = (
            "Open the garden gate before the rain. The execution strategy gate asks "
            "whether to run subagents. A completion gate confirms the user is ready. "
            "Write a unit of work before lunch; the death of summer comes before the "
            "first frost. The auto mode gate routes decisions. Test the soup before "
            "serving and keep the ordering of courses."
        )
        new_groups = {
            **TEST_CONTRACT_GATE,
            **GATE_BEFORE_UNIT,
            **DEATH_TEST_FIRST,
        }
        # DRY the coverage assertion via the shared helper so tasks 2-6 cannot
        # diverge on what "covered" means. The decoy STRING stays local — genuinely
        # different hostile prose (healthy DAMP); only the CHECK is shared.
        covered = concepts_covered_by(decoy, new_groups)
        assert not covered, (
            "SILENT FAILURE [DC-DECOY]: these new SKILL-surface concepts were "
            f"reported covered by unrelated decoy prose: {sorted(covered)}. Their "
            "tokens key on common words ('gate'/'before'/'unit') and can never go "
            "red. Tighten them to intent-bearing tokens bound to the test contract."
        )

    def test_new_concept_tokens_are_not_pinned_headings(self):
        # A token must not BE a markdown heading string, or the check passes only
        # while a specific heading survives. The heading-pin scan is the authoritative
        # shared `pinned_heading_offenders` (same implementation task-1/2 use).
        # CONTRACT_REFERENCE_SUPPORT_FILE is a path literal (legitimately exact), but
        # it still must not contain '##', so it is included in the scan.
        new_groups = {
            **TEST_CONTRACT_GATE,
            **GATE_BEFORE_UNIT,
            **DEATH_TEST_FIRST,
            **CONTRACT_REFERENCE_SUPPORT_FILE,
        }
        offenders = pinned_heading_offenders(new_groups)
        assert not offenders, (
            "SILENT FAILURE [DC-PINNED-HEADING]: a new concept token is a markdown "
            f"heading string: {offenders}. Tokens must be intent-bearing concepts."
        )

    def test_unrelated_contract_gate_prose_is_missing_contract_gate(self):
        # DC-DECOY-POLARITY: the TEST_CONTRACT_GATE concept must bind to the *test*
        # contract gate, not any "contract gate" prose. A doc about a "deployment
        # contract gate" / "data contract gate" — with no link to the test/unit-test
        # protocol and no reference path — must be reported MISSING. This is the exact
        # over-fit the loose `contract gate` token caused: it matched unrelated prose.
        unrelated = (
            "The deployment contract gate checks the API schema before release. "
            "Our data contract gate validates the producer-consumer schema. A "
            "billing contract gate blocks invoices that fail the SLA contract."
        )
        assert not concepts_covered_by(unrelated, TEST_CONTRACT_GATE), (
            "SILENT FAILURE [DC-DECOY-POLARITY]: TEST_CONTRACT_GATE was reported "
            "covered by unrelated 'contract gate' prose (deployment/data/billing). "
            "The token must bind the gate to the test/unit-test protocol or the "
            "reference path, or any 'contract gate' mention passes review."
        )

    def test_silent_green_decoy_separates_poles(self):
        # DC-DECOY-POLES: prove the two red-flag poles are independently checkable —
        # a doc that flags ONLY brittleness must NOT be reported as covering the
        # silent-green pole. This is the precise gap the task names ("prevents
        # over-fit tests but omits silent-green tests"): if SILENT_GREEN_GUARD could
        # be satisfied by brittleness-only prose, the omission would pass silently.
        brittle_only = (
            "Red flag: do not write over-fit, brittle unit tests that pin "
            "implementation details and redden on a harmless rename."
        )
        assert not concepts_covered_by(brittle_only, SILENT_GREEN_GUARD), (
            "SILENT FAILURE [DC-DECOY-POLES]: SILENT_GREEN_GUARD was reported covered "
            "by brittleness-only prose. The silent-green pole must be independently "
            "checkable, or a skill that flags only over-fit would pass review."
        )


# --- Unit tests ------------------------------------------------------------


class TestImplementSkillContractProtocol:
    def test_names_test_contract_gate(self):
        text = read_skill()
        missing = missing_concepts(text, TEST_CONTRACT_GATE)
        assert not missing, (
            f"SKILL.md must name a Test Contract Gate; missing concepts: {missing}"
        )

    def test_gate_runs_before_unit_tests(self):
        text = read_skill()
        missing = missing_concepts(text, GATE_BEFORE_UNIT)
        assert not missing, (
            f"SKILL.md must place the Test Contract Gate before unit tests; "
            f"missing concepts: {missing}"
        )

    def test_flags_both_poles(self):
        text = read_skill()
        both = {**BRITTLENESS_FILTER, **SILENT_GREEN_GUARD}
        missing = missing_concepts(text, both)
        assert not missing, (
            f"SKILL.md must flag BOTH red-flag poles (over-fit + silent-green); "
            f"missing concepts: {missing}"
        )

    def test_states_contract_principle_and_points_to_reference(self):
        # The lean skill must carry the PRINCIPLE (assert a behavioral contract, not
        # implementation detail) AND a POINTER to references/test-contract.md — but it
        # must NOT re-enumerate the source catalog (that is implementer-surface,
        # task-2's concern; a duplicated catalog drifts). So we check the principle +
        # pointer, not the full source list.
        text = read_skill()
        missing = missing_concepts(text, CONTRACT_PRINCIPLE_AND_POINTER)
        assert not missing, (
            f"SKILL.md must state the contract-bound principle (assert a behavioral "
            f"contract, not implementation details) AND point to "
            f"references/test-contract.md; missing concepts: {missing}"
        )

    def test_registers_reference_in_support_files_section(self):
        # Scoped to the '## Support Files' section (consistent with the death test
        # test_reference_registered_as_support_file). The earlier name/scope checked
        # the WHOLE document, so a passing mention anywhere — including the Test
        # Contract Gate prose that names the path — satisfied a name promising
        # *registration in the support-files list*. That over-promise is fixed here.
        section = support_files_section()
        assert section is not None, (
            f"SKILL.md has no section matching '{SUPPORT_FILES_HEADING}' (heading may "
            f"have been renamed); cannot register the reference as a support file."
        )
        missing = missing_concepts(section, CONTRACT_REFERENCE_SUPPORT_FILE)
        assert not missing, (
            f"SKILL.md must register references/test-contract.md in the Support Files "
            f"section; missing concepts: {missing}"
        )

    def test_preserves_death_test_first_ordering(self):
        text = read_skill()
        missing = missing_concepts(text, DEATH_TEST_FIRST)
        assert not missing, (
            f"SKILL.md must preserve death-test-first ordering; missing concepts: "
            f"{missing}"
        )

    def test_no_surviving_three_questions_reference(self):
        text = read_skill()
        assert "三問" not in text
        lower = text.lower()
        assert "three questions" not in lower
        assert "three prerequisite" not in lower
