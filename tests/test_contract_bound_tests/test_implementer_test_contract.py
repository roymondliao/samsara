"""Evaluator for the implementer agent's contract-bound test-writing protocol (Task 2).

The implementer agent (`agents/implementer.md`) is the highest-leverage surface in
this feature: it is the file that actually WRITES death tests and unit tests. Its
execution order historically said only "Write unit tests", which silently permits
hard-coded / tautological unit tests to be written and then pass review.

Death tests run BEFORE the unit tests and target SILENT failure paths — the ones
that stay GREEN while the instruction is hollow:

  DC1 The agent says only "Write unit tests" with no contract binding → it writes
      brittle, implementation-detail-coupled unit tests that pass review.
  DC2 The agent guards the over-fit pole (brittleness) but NOT the silent-green
      pole → it writes tautological tests that never go red.
  DC3 The agent implies every failing test means the implementation is wrong → it
      bends the implementation to satisfy a rotten test instead of fixing the test.
  DC4 The anti-over-fit rule bleeds onto DEATH tests → someone softens a death
      test that was correctly pinning its exact failure mode.
  DC-DESYNC The STEP 0 question count is changed in some places but a "three
      questions" occurrence survives → the agent answers four but reports three.
  DC-DECOY The new implementer-surface concept tokens are green-by-construction
      (key on the bare words "contract"/"fix") → they can never go red.

Each death test names the silent-failure mode it pins; that failure mode IS this
death test's contract, so (per the protocol) it is allowed to be exact here.
"""

from __future__ import annotations

import re
from pathlib import Path

from tests.test_contract_bound_tests._contract_tokens import (
    BRITTLENESS_FILTER,
    CONTRACT_BOUND_UNIT,
    CONTRACT_GATE,
    FIX_THE_TEST,
    SILENT_GREEN_GUARD,
    UNIT_VS_DEATH,
)
from tests.test_contract_bound_tests._token_lib import (
    concept_present,
    concepts_covered_by,
    missing_concepts,
    pinned_heading_offenders,
)

ROOT = Path(__file__).resolve().parents[2]
IMPLEMENTER = ROOT / "agents" / "implementer.md"


def read_implementer() -> str:
    return IMPLEMENTER.read_text(encoding="utf-8")


# --- Death tests -----------------------------------------------------------


class TestContractBoundRequiredDeath:
    def test_unit_test_step_requires_contract_binding(self):
        # DEATH [DC1-BRITTLE-PASSES-REVIEW]: if the agent says only "Write unit
        # tests" with no contract binding, it writes implementation-detail-coupled
        # unit tests that redden on harmless refactors yet pass review.
        text = read_implementer()
        for key, tokens in CONTRACT_BOUND_UNIT.items():
            assert concept_present(text, tokens), (
                f"SILENT FAILURE [DC1-BRITTLE]: implementer.md does not require the "
                f"contract-bound unit-test concept '{key}'. A bare 'Write unit "
                f"tests' instruction lets brittle/tautological tests pass review."
            )

    def test_bare_write_unit_tests_line_is_not_left_uncaveated(self):
        # DEATH [DC1-SLOGAN-VOID]: the literal execution-order line must not remain
        # the un-caveated "Write unit tests" with nothing binding it to a contract.
        # We pin the silent regression directly: the exact bare line must be gone.
        text = read_implementer()
        lines = [ln.strip() for ln in text.splitlines()]
        assert "4. Write unit tests" not in lines, (
            "SILENT FAILURE [DC1-SLOGAN-VOID]: the execution-order line is still the "
            "bare '4. Write unit tests' with no contract-binding caveat. This is the "
            "exact gap the feature exists to close."
        )

    def test_mention_only_sources_are_missing_contract_source(self):
        # DEATH [DC1-MENTION-NOT-BINDING]: presence-not-binding backdoor. A doc that
        # merely NAMES the source words ("observable behaviour", "public api or
        # schema", "documented artifact shape") WITHOUT binding a unit test to them
        # would silently pass `names_a_contract_source`. We construct exactly that
        # mention-only prose (sources named, no assert-binding, no reference path)
        # and assert the concept is reported MISSING. `contract_bound_requirement`
        # remains the harder gate; this proves the SOURCE token requires binding.
        mention_only = (
            "Background notes: observable behaviour can vary between runs. The "
            "public api or schema evolves over releases, and the documented "
            "artifact shape is discussed in onboarding. Anyway, write some unit "
            "tests when you get a chance."
        )
        assert not concept_present(
            mention_only, CONTRACT_BOUND_UNIT["names_a_contract_source"]
        ), (
            "SILENT FAILURE [DC1-MENTION-NOT-BINDING]: 'names_a_contract_source' "
            "matched prose that merely MENTIONS the source words without binding a "
            "unit test to them. The token is presence-not-binding — it must require "
            "the source to be bound to the act of asserting (a unit test MUST ASSERT "
            "<source>), or name the canonical reference PATH, not a passing mention."
        )


class TestBothPolesGuardedDeath:
    def test_overfit_pole_guarded(self):
        # DEATH [DC1-OVERFIT]: self-review must guard the over-fit pole.
        text = read_implementer()
        for key, tokens in BRITTLENESS_FILTER.items():
            assert concept_present(text, tokens), (
                f"SILENT FAILURE [DC1-OVERFIT]: implementer.md does not guard the "
                f"over-fit pole concept '{key}'. Brittle unit tests pass self-review."
            )

    def test_silent_green_pole_guarded(self):
        # DEATH [DC2-SILENT-GREEN]: guarding brittleness ALONE is the trap — the
        # fix is not "assert less". If the silent-green pole is not also guarded,
        # the agent writes tautological tests that stay green when behavior breaks.
        text = read_implementer()
        for key, tokens in SILENT_GREEN_GUARD.items():
            assert concept_present(text, tokens), (
                f"SILENT FAILURE [DC2-SILENT-GREEN]: implementer.md guards "
                f"brittleness but not the silent-green pole concept '{key}'. "
                f"Tautological tests stay green when behavior breaks."
            )

    def test_self_review_asks_both_poles(self):
        # DEATH [DC-BOTH-POLES]: the contract gate's BOTH directions must be
        # askable in self-review — a behavior-preserving refactor must NOT redden
        # the test, AND a real behavior break MUST redden it. Guarding one pole
        # only re-creates the disease at the other pole.
        text = read_implementer()
        for key, tokens in CONTRACT_GATE.items():
            assert concept_present(text, tokens), (
                f"SILENT FAILURE [DC-BOTH-POLES]: implementer self-review does not "
                f"ask the contract-gate concept '{key}'. Only one pole is guarded."
            )


class TestFixTheRottenTestDeath:
    def test_failing_test_does_not_always_mean_impl_is_wrong(self):
        # DEATH [DC3-ROTTEN-TEST]: if the instruction implies every failing test
        # means the implementation is wrong, the agent bends the implementation to
        # satisfy a test bound to the WRONG contract. The fix-the-test caveat must
        # be present.
        text = read_implementer()
        for key, tokens in FIX_THE_TEST.items():
            assert concept_present(text, tokens), (
                f"SILENT FAILURE [DC3-ROTTEN-TEST]: implementer.md lacks the "
                f"fix-the-test concept '{key}'. The agent would bend the "
                f"implementation to satisfy a rotten (wrong-contract) test."
            )

    def test_fix_the_test_caveat_rides_the_execution_order_line(self):
        # DEATH [DC3-CAVEAT-MISPLACED]: the task requires the caveat to ride the
        # execution-order line ITSELF (the "implement minimal code to pass all
        # tests" line), not live only in a faraway note. We locate that line and
        # assert the fix-the-test concept is present in its immediate vicinity.
        text = read_implementer()
        lines = text.splitlines()
        anchor_idx = next(
            (
                i
                for i, ln in enumerate(lines)
                if "implement minimal code to pass" in ln.lower()
            ),
            None,
        )
        assert anchor_idx is not None, (
            "execution-order 'implement minimal code to pass all tests' line not "
            "found; structure changed unexpectedly."
        )
        # Anti-brittleness: a behavior-preserving REWRAP of step 6 across more lines
        # must NOT redden this. So instead of a fixed +2 window (over-fit, ironic in
        # an anti-brittleness exemplar), scan from the anchor to the NEXT numbered
        # list item ("7."), proving the caveat lives within the SAME execution-order
        # step — not a faraway section — however that step is wrapped.
        end_idx = next(
            (
                j
                for j in range(anchor_idx + 1, len(lines))
                if re.match(r"\s*7\.\s", lines[j])
            ),
            None,
        )
        # Fallback bound if step 7 is ever unnumbered/renumbered: cap the window so
        # the caveat must still be near the anchor, never an arbitrary distance.
        if end_idx is None:
            end_idx = min(anchor_idx + 8, len(lines))
        window = "\n".join(lines[anchor_idx:end_idx])
        assert concept_present(window, FIX_THE_TEST["fix_rotten_test_not_impl"]), (
            "SILENT FAILURE [DC3-CAVEAT-MISPLACED]: the fix-the-test caveat is not "
            "carried within the execution-order step itself (anchor line through the "
            "next numbered item). A separate note far away is silently skippable "
            "when an agent follows the numbered steps."
        )

    def test_endorsing_wrong_practice_is_missing_fix_concept(self):
        # DEATH [DC3-POLARITY]: presence-not-polarity backdoor. A bare
        # `fix the test` token would match a doc that ENDORSES the WRONG practice
        # ("when a test fails, always fix the test to make it pass") identically to
        # one that says "fix the test, NOT the implementation". The decoy test
        # proves WORD-matching is dead; THIS polarity test proves DIRECTION is
        # required. An endorsing string must be reported MISSING the concept.
        endorsing_wrong_practice = (
            "Testing policy: when a test fails, always fix the test to make it "
            "pass. A failing test is the test's problem — adjust the test until it "
            "is green and move on. Fix the test, then ship."
        )
        assert not concept_present(
            endorsing_wrong_practice, FIX_THE_TEST["fix_rotten_test_not_impl"]
        ), (
            "SILENT FAILURE [DC3-POLARITY]: the 'fix-the-test' concept matched prose "
            "that ENDORSES the wrong practice (always fix the test to make it pass). "
            "The token is presence-not-polarity — a silent-green backdoor. It must "
            "require the DIRECTION (fix the test, NOT the implementation / "
            "wrong-rotten contract), not the bare phrase 'fix the test'."
        )


class TestDeathTestDistinctionPreservedDeath:
    def test_anti_overfit_does_not_weaken_death_tests(self):
        # DEATH [DC4-WEAKENED-DEATH-TEST]: the anti-over-fit rule applies to UNIT
        # tests only. If the implementer omits this distinction, the new
        # anti-brittleness language bleeds onto death tests and someone softens a
        # death test that was correctly pinning its exact silent-failure mode.
        text = read_implementer()
        for key, tokens in UNIT_VS_DEATH.items():
            assert concept_present(text, tokens), (
                f"SILENT FAILURE [DC4-WEAKENED-DEATH-TEST]: implementer.md does not "
                f"preserve the unit-vs-death concept '{key}'. Death tests could be "
                f"weakened by anti-over-fit language meant only for unit tests."
            )


class TestStepZeroFourQuestionsDeath:
    def test_step_zero_has_the_longevity_question(self):
        # DEATH [DC-Q4-MISSING]: STEP 0 must include the canonical longevity
        # question. Omitting it silently drops the "is this still alive in the
        # future?" gate from every implementer run.
        text = read_implementer()
        assert "目前做的事情在未來是否還活著" in text, (
            "SILENT FAILURE [DC-Q4-MISSING]: STEP 0 longevity question "
            "'目前做的事情在未來是否還活著？' is absent. The fourth prerequisite "
            "gate is silently dropped."
        )

    def test_no_three_questions_desync_survives(self):
        # DEATH [DC-DESYNC]: a single surviving "three questions"/"three
        # prerequisite" occurrence means the agent answers four questions while
        # some line still claims three — a silent count desync nobody is alerted to.
        text = read_implementer().lower()
        forbidden = ["three questions", "three prerequisite"]
        survivors = [p for p in forbidden if p in text]
        assert not survivors, (
            f"SILENT FAILURE [DC-DESYNC]: implementer.md still contains "
            f"{survivors}. STEP 0 is now four questions; a surviving 'three' "
            f"occurrence desyncs the count and silently mis-instructs the agent."
        )


class TestNewConceptsAreNotGreenByConstructionDeath:
    """DC-DECOY: the new implementer-surface tokens must be able to go RED.

    The disease this feature kills is a token that matches any document because it
    keys on a common word ("contract" appears in every scar-report sentence;
    "fix" appears everywhere). We construct hostile decoy prose that sprinkles in
    those exact words and assert EVERY new concept is reported missing. Any concept
    covered here is green-by-construction and must be tightened.
    """

    def test_new_concepts_fail_on_hostile_decoy(self):
        decoy = (
            "The team agreed on a social contract over lunch and signed it. "
            "Please fix the leaky faucet and fix the printer; the unit price was "
            "fine. We wrote a behaviour report about the public square and the "
            "documented history of the old shape on the wall. Schema the cake into "
            "even slices and assert your right to dessert."
        )
        new_groups = {
            **CONTRACT_BOUND_UNIT,
            **FIX_THE_TEST,
        }
        # DRY the coverage assertion via the shared helper so tasks 2-6 cannot
        # diverge on what "covered" means. The decoy STRING stays local — it is
        # genuinely different hostile prose (healthy DAMP); only the CHECK is shared.
        covered = concepts_covered_by(decoy, new_groups)
        assert not covered, (
            "SILENT FAILURE [DC-DECOY]: these new implementer-surface concepts were "
            f"reported covered by unrelated decoy prose: {sorted(covered)}. Their "
            "tokens key on common words ('contract'/'fix') and can never go red. "
            "Tighten them to intent-bearing tokens."
        )

    def test_new_concept_tokens_are_not_pinned_headings(self):
        # A token must not BE a markdown heading string, or the check passes only
        # while a specific heading survives. The heading-pin scan is the authoritative
        # shared `pinned_heading_offenders` (same implementation task-1 uses).
        new_groups = {**CONTRACT_BOUND_UNIT, **FIX_THE_TEST}
        offenders = pinned_heading_offenders(new_groups)
        assert not offenders, (
            "SILENT FAILURE [DC-PINNED-HEADING]: a new concept token is a markdown "
            f"heading string: {offenders}. Tokens must be intent-bearing concepts."
        )


# --- Unit tests ------------------------------------------------------------


class TestImplementerContractProtocol:
    def test_requires_contract_bound_unit_tests(self):
        text = read_implementer()
        missing = missing_concepts(text, CONTRACT_BOUND_UNIT)
        assert not missing, (
            f"implementer.md must require contract-bound unit tests; missing "
            f"concepts: {missing}"
        )

    def test_guards_both_poles(self):
        text = read_implementer()
        both = {**BRITTLENESS_FILTER, **SILENT_GREEN_GUARD}
        missing = missing_concepts(text, both)
        assert not missing, (
            f"implementer.md must guard BOTH poles (brittle + silent-green); "
            f"missing concepts: {missing}"
        )

    def test_self_review_asks_both_poles_questions(self):
        text = read_implementer()
        missing = missing_concepts(text, CONTRACT_GATE)
        assert not missing, (
            f"implementer self-review must ask both-poles contract-gate questions; "
            f"missing concepts: {missing}"
        )

    def test_allows_fixing_a_rotten_test(self):
        text = read_implementer()
        missing = missing_concepts(text, FIX_THE_TEST)
        assert not missing, (
            f"implementer.md must allow fixing a test bound to the wrong contract; "
            f"missing concepts: {missing}"
        )

    def test_preserves_unit_vs_death_distinction(self):
        text = read_implementer()
        missing = missing_concepts(text, UNIT_VS_DEATH)
        assert not missing, (
            f"implementer.md must preserve the unit-vs-death distinction so death "
            f"tests keep exact failure-mode pinning; missing concepts: {missing}"
        )

    def test_step_zero_lists_four_questions(self):
        text = read_implementer()
        # The four canonical STEP 0 questions must all be present (the longevity
        # question is the new fourth). We assert the count framing is "four" and
        # the four numbered prompts exist.
        assert "目前做的事情在未來是否還活著" in text
        # The intro must frame STEP 0 as four questions, not three.
        lines = text.lower()
        assert "four questions" in lines, (
            "STEP 0 intro must frame the prerequisite as 'four questions'."
        )

    def test_no_surviving_three_questions_reference(self):
        text = read_implementer().lower()
        assert "three questions" not in text
        assert "three prerequisite" not in text
