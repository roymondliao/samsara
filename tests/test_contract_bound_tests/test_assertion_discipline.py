"""Evaluator + death tests for the assertion-discipline section (iteration-fix-2).

Across all six tasks of contract-bound-unit-tests, code review caught the SAME
failure-mode family six times: an assertion that proves a topic is *mentioned*
rather than *asserted in the right direction*. The reference's Contract Gate and
both-poles material teach the principle; this iteration pins the five CONCRETE
sub-rules the build proved necessary, in a new reference section, and checks the
reference carries them via the `ASSERTION_DISCIPLINE` concept group.

The unifying principle (a deepening of the Contract Gate, not a separate topic):
**an assertion is only as strong as its weakest clause, and must be able to fail
in the DIRECTION the contract cares about.** The five sub-rules:

  1. weakest-token-in-an-OR floor   — the loosest token sets the floor.
  2. presence-not-polarity          — keyword match without direction.
  3. green-by-construction          — a common-word token can never go red.
  4. order-by-label                 — ordering by label presence, not position.
  5. boundary bleed                 — a loose [^.] stop class leaks across blocks.

Death tests run BEFORE the unit tests and target the SILENT failure paths — the
ones that stay GREEN while the discipline has rotted. CRITICAL self-discipline:
this is the worst possible place to commit the very bugs it documents, so the new
tokens MUST themselves obey all five rules. The hostile-decoy and wrong-direction
death tests below are the forcing function that proves they do.

Each death test names the silent-failure mode it pins; that failure mode IS this
death test's contract, so (per the protocol) it is allowed to be exact here.
"""

from __future__ import annotations

from tests.test_contract_bound_tests._contract_tokens import (
    ASSERTION_DISCIPLINE,
)
from tests.test_contract_bound_tests._token_lib import (
    ROOT,
    concept_present,
    concepts_covered_by,
    missing_concepts,
    pinned_heading_offenders,
)

REFERENCE = ROOT / "references" / "test-contract.md"


def read_reference() -> str:
    return REFERENCE.read_text(encoding="utf-8")


# --- Death tests -----------------------------------------------------------


class TestAllFiveSubRulesPresentDeath:
    def test_reference_carries_every_assertion_discipline_concept(self):
        # DEATH [DC-DISCIPLINE-VOID]: the reference teaches the both-poles principle
        # but, without these five concrete sub-rules, a future test author writes a
        # weakest-OR-floor / presence-not-polarity / green-by-construction assertion,
        # it passes green, and review catches the SAME family a SEVENTH time by hand.
        # The whole point of this fix is to make that catch automatable; a reference
        # that drops any sub-rule silently re-opens the hole.
        text = read_reference()
        missing = missing_concepts(text, ASSERTION_DISCIPLINE)
        assert not missing, (
            "SILENT FAILURE [DC-DISCIPLINE-VOID]: references/test-contract.md does "
            f"not carry assertion-discipline concept(s): {missing}. The five "
            "sub-rules the build proved necessary are not codified; the failure-mode "
            "family stays catchable only by hand."
        )


class TestHostileDecoyDeath:
    """RULE 3 applied to THIS group: the new tokens must not be green-by-construction.

    The disease this whole feature kills is a token that can NEVER fail because it
    keys on a common word. The five discipline concepts use words a careless author
    WOULD key on bare ("weakest", "polarity", "direction", "order", "before",
    "boundary", "regex", "common word", "decoy"). A healthy token set rejects
    unrelated prose that sprinkles ALL of them for EVERY concept.
    """

    def test_no_discipline_concept_covered_by_hostile_decoy(self):
        # DEATH [DC-DISCIPLINE-DECOY]: hostile prose sprinkling the exact keywords a
        # green-by-construction token would key on. If ANY discipline concept is
        # reported covered here, that concept's token keys on a word, not the rule,
        # and can never go red — the exact bug this section documents.
        decoy = (
            "The weakest swimmer in the loosest division took the regex of the law "
            "into his own hands at the boundary of the county. Polarity of the "
            "magnet pointed in a strange direction. He gave the order to march "
            "before dawn. A common word for the structural beam is joist. The decoy "
            "duck floated near the index of the river. Tests of patience followed "
            "and the contract was signed on that date with a green pen."
        )
        covered = concepts_covered_by(decoy, ASSERTION_DISCIPLINE)
        assert not covered, (
            "SILENT FAILURE [DC-DISCIPLINE-DECOY]: these discipline concepts were "
            f"reported covered by unrelated decoy prose: {sorted(covered)}. Their "
            "tokens are green-by-construction (key on common words / bare substrings) "
            "and can never go red. Tighten them to bind keyword to DIRECTION."
        )


class TestWrongDirectionDecoyDeath:
    """RULE 2 applied to THIS group: directional concepts must check DIRECTION.

    For each of the five polarity-bearing rules, a decoy that uses the REAL phrase in
    the WRONG direction (endorsing the bad practice, or stating the bad practice as
    fine) must be reported MISSING the concept. If it is reported covered, the token
    proves only PRESENCE of the keyword, not the rule's polarity. The two newest
    decoys (green_by_construction, presence_not_polarity) close the self-refuting hole
    that iteration-fix-2 review found: those concepts' first tokens used to be the bare
    compound phrase, which fired on the section heading whether the doc taught the rule
    or endorsed the bug — so all five polarity-bearing rules now have a dedicated
    wrong-direction decoy here.
    """

    def test_endorsing_green_by_construction_is_missing_concept(self):
        # WRONG DIRECTION: a doc that ENDORSES green-by-construction tokens (the bug)
        # must NOT satisfy green_by_construction, which exists to WARN against them.
        # This is the self-refuting hole: the old bare rx("green-by-construction") fired
        # on this endorsement identically to the real teaching section.
        decoy = (
            "green-by-construction tokens are fine here; the concept is obvious so a "
            "bare common-word token is acceptable and saves effort."
        )
        assert not concept_present(
            decoy, ASSERTION_DISCIPLINE["green_by_construction"]
        ), (
            "SILENT FAILURE [DC-DISCIPLINE-POLARITY-3]: a doc ENDORSING green-by-"
            "construction satisfied green_by_construction. The token proves keyword "
            "presence (the heading phrase), not the never-go-red WARNING direction."
        )

    def test_endorsing_presence_not_polarity_is_missing_concept(self):
        # WRONG DIRECTION: a doc that ENDORSES presence-not-polarity tokens (the bug)
        # must NOT satisfy presence_not_polarity, which exists to WARN against them.
        decoy = (
            "presence-not-polarity is acceptable when the rule is obvious; just match "
            "the keyword and move on, no need to bind it to a direction."
        )
        assert not concept_present(
            decoy, ASSERTION_DISCIPLINE["presence_not_polarity"]
        ), (
            "SILENT FAILURE [DC-DISCIPLINE-POLARITY-2]: a doc ENDORSING presence-not-"
            "polarity satisfied presence_not_polarity. The token proves keyword "
            "presence (the heading phrase), not the reject-wrong-direction polarity."
        )

    def test_endorsing_weakest_floor_is_missing_concept(self):
        # WRONG DIRECTION: a doc that ENDORSES letting the loosest token stand (the
        # bug) must NOT satisfy weakest_clause_sets_the_floor, which exists to WARN
        # against it.
        decoy = (
            "Feel free to add a loose alternative token to any OR tuple; the weakest "
            "one is a convenient catch-all and keeps the test passing."
        )
        assert not concept_present(
            decoy, ASSERTION_DISCIPLINE["weakest_clause_sets_the_floor"]
        ), (
            "SILENT FAILURE [DC-DISCIPLINE-POLARITY-1]: a doc ENDORSING the weakest-OR "
            "floor satisfied weakest_clause_sets_the_floor. The token proves keyword "
            "presence, not the WARNING direction."
        )

    def test_endorsing_label_ordering_is_missing_concept(self):
        # WRONG DIRECTION: a doc that says a label-presence token is FINE for ordering
        # (the bug) must NOT satisfy order_by_structural_position.
        decoy = (
            "To assert that X comes before Y, just check that both labels are present "
            "in the document; a label-presence order check is good enough."
        )
        assert not concept_present(
            decoy, ASSERTION_DISCIPLINE["order_by_structural_position"]
        ), (
            "SILENT FAILURE [DC-DISCIPLINE-POLARITY-4]: a doc ENDORSING label-presence "
            "ordering satisfied order_by_structural_position. The token proves keyword "
            "presence, not the STRUCTURAL-position direction."
        )

    def test_endorsing_loose_stop_class_is_missing_concept(self):
        # WRONG DIRECTION: a doc that says a loose stop class is fine (the bug) must
        # NOT satisfy boundary_bleed_tight_clause unless it names the bug or the cure.
        decoy = (
            "A proximity regex with a generous wildcard span is convenient and reads "
            "well; let the words be as far apart as the paragraph allows."
        )
        assert not concept_present(
            decoy, ASSERTION_DISCIPLINE["boundary_bleed_tight_clause"]
        ), (
            "SILENT FAILURE [DC-DISCIPLINE-POLARITY-5]: a doc ENDORSING a loose "
            "proximity span satisfied boundary_bleed_tight_clause. The token proves "
            "keyword presence, not the tight-clause / bleed-warning direction."
        )


class TestNoPinnedHeadingDeath:
    def test_no_discipline_token_is_a_pinned_heading_string(self):
        # DEATH [DC-DISCIPLINE-PINNED-HEADING]: a token that IS a markdown heading
        # string would pass only while that heading survives — the over-fit this
        # feature kills. Reuse the authoritative shared scanner so the guard cannot
        # drift from the other evaluators.
        offenders = pinned_heading_offenders(ASSERTION_DISCIPLINE)
        assert not offenders, (
            "SILENT FAILURE [DC-DISCIPLINE-PINNED-HEADING]: a discipline token is a "
            f"markdown heading string: {offenders}. Tokens must be intent-bearing, "
            "not heading text."
        )


# --- Unit tests ------------------------------------------------------------


class TestAssertionDisciplineSection:
    def test_section_present_via_intent_tokens(self):
        # The reference carries the discipline section. Checked by intent-bearing
        # concepts (not a heading string), so an honest reflow survives.
        text = read_reference()
        for key, tokens in ASSERTION_DISCIPLINE.items():
            assert concept_present(text, tokens), (
                f"reference lacks assertion-discipline concept '{key}'"
            )

    def test_group_is_nonempty_and_keyed_by_concept(self):
        assert ASSERTION_DISCIPLINE, "ASSERTION_DISCIPLINE is empty"
        for key, tokens in ASSERTION_DISCIPLINE.items():
            assert isinstance(tokens, tuple) and tokens, f"{key} has no tokens"
