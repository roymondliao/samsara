"""Death tests for the test-contract reference (Task 1).

These run BEFORE the unit tests and target SILENT failure paths, not merely
"file is absent". The dangerous failures here are the ones that stay GREEN while
the protocol is hollow:

  DC-A The reference exists but guards only ONE pole (over-fit OR silent-green,
       not both). An implementer then writes the un-guarded failure shape and
       review never catches it.
  DC-B The reference exists but drops the unit-vs-death distinction, so the
       anti-over-fit language silently weakens death tests (which must keep
       pinning their exact failure mode).
  DC7  The evaluator refutes its own thesis by checking coverage with pinned
       heading strings / whole sentences. Renaming a heading while preserving
       the concept would then false-fail — proving the evaluator is over-fit.

Each test names the silent-failure mode it pins; that failure mode IS this death
test's contract, so (per the protocol) it is allowed to be exact here.
"""

from __future__ import annotations

from tests.test_contract_bound_tests._contract_tokens import (
    BRITTLENESS_FILTER,
    REFERENCE_CONCEPTS,
    SILENT_GREEN_GUARD,
    SNAPSHOT_GOLDEN,
    UNIT_VS_DEATH,
)
from tests.test_contract_bound_tests._token_lib import (
    ROOT,
    concept_present,
)

REFERENCE = ROOT / "references" / "test-contract.md"


def read_reference() -> str:
    return REFERENCE.read_text(encoding="utf-8")


class TestReferenceExistenceDeath:
    def test_missing_reference_is_a_silent_protocol_void(self):
        # DEATH: if references/test-contract.md does not exist, implementers have
        # NO canonical contract-bound test protocol, yet the implement skill may
        # still link to it — producing a dangling protocol that silently never
        # constrains anyone.
        assert REFERENCE.exists(), (
            "SILENT FAILURE [CONTRACT-REF-VOID]: references/test-contract.md is "
            "absent. The implement skill would reference a protocol that does not "
            "exist; implementers get no contract gate and no one is alerted."
        )


class TestBothPolesGuardedDeath:
    def test_overfit_pole_guarded(self):
        text = read_reference()
        # DEATH: a reference that only warns against silent-green but not brittle
        # over-fit lets brittle tests pass review (DC1).
        for key, tokens in BRITTLENESS_FILTER.items():
            assert concept_present(text, tokens), (
                f"SILENT FAILURE [DC1-OVERFIT]: reference does not guard the "
                f"over-fit pole concept '{key}'. Brittle tests pass review."
            )

    def test_silent_green_pole_guarded(self):
        text = read_reference()
        # DEATH: a reference that only warns against brittleness but not the
        # tautology pole lets silent-green tests pass review (DC2).
        for key, tokens in SILENT_GREEN_GUARD.items():
            assert concept_present(text, tokens), (
                f"SILENT FAILURE [DC2-SILENT-GREEN]: reference does not guard the "
                f"silent-green pole concept '{key}'. Tautological tests stay green."
            )


class TestUnitVsDeathDistinctionDeath:
    def test_death_tests_keep_exact_failure_pinning(self):
        text = read_reference()
        # DEATH: if the reference omits the unit-vs-death distinction, the
        # anti-over-fit rule bleeds onto death tests and someone "softens" a
        # death test that was correctly pinning its exact silent-failure mode.
        for key, tokens in UNIT_VS_DEATH.items():
            assert concept_present(text, tokens), (
                f"SILENT FAILURE [DC-UNIT-VS-DEATH]: reference does not preserve "
                f"concept '{key}'. Death tests could be weakened by anti-over-fit "
                f"language meant only for unit tests."
            )


class TestSnapshotsNotBannedOutrightDeath:
    def test_snapshots_permitted_under_normalization(self):
        text = read_reference()
        # DEATH: banning snapshots/golden tests outright is a silent degradation
        # — real contracts (CLI output, generated files) then go untested because
        # the only honest tool was forbidden. The reference must PERMIT them with
        # normalize-then-snapshot, not ban them.
        #
        # We source the check from the shared concept key, not an ad-hoc literal.
        # `normalize_before_snapshot` already requires the word "snapshot" in
        # proximity to a normalization verb, so it proves BOTH that snapshots are
        # discussed AND that they are permitted-with-normalization. A bare
        # token_present(text, "snapshot") literal would duplicate the key's intent
        # and could silently diverge from the shared token source.
        assert concept_present(text, SNAPSHOT_GOLDEN["normalize_before_snapshot"]), (
            "SILENT FAILURE [DC-SNAPSHOT-BAN]: reference lacks the "
            "normalize-then-snapshot concept. Snapshots are either banned outright "
            "or left unguarded (volatile fields make the snapshot brittle)."
        )


class TestEvaluatorIsNotOverfitDeath:
    """DC7: the evaluator must refuse to refute its own thesis.

    The coverage check must survive an honest heading rename. We prove this by
    rewriting the reference with every '## Heading' line mutated and confirming
    full concept coverage is preserved. If coverage drops, the evaluator was
    secretly keyed on heading text — over-fit — and the feature contradicts
    itself.
    """

    def _rename_headings(self, text: str) -> str:
        out = []
        for line in text.splitlines():
            if line.lstrip().startswith("#"):
                hashes = line[: len(line) - len(line.lstrip())] + "#" * (
                    len(line.lstrip()) - len(line.lstrip().lstrip("#"))
                )
                out.append(f"{hashes} Renamed Section {len(out)}")
            else:
                out.append(line)
        return "\n".join(out)

    def test_coverage_survives_heading_rename(self):
        text = read_reference()
        renamed = self._rename_headings(text)
        # Sanity: the rename actually changed the headings.
        assert renamed != text, "rename helper did not mutate any heading"

        # Stronger sanity: NO original heading text may survive the rename, or the
        # meta-test could false-pass (a token that secretly matched a surviving
        # heading would still be covered). Every '#'-led line in the renamed text
        # must be the placeholder form; no original heading words remain.
        original_headings = [
            line.lstrip().lstrip("#").strip()
            for line in text.splitlines()
            if line.lstrip().startswith("#")
        ]
        renamed_heading_lines = [
            line for line in renamed.splitlines() if line.lstrip().startswith("#")
        ]
        for line in renamed_heading_lines:
            body = line.lstrip().lstrip("#").strip()
            assert body.startswith("Renamed Section "), (
                f"heading line not rewritten to placeholder form: {line!r}"
            )
        for original in original_headings:
            assert original not in renamed_heading_lines, (
                f"original heading text survived the rename: {original!r}; the "
                "meta-test could false-pass on a heading-pinned token."
            )

        from tests.test_contract_bound_tests._token_lib import missing_concepts

        still_missing = missing_concepts(renamed, REFERENCE_CONCEPTS)
        assert not still_missing, (
            "SILENT FAILURE [DC7-OVERFIT-EVALUATOR]: concept coverage broke when "
            f"headings were renamed: {still_missing}. The tokens are pinned to "
            "heading text, not intent-bearing concepts. The evaluator is over-fit "
            "and refutes this feature's own thesis."
        )

    def test_no_concept_passes_on_unrelated_decoy_prose(self):
        # DEATH [DC-DECOY / silent-green-by-construction]: the disease this whole
        # feature exists to kill is a token that can NEVER fail — one that matches
        # any document because it is a common English word (e.g. "path", "version",
        # "spy", "snapshot") or a bare substring that proves only that a phrase
        # appears, not that the concept is asserted. Such a token reports its
        # concept "covered" even on prose that says nothing about the protocol.
        #
        # We construct a decoy that mentions NONE of the protocol concepts and
        # assert that the evaluator reports (nearly) every concept missing. If any
        # protocol concept is reported covered here, that concept's token is
        # green-by-construction and must be tightened. This is the forcing function
        # that would have caught the over-fit-pole findings.
        # The decoy is deliberately HOSTILE: it is unrelated prose that still
        # sprinkles in the exact common English words a green-by-construction token
        # would key on ("path", "port", "version", "date", "spy", "mock",
        # "snapshot", "golden", "assert less"). A healthy token set must reject
        # this prose for EVERY concept; any concept reported covered here is keyed
        # on a word, not the protocol concept. A clean, word-free decoy would
        # false-pass and defeat the purpose of this guard.
        decoy = (
            "The file path to the config version was set on port 8080 by the given "
            "date. We pointed a spy camera at the golden retriever, asked it to "
            "mock the cat, and took a snapshot for the album. Please assert less "
            "drama at the dinner table; the random id on the receipt was long."
        )
        from tests.test_contract_bound_tests._token_lib import missing_concepts

        missing = set(missing_concepts(decoy, REFERENCE_CONCEPTS))
        covered = set(REFERENCE_CONCEPTS) - missing
        assert not covered, (
            "SILENT FAILURE [DC-DECOY]: these concepts were reported covered by "
            f"unrelated decoy prose: {sorted(covered)}. Their tokens are "
            "green-by-construction (match common words / bare substrings) and can "
            "never go red. Tighten them to intent-bearing tokens."
        )

    def test_known_overfit_pole_concepts_fail_on_decoy(self):
        # DEATH [DC-DECOY-MIN]: a sharper, named-floor version of the test above.
        # Even if some incidental concept slipped through, the concepts the review
        # findings named MUST be reported missing on the decoy: the snapshot, spy,
        # volatile-field, and assert-less concepts. This pins findings 1-3
        # directly and survives future additions to REFERENCE_CONCEPTS.
        decoy = (
            "Plain unrelated prose: a path, a port, a version, a date, a spy, a "
            "mock, a snapshot, a golden hour, and a note to assert less at lunch."
        )
        from tests.test_contract_bound_tests._token_lib import missing_concepts

        missing = set(missing_concepts(decoy, REFERENCE_CONCEPTS))
        must_be_missing = {
            "not_assert_less",
            "volatile_fields",
            "normalize_before_snapshot",
            "interaction_is_the_feature",
        }
        not_caught = must_be_missing - missing
        assert not not_caught, (
            "SILENT FAILURE [DC-DECOY-MIN]: these named concepts were NOT reported "
            f"missing on unrelated prose: {sorted(not_caught)}. Their tokens are "
            "green-by-construction — the exact disease findings 1-3 named."
        )

    def test_no_token_is_a_pinned_heading_string(self):
        # The tokens themselves must not BE heading strings. A literal '## ' token
        # would mean the check passes only while a specific heading survives. The
        # scan is the authoritative shared `pinned_heading_offenders` — the SAME
        # implementation task-2 (and tasks 3-6) reuse, so the heading-pin guard
        # cannot drift between evaluators.
        from tests.test_contract_bound_tests._contract_tokens import (
            REFERENCE_CONCEPTS as cm,
        )
        from tests.test_contract_bound_tests._token_lib import (
            pinned_heading_offenders,
        )

        offenders = pinned_heading_offenders(cm)
        assert not offenders, (
            "SILENT FAILURE [DC7-PINNED-HEADING]: a concept token is a markdown "
            f"heading string: {offenders}. Tokens must be intent-bearing concepts "
            "that survive a rename, never heading text."
        )
