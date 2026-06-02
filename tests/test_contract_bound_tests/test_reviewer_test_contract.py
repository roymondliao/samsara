"""Evaluator for reviewer enforcement + dispatch propagation (Task 4).

Task-4 closes the loop. The reference (task-1), implementer (task-2), implement
skill (task-3), and planning (task-5) surfaces all describe contract-bound unit
tests. But a gate that is DOCUMENTED yet never DISPATCHED is worthless — death case
DC4. So three surfaces must make the gate REAL:

  * agents/code-reviewer.md (yin) — reviews TESTS BEFORE implementation correctness;
    flags brittle (over-fit) and tautological (silent-green) tests; can say "fix the
    test, not the implementation" when a test is bound to the wrong contract; and
    CHALLENGES a perfunctory contract LABEL (Clean Scar — a slogan that maps to no
    observable behavior / API / schema / artifact / death-or-bug case).
  * agents/code-quality-reviewer.md — owns STRUCTURAL test coupling (tests coupled to
    implementation structure) and REFERS silent-rot/correctness concerns to the yin
    reviewer (the role split).
  * skills/implement/dispatch-template.md — BOTH reviewer dispatch BLOCKS carry a
    test-quality review prompt, so the gate is actually asked on dispatch.

Death tests run BEFORE the unit tests and target SILENT failure paths — the ones
that stay GREEN while the enforcement loop is hollow:

  DC1-NO-TEST-REVIEW The yin reviewer never reviews tests as a subject → brittle
      tests pass review.
  DC2-ORDER-REVERSED The yin reviewer reviews implementation correctness BEFORE
      tests → a rotten test forces a wrong implementation change before anyone looks
      at the test. Asserted STRUCTURALLY (position), proven RED on a reversed fixture.
  DC3-NO-FIX-THE-TEST No reviewer can say "fix the test, not the implementation" →
      the rotten test bends the implementation to itself.
  DC4-DISPATCH-OMITTED A dispatch block omits the test-quality prompt → the gate is
      documented but never asked. Checked per-block; both must carry it.
  DC5-NO-STRUCTURAL-COUPLING The code-quality reviewer has no structural test-coupling
      guidance → tests coupled to implementation structure pass review.
  DC6-NO-REFERRAL The code-quality reviewer does not refer silent-rot to the yin
      reviewer → the role split collapses (both score the same thing, or neither).
  DC7-CLEAN-SCAR The yin reviewer cannot challenge a perfunctory contract LABEL → a
      slogan like "# contract: it works" satisfies the gate.
  DC-DECOY The new reviewer-surface tokens are green-by-construction → can never go
      red.
  DC-POLARITY The directional tokens match a doc that ENDORSES the wrong practice →
      the polarity is not actually checked.

Each death test names the silent-failure mode it pins; that failure mode IS this
death test's contract, so (per the protocol) it is allowed to be exact here.
"""

from __future__ import annotations

from tests.test_contract_bound_tests._contract_tokens import (
    DISPATCH_TEST_QUALITY_PROMPT,
    REVIEWER_CHALLENGE_CLEAN_SCAR,
    REVIEWER_FIX_THE_TEST,
    REVIEWER_REFERS_SILENT_ROT,
    REVIEWER_REVIEWS_TESTS,
    REVIEWER_STRUCTURAL_TEST_COUPLING,
)
from tests.test_contract_bound_tests._token_lib import (
    ROOT,
    concept_present,
    concepts_covered_by,
    missing_concepts,
    pinned_heading_offenders,
    rx,
)

# Load-bearing anchors: the evaluator is meaningless against any other file. A move
# of any target is a single-line change here.
CODE_REVIEWER = ROOT / "agents" / "code-reviewer.md"
CODE_QUALITY_REVIEWER = ROOT / "agents" / "code-quality-reviewer.md"
DISPATCH_TEMPLATE = ROOT / "skills" / "implement" / "dispatch-template.md"


def read_code_reviewer() -> str:
    return CODE_REVIEWER.read_text(encoding="utf-8")


def read_code_quality_reviewer() -> str:
    return CODE_QUALITY_REVIEWER.read_text(encoding="utf-8")


def read_dispatch_template() -> str:
    return DISPATCH_TEMPLATE.read_text(encoding="utf-8")


# --- Structural ordering: tests reviewed BEFORE correctness ------------------
#
# CRITICAL (this exact mistake FAILED task-3 review): "the yin reviewer reviews tests
# BEFORE implementation correctness" is an ORDERING claim. A presence token that
# matches a LABEL ("review tests first") still passes if a future author moves the
# test-review step BELOW the correctness step but keeps the label. So the position is
# read STRUCTURALLY: find the source position of the step whose body reviews TESTS and
# the step whose body reviews CORRECTNESS within the Review Order section, and assert
# tests_pos < correctness_pos.
#
# WHY NOT numbered_steps(): code-reviewer.md's Review Order uses '### N. Title' H3
# subsection headings, not a top-level 'N. ' numbered list, so the shared
# numbered_steps parser (top-level '`N.` ...' lines) does not see them. We therefore
# locate the two STEP HEADINGS by concept and compare their source positions. This is
# still a POSITION assertion, not a label assertion: the proof is the reversed-order
# synthetic fixture below, which keeps the step LABELS but swaps their POSITIONS and
# must go RED.

# Declared anchor for the Review Order section. Single-sourced so a renamed heading
# yields an honest "section not found" message, not a misleading "step missing".
REVIEW_ORDER_HEADING = "## review order"

# Concept tokens identifying the TEST-review step heading and the CORRECTNESS-review
# step heading. They match the step's intent, not an exact label, so an honest reword
# survives. STEP_TEST_REVIEW must bind the review step to TESTS as the subject (so it
# does not also match the correctness step); STEP_CORRECTNESS_REVIEW binds to
# correctness as the subject.
STEP_TEST_REVIEW = (
    rx(
        r"test\w*[^.\n]{0,40}(brittle|over[- ]?fit|tautolog|silent[- ]green|contract|quality)"
    ),
    rx(r"(brittle|over[- ]?fit|tautolog|silent[- ]green)[^.\n]{0,40}test"),
    rx(r"test[- ]quality"),
    rx(r"review\s+the\s+tests?\b"),
)
STEP_CORRECTNESS_REVIEW = (rx(r"\bcorrectness\b"),)


def extract_section(
    lines: list[str], start_prefix: str, end_prefixes: tuple[str, ...]
) -> str | None:
    """Return the text of the section that begins at the first line whose stripped,
    lowercased text starts with `start_prefix`, up to (excluding) the next line that
    starts with ANY of `end_prefixes`, or None if no start line is found.

    Shared by review_order_section() and dispatch_block() — both scan a heading to the
    next boundary heading and differ ONLY in their start prefix and boundary-heading
    prefixes. Returning None (never an empty string) is a LOUD signal: callers MUST
    distinguish "heading absent / renamed" from "concept missing within the section"
    and never silently treat a renamed heading as an empty section. The boundary scan
    is window-free (scan to the next boundary heading) so a section may grow or shrink
    without the parser drifting.

    Note the asymmetry the two call sites deliberately keep: the start match is on the
    STRIPPED+lowercased line (headings may be indented / cased differently), while the
    boundary match is on the RAW line prefix (a top-level '## '/'### ' heading is never
    indented). Preserving both behaviors is why the prefixes are parameters, not a
    single hardcoded rule.
    """
    start = next(
        (
            i
            for i, ln in enumerate(lines)
            if ln.strip().lower().startswith(start_prefix)
        ),
        None,
    )
    if start is None:
        return None
    end = next(
        (
            j
            for j in range(start + 1, len(lines))
            if any(lines[j].startswith(p) for p in end_prefixes)
        ),
        len(lines),
    )
    return "\n".join(lines[start:end])


def review_order_section() -> str | None:
    """Return the text of code-reviewer.md's Review Order section, or None if the
    declared heading is absent (renamed/removed). None is a LOUD signal — callers
    distinguish it from "step missing within the section", never silently treat a
    renamed heading as an empty section.

    Boundary: the next H2 heading ('## '). The Review Order section's own '### N.' step
    headings must NOT be treated as boundaries (they are CONTENT of this section), so
    only '## ' ends it — distinct from dispatch_block(), whose blocks ARE '### '
    sections and therefore end at the next '### ' or '## '.
    """
    return extract_section(
        read_code_reviewer().splitlines(), REVIEW_ORDER_HEADING, ("## ",)
    )


def step_heading_positions(section: str) -> list[tuple[int, str]]:
    """Return [(line_index, heading_body), ...] for every '### ...' step heading in
    the Review Order section.

    POSITION (line_index) is the ordering, not the printed digit — a step physically
    later in the section is "after" regardless of how it is numbered. Matching step
    HEADINGS (not arbitrary body lines) keeps the position read tied to the structural
    step boundaries the document author controls.
    """
    headings: list[tuple[int, str]] = []
    for i, line in enumerate(section.splitlines()):
        if line.startswith("### "):
            headings.append((i, line[4:]))
    return headings


def first_step_pos_matching(
    headings: list[tuple[int, str]], tokens: tuple
) -> int | None:
    """Return the source line_index of the FIRST step heading whose body carries the
    concept, or None if no heading does. None means the step is absent — callers MUST
    treat None as a loud failure, never silently compare None.
    """
    for line_index, body in headings:
        if concept_present(body, tokens):
            return line_index
    return None


# --- Death tests -----------------------------------------------------------


class TestYinReviewerReviewsTestsDeath:
    def test_yin_reviewer_reviews_tests_as_subject(self):
        # DEATH [DC1-NO-TEST-REVIEW]: the yin reviewer must review TESTS (their
        # brittleness / tautology) as a first-class subject, not only implementation
        # correctness. Without it, brittle/tautological tests pass review unexamined.
        text = read_code_reviewer()
        for key, tokens in REVIEWER_REVIEWS_TESTS.items():
            assert concept_present(text, tokens), (
                f"SILENT FAILURE [DC1-NO-TEST-REVIEW]: code-reviewer.md does not "
                f"review tests as a subject (concept '{key}'). Brittle or tautological "
                f"tests pass review because no step inspects the tests themselves."
            )


class TestStructuralOrderingDeath:
    """Tests-before-correctness is an ORDER claim — asserted by POSITION, not label.

    A presence token ("review tests first") proves the test-review step is MENTIONED.
    It cannot prove the test-review step physically PRECEDES the correctness step: a
    future author can move the test-review step below correctness and keep the label.
    So here we read the two step headings' source positions and assert tests < corr.
    The reversed synthetic fixture proves the check goes RED when the order flips —
    which a presence token never would.
    """

    def test_tests_reviewed_before_correctness_structurally(self):
        # DEATH [DC2-ORDER-REVERSED, structural]: assert ORDER by source position of
        # the step headings, independent of label wording.
        section = review_order_section()
        assert section is not None, (
            f"SILENT FAILURE [DC2-NO-REVIEW-SECTION]: no section matching the declared "
            f"anchor '{REVIEW_ORDER_HEADING}' was found in code-reviewer.md. The "
            f"heading may have been RENAMED (update REVIEW_ORDER_HEADING) or removed. "
            f"The tests-before-correctness ordering invariant cannot be checked, so a "
            f"reversed order would go undetected."
        )
        headings = step_heading_positions(section)
        tests_pos = first_step_pos_matching(headings, STEP_TEST_REVIEW)
        corr_pos = first_step_pos_matching(headings, STEP_CORRECTNESS_REVIEW)
        assert tests_pos is not None, (
            "SILENT FAILURE [DC1/DC2]: no Review Order step heading reviews tests; the "
            "test-review step may have been removed or reworded out of recognition."
        )
        assert corr_pos is not None, (
            "SILENT FAILURE [DC2]: no Review Order step heading reviews correctness; "
            "the correctness step may have been removed or reworded out of recognition."
        )
        assert tests_pos < corr_pos, (
            f"SILENT FAILURE [DC2-ORDER-REVERSED, structural]: in code-reviewer.md the "
            f"test-review step is at line {tests_pos} and the correctness step at line "
            f"{corr_pos}. The invariant is tests < correctness. A rotten test reviewed "
            f"AFTER correctness has already forced a wrong implementation change."
        )

    def test_structural_check_reddens_on_synthetic_reversed_order(self):
        # MUTATE-TO-RED: construct a SYNTHETIC Review Order section where correctness
        # is reviewed BEFORE tests (step LABELS preserved, POSITIONS swapped) and
        # assert the structural check catches it. This is the proof a presence token
        # cannot give: same labels, wrong order, must go RED.
        reversed_section = (
            "## Review Order\n"
            "\n"
            "### 1. Implementation Correctness\n"
            "Review whether the code behaves correctly: logic errors, off-by-one,\n"
            "race conditions.\n"
            "\n"
            "### 2. Test Quality\n"
            "Review the tests for brittle (over-fit) and tautological (silent-green)\n"
            "assertions before trusting them.\n"
        )
        headings = step_heading_positions(reversed_section)
        tests_pos = first_step_pos_matching(headings, STEP_TEST_REVIEW)
        corr_pos = first_step_pos_matching(headings, STEP_CORRECTNESS_REVIEW)
        assert tests_pos is not None and corr_pos is not None, (
            "fixture sanity: both step headings must be locatable in the synthetic "
            "reversed section, or the mutate-to-red proof is vacuous."
        )
        # The reversed fixture keeps both LABELS, so a presence token would pass. The
        # structural invariant must FAIL (tests are after correctness here).
        assert not (tests_pos < corr_pos), (
            "The structural ordering check did NOT redden on a synthetic section with "
            "correctness reviewed before tests. The check is asserting labels, not "
            "positions — it cannot enforce the tests-before-correctness invariant."
        )

    def test_structural_check_passes_on_real_reviewer(self):
        # The same check that reddens on the synthetic reversed section must PASS on
        # the real code-reviewer.md (mutate-to-red is only meaningful if the real doc
        # is green).
        section = review_order_section()
        assert section is not None
        headings = step_heading_positions(section)
        tests_pos = first_step_pos_matching(headings, STEP_TEST_REVIEW)
        corr_pos = first_step_pos_matching(headings, STEP_CORRECTNESS_REVIEW)
        assert tests_pos is not None and corr_pos is not None
        assert tests_pos < corr_pos


class TestFixTheTestVerdictDeath:
    def test_reviewer_can_say_fix_the_test_not_implementation(self):
        # DEATH [DC3-NO-FIX-THE-TEST]: a reviewer must be able to say a FAILING test is
        # bound to the WRONG contract and the TEST must be fixed — NOT the
        # implementation bent to a rotten test. Without this verdict power, every
        # failing test is read as an implementation bug and the rotten test wins.
        text = read_code_reviewer()
        for key, tokens in REVIEWER_FIX_THE_TEST.items():
            assert concept_present(text, tokens), (
                f"SILENT FAILURE [DC3-NO-FIX-THE-TEST]: code-reviewer.md does not grant "
                f"the directional 'fix the test, not the implementation' verdict "
                f"(concept '{key}'). A test bound to the wrong contract bends the "
                f"implementation to itself."
            )


class TestCleanScarChallengeDeath:
    def test_reviewer_challenges_perfunctory_contract_label(self):
        # DEATH [DC7-CLEAN-SCAR]: a perfunctory contract LABEL (a slogan like
        # "# contract: it works") that maps to NO observable behavior / API / schema /
        # artifact / death-or-bug case must be CHALLENGED. If the reviewer cannot
        # reject it, the contract gate is satisfied by a slogan.
        text = read_code_reviewer()
        for key, tokens in REVIEWER_CHALLENGE_CLEAN_SCAR.items():
            assert concept_present(text, tokens), (
                f"SILENT FAILURE [DC7-CLEAN-SCAR]: code-reviewer.md does not challenge "
                f"a perfunctory/tautological contract label (concept '{key}'). A "
                f"slogan that maps to no observable behavior/API/schema/artifact/"
                f"death-case would satisfy the gate."
            )


class TestStructuralTestCouplingDeath:
    def test_code_quality_reviewer_reviews_structural_test_coupling(self):
        # DEATH [DC5-NO-STRUCTURAL-COUPLING]: the code-quality reviewer must own
        # STRUCTURAL test coupling — tests coupled to implementation structure
        # (internals, call sequence, private members). Without it, structurally
        # coupled tests pass review and rot the moment the structure changes.
        text = read_code_quality_reviewer()
        for key, tokens in REVIEWER_STRUCTURAL_TEST_COUPLING.items():
            assert concept_present(text, tokens), (
                f"SILENT FAILURE [DC5-NO-STRUCTURAL-COUPLING]: code-quality-reviewer.md "
                f"has no structural test-coupling guidance (concept '{key}'). Tests "
                f"coupled to implementation structure pass review."
            )


class TestReferralRoleSplitDeath:
    def test_code_quality_reviewer_refers_silent_rot_to_yin(self):
        # DEATH [DC6-NO-REFERRAL]: the role split requires the code-quality reviewer to
        # REFER silent-rot/correctness test concerns to the yin reviewer — not score
        # them itself. If the referral is missing, the split collapses: both reviewers
        # duplicate the same responsibility, or neither owns silent-rot in tests.
        text = read_code_quality_reviewer()
        for key, tokens in REVIEWER_REFERS_SILENT_ROT.items():
            assert concept_present(text, tokens), (
                f"SILENT FAILURE [DC6-NO-REFERRAL]: code-quality-reviewer.md does not "
                f"refer silent-rot/correctness concerns to the yin code reviewer "
                f"(concept '{key}'). The yin/structural role split collapses."
            )


# --- Dispatch propagation (DC4 — the core of this task) ----------------------
#
# The two reviewer dispatch BLOCKS live in dispatch-template.md under '### Yin
# reviewer' and '### Code Quality reviewer'. The gate is only REAL if BOTH blocks
# carry a test-quality review prompt — a reviewer agent that documents the rule while
# the dispatch never asks for it is exactly DC4. We scope to each block separately so
# a single prompt added to one block cannot satisfy both.

YIN_BLOCK_HEADING = "### yin reviewer"
QUALITY_BLOCK_HEADING = "### code quality reviewer"


def dispatch_block(heading: str) -> str | None:
    """Return the text of the named dispatch sub-block (from its '### ' heading to the
    next '### '/'## ' heading), or None if the declared heading is absent. None is a
    LOUD signal callers distinguish from "prompt missing within the block".

    Boundary: the next '### ' OR '## ' heading. Distinct from review_order_section():
    a dispatch block IS a '### ' section, so a sibling '### ' (the OTHER reviewer block)
    must END it — otherwise the two blocks would merge and a single prompt could satisfy
    both, defeating the per-block DC4 check. This is why both boundary prefixes are
    passed here but only '## ' for the Review Order section.
    """
    return extract_section(
        read_dispatch_template().splitlines(), heading, ("### ", "## ")
    )


class TestDispatchPropagationDeath:
    def test_yin_dispatch_block_asks_for_test_quality(self):
        # DEATH [DC4-DISPATCH-OMITTED, yin]: the yin reviewer dispatch block must carry
        # a test-quality review prompt, or the documented gate is never asked when the
        # yin reviewer is actually dispatched.
        block = dispatch_block(YIN_BLOCK_HEADING)
        assert block is not None, (
            f"SILENT FAILURE [DC4-NO-YIN-BLOCK]: no dispatch block matching "
            f"'{YIN_BLOCK_HEADING}' found in dispatch-template.md. The heading may have "
            f"been renamed; the per-block test-quality prompt cannot be verified."
        )
        for key, tokens in DISPATCH_TEST_QUALITY_PROMPT.items():
            assert concept_present(block, tokens), (
                f"SILENT FAILURE [DC4-DISPATCH-OMITTED, yin]: the Yin reviewer dispatch "
                f"block does not ask for test-quality review (concept '{key}'). The "
                f"gate is documented in the agent but never dispatched."
            )

    def test_quality_dispatch_block_asks_for_test_quality(self):
        # DEATH [DC4-DISPATCH-OMITTED, quality]: the code-quality reviewer dispatch
        # block must ALSO carry a test-quality review prompt (structural test coupling
        # is its lane), or the documented gate is never asked when it is dispatched.
        block = dispatch_block(QUALITY_BLOCK_HEADING)
        assert block is not None, (
            f"SILENT FAILURE [DC4-NO-QUALITY-BLOCK]: no dispatch block matching "
            f"'{QUALITY_BLOCK_HEADING}' found in dispatch-template.md. The heading may "
            f"have been renamed; the per-block test-quality prompt cannot be verified."
        )
        for key, tokens in DISPATCH_TEST_QUALITY_PROMPT.items():
            assert concept_present(block, tokens), (
                f"SILENT FAILURE [DC4-DISPATCH-OMITTED, quality]: the Code Quality "
                f"reviewer dispatch block does not ask for test-quality review "
                f"(concept '{key}'). The gate is documented in the agent but never "
                f"dispatched."
            )

    def test_both_blocks_distinct_and_both_carry_prompt(self):
        # DC4-SINGLE-BLOCK: the two blocks must be DISTINCT sections AND both carry the
        # prompt. If a single prompt in one block could satisfy a whole-document check,
        # the gate would be asked of only one reviewer. This pins that BOTH blocks
        # exist as separate sections and each independently carries the prompt.
        yin = dispatch_block(YIN_BLOCK_HEADING)
        quality = dispatch_block(QUALITY_BLOCK_HEADING)
        assert yin is not None and quality is not None, (
            "SILENT FAILURE [DC4]: one of the two reviewer dispatch blocks is missing; "
            "both must exist as distinct sections."
        )
        assert yin != quality, (
            "SILENT FAILURE [DC4]: the two dispatch blocks resolved to identical text "
            "— the section parser is not distinguishing them."
        )
        assert not missing_concepts(yin, DISPATCH_TEST_QUALITY_PROMPT), (
            "SILENT FAILURE [DC4]: the Yin dispatch block is missing the test-quality "
            "prompt."
        )
        assert not missing_concepts(quality, DISPATCH_TEST_QUALITY_PROMPT), (
            "SILENT FAILURE [DC4]: the Code Quality dispatch block is missing the "
            "test-quality prompt."
        )


# --- DC-DECOY / DC-POLARITY: the new tokens must be able to go RED ------------


class TestNewConceptsAreNotGreenByConstructionDeath:
    """DC-DECOY: the new reviewer-surface tokens must be able to go RED.

    The disease this feature has hit four times: a token that matches any document
    because it keys on a common word. The reviewer agents mention "test", "review",
    "contract", "coupling" everywhere. We build hostile decoy prose sprinkling those
    words WITHOUT the reviewer-surface concept and assert EVERY new concept is reported
    missing. Any concept covered here is green-by-construction and must be tightened.
    """

    def test_new_concepts_fail_on_hostile_decoy(self):
        decoy = (
            "Review the menu before lunch. The test kitchen serves coffee. Our "
            "contract with the cafe expires in spring. Coupling on the train is "
            "loose. We review attendance and test the soup. The implementation of "
            "the festival was a success. Refer a friend for a discount. A quality "
            "morning improves the day. Structure your weekend around rest."
        )
        new_groups = {
            **REVIEWER_REVIEWS_TESTS,
            **REVIEWER_FIX_THE_TEST,
            **REVIEWER_CHALLENGE_CLEAN_SCAR,
            **REVIEWER_STRUCTURAL_TEST_COUPLING,
            **REVIEWER_REFERS_SILENT_ROT,
            **DISPATCH_TEST_QUALITY_PROMPT,
        }
        covered = concepts_covered_by(decoy, new_groups)
        assert not covered, (
            "SILENT FAILURE [DC-DECOY]: these new reviewer-surface concepts were "
            f"reported covered by unrelated decoy prose: {sorted(covered)}. Their "
            "tokens key on common words and can never go red. Tighten them to "
            "intent-bearing tokens bound to the reviewer/test-contract concept."
        )

    def test_new_concept_tokens_are_not_pinned_headings(self):
        # A token must not BE a markdown heading string, or the check passes only while
        # a specific heading survives. Uses the authoritative shared scan.
        new_groups = {
            **REVIEWER_REVIEWS_TESTS,
            **REVIEWER_FIX_THE_TEST,
            **REVIEWER_CHALLENGE_CLEAN_SCAR,
            **REVIEWER_STRUCTURAL_TEST_COUPLING,
            **REVIEWER_REFERS_SILENT_ROT,
            **DISPATCH_TEST_QUALITY_PROMPT,
        }
        offenders = pinned_heading_offenders(new_groups)
        assert not offenders, (
            "SILENT FAILURE [DC-PINNED-HEADING]: a new concept token is a markdown "
            f"heading string: {offenders}. Tokens must be intent-bearing concepts."
        )

    def test_endorsing_wrong_practice_is_missing_fix_concept(self):
        # DC-POLARITY: REVIEWER_FIX_THE_TEST is DIRECTIONAL. A doc that ENDORSES the
        # WRONG practice — "always fix the test to make it pass" / "bend the test to
        # match the implementation" — must be reported MISSING, identical-looking word
        # presence notwithstanding. A bare 'fix the test' token would false-pass here.
        endorses_wrong = (
            "When a test fails, always fix the test to make it pass — adjust the "
            "assertions until they match whatever the implementation now returns. "
            "Bend the test to the implementation and move on."
        )
        assert not concepts_covered_by(endorses_wrong, REVIEWER_FIX_THE_TEST), (
            "SILENT FAILURE [DC-POLARITY]: REVIEWER_FIX_THE_TEST was reported covered "
            "by prose ENDORSING the wrong practice (bend the test to the "
            "implementation). The token proves word presence, not the "
            "test-not-implementation direction."
        )

    def test_mentioning_contract_is_missing_clean_scar_concept(self):
        # DC-POLARITY: REVIEWER_CHALLENGE_CLEAN_SCAR must require the reviewer to
        # REJECT a perfunctory label, not merely mention "contract". A doc that praises
        # contracts without challenging an empty one must be reported MISSING.
        mentions_contract = (
            "Every change should declare a contract. Contracts are good. A contract "
            "documents the intent of the code and helps the next developer. We like "
            "contracts and write them often."
        )
        assert not concepts_covered_by(
            mentions_contract, REVIEWER_CHALLENGE_CLEAN_SCAR
        ), (
            "SILENT FAILURE [DC-POLARITY]: REVIEWER_CHALLENGE_CLEAN_SCAR was reported "
            "covered by prose that merely MENTIONS 'contract' without challenging a "
            "perfunctory label. The token proves presence, not the reject-perfunctory "
            "direction."
        )

    def test_code_coupling_without_test_subject_is_missing(self):
        # DC-DECOY: REVIEWER_STRUCTURAL_TEST_COUPLING must bind coupling to TESTS as the
        # subject. A doc about CODE coupling (the quality reviewer's existing Coupling
        # principle) with no TEST subject must be reported MISSING — otherwise the new
        # concept is satisfied by the agent's pre-existing code-coupling prose.
        code_coupling_only = (
            "The Coupling principle: the danger of coupling is not the dependency, it "
            "is not knowing you depend. An invisible dependency between two modules "
            "cannot be debugged. Declare your dependencies."
        )
        assert not concepts_covered_by(
            code_coupling_only, REVIEWER_STRUCTURAL_TEST_COUPLING
        ), (
            "SILENT FAILURE [DC-DECOY]: REVIEWER_STRUCTURAL_TEST_COUPLING was reported "
            "covered by code-coupling prose with no TEST subject. The token must bind "
            "coupling to tests, or the agent's pre-existing Coupling principle "
            "satisfies it green-by-construction."
        )

    def test_generic_handoff_without_subject_is_missing_referral_concept(self):
        # DC-POLARITY: REVIEWER_REFERS_SILENT_ROT must bind the referral ACT to the
        # silent-rot / correctness / test SUBJECT. A code-quality-reviewer doc that
        # carries ONLY a generic hand-off to the yin reviewer (the Scope-Boundary
        # preamble line, no silent-rot / test subject) must be reported MISSING — else
        # an author could delete the specific "refer test silent-rot to the yin
        # reviewer" sentence and stay falsely covered via the generic line. The OLD bare
        # `refer ... code-reviewer` token false-passed here (mutate-to-red baseline).
        generic_handoff_only = (
            "## Scope Boundary\n"
            "This is not the yin code reviewer. You review structural coupling only.\n"
            "If you encounter any issue outside structural coupling, note it with a "
            "single line that must include file:line evidence:\n"
            "`→ Refer to samsara:code-reviewer at <file:line>: [brief description]`\n"
            "Do not score it. Hand it off and move on.\n"
        )
        assert not concepts_covered_by(
            generic_handoff_only, REVIEWER_REFERS_SILENT_ROT
        ), (
            "SILENT FAILURE [DC-POLARITY]: REVIEWER_REFERS_SILENT_ROT was reported "
            "covered by a GENERIC hand-off to the yin reviewer with no silent-rot / "
            "correctness / test subject. The token proves a referral exists, not that "
            "the referral is ABOUT test silent-rot. A future author could delete the "
            "specific referral sentence and the concept would silently stay covered."
        )

    def test_bare_test_quality_mention_is_missing_dispatch_concept(self):
        # DC-POLARITY: DISPATCH_TEST_QUALITY_PROMPT must require the dispatch block to
        # actually ASK for brittle / over-fit / tautological / silent-green / contract
        # review — not merely say "test quality". A block that says only "ensure good
        # test quality" (no enforcement content) must be reported MISSING — else an
        # author could gut the enforcement bullets, keep a "Test-Quality" heading, and
        # the gate would stay falsely covered while the dispatch no longer asks for the
        # review (DC4). The OLD bare `test[- ]quality` token false-passed here
        # (mutate-to-red baseline).
        bare_test_quality = (
            "### Yin reviewer\n"
            "    ## Test-Quality Review\n"
            "    Please ensure good test quality when you review this change. Make sure "
            "the tests are tidy and that overall test quality is high before approving.\n"
        )
        assert not concepts_covered_by(
            bare_test_quality, DISPATCH_TEST_QUALITY_PROMPT
        ), (
            "SILENT FAILURE [DC-POLARITY]: DISPATCH_TEST_QUALITY_PROMPT was reported "
            "covered by a block that merely says 'test quality' with no brittle / "
            "over-fit / tautological / silent-green / contract enforcement content. The "
            "token proves the phrase is present, not that the dispatch actually asks "
            "for the test-contract review that makes the gate real (DC4)."
        )


# --- Unit tests ------------------------------------------------------------


class TestYinReviewerProtocol:
    def test_reviews_tests_as_subject(self):
        text = read_code_reviewer()
        missing = missing_concepts(text, REVIEWER_REVIEWS_TESTS)
        assert not missing, (
            f"code-reviewer.md must review tests as a subject; missing: {missing}"
        )

    def test_can_fix_the_test_directionally(self):
        text = read_code_reviewer()
        missing = missing_concepts(text, REVIEWER_FIX_THE_TEST)
        assert not missing, (
            f"code-reviewer.md must grant the 'fix the test, not the implementation' "
            f"verdict; missing: {missing}"
        )

    def test_challenges_clean_scar(self):
        text = read_code_reviewer()
        missing = missing_concepts(text, REVIEWER_CHALLENGE_CLEAN_SCAR)
        assert not missing, (
            f"code-reviewer.md must challenge a perfunctory contract label; "
            f"missing: {missing}"
        )

    def test_tests_reviewed_before_correctness(self):
        section = review_order_section()
        assert section is not None, (
            f"code-reviewer.md has no section matching '{REVIEW_ORDER_HEADING}' "
            f"(heading may have been renamed)."
        )
        headings = step_heading_positions(section)
        tests_pos = first_step_pos_matching(headings, STEP_TEST_REVIEW)
        corr_pos = first_step_pos_matching(headings, STEP_CORRECTNESS_REVIEW)
        assert tests_pos is not None and corr_pos is not None, (
            "both the test-review and correctness step headings must be locatable in "
            "the Review Order section."
        )
        assert tests_pos < corr_pos


class TestCodeQualityReviewerProtocol:
    def test_reviews_structural_test_coupling(self):
        text = read_code_quality_reviewer()
        missing = missing_concepts(text, REVIEWER_STRUCTURAL_TEST_COUPLING)
        assert not missing, (
            f"code-quality-reviewer.md must review structural test coupling; "
            f"missing: {missing}"
        )

    def test_refers_silent_rot_to_yin(self):
        text = read_code_quality_reviewer()
        missing = missing_concepts(text, REVIEWER_REFERS_SILENT_ROT)
        assert not missing, (
            f"code-quality-reviewer.md must refer silent-rot to the yin reviewer; "
            f"missing: {missing}"
        )


class TestDispatchTemplateProtocol:
    def test_yin_block_carries_test_quality_prompt(self):
        block = dispatch_block(YIN_BLOCK_HEADING)
        assert block is not None
        missing = missing_concepts(block, DISPATCH_TEST_QUALITY_PROMPT)
        assert not missing, (
            f"Yin dispatch block must carry the test-quality prompt; missing: {missing}"
        )

    def test_quality_block_carries_test_quality_prompt(self):
        block = dispatch_block(QUALITY_BLOCK_HEADING)
        assert block is not None
        missing = missing_concepts(block, DISPATCH_TEST_QUALITY_PROMPT)
        assert not missing, (
            f"Code Quality dispatch block must carry the test-quality prompt; "
            f"missing: {missing}"
        )
