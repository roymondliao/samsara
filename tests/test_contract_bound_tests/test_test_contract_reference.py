"""Evaluator (unit) tests for references/test-contract.md (Task 1).

These assert the *content contract* of the canonical reference via the shared
concept tokens in `_contract_tokens.py`. They never pin a heading string or a
whole sentence: coverage is "is the concept present in any honest phrasing", so
an editor may rewrite the prose freely as long as the protocol's concepts remain.

Death tests for the silent-failure paths live in the sibling
`test_test_contract_reference_death.py` and run first.
"""

from __future__ import annotations

from pathlib import Path

from tests.test_contract_bound_tests._contract_tokens import (
    REFERENCE_CONCEPTS,
)
from tests.test_contract_bound_tests._token_lib import (
    concept_present,
    missing_concepts,
)

ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT / "references" / "test-contract.md"


def read_reference() -> str:
    return REFERENCE.read_text(encoding="utf-8")


class TestReferenceCoversEveryConcept:
    def test_reference_exists(self):
        assert REFERENCE.exists(), f"missing canonical reference: {REFERENCE}"

    def test_all_canonical_concepts_present(self):
        text = read_reference()
        missing = missing_concepts(text, REFERENCE_CONCEPTS)
        assert not missing, (
            "references/test-contract.md does not cover required concepts "
            f"(checked via shared tokens, not heading text): {missing}"
        )


class TestWorkedExamplesPresent:
    """Acceptance: the reference must include concrete examples, not just rules.

    Checked by intent-bearing markers (example fences + the example's defining
    concept), never by the exact example text.
    """

    def test_has_code_examples(self):
        text = read_reference()
        assert "```" in text, "reference contains no fenced example blocks"

    def test_normalize_then_snapshot_example(self):
        text = read_reference()
        assert concept_present(text, REFERENCE_CONCEPTS["normalize_before_snapshot"]), (
            "no normalize-then-snapshot worked example"
        )

    def test_minimum_contract_workflow_example(self):
        text = read_reference()
        assert concept_present(
            text, REFERENCE_CONCEPTS["minimum_contract"]
        ) and concept_present(text, REFERENCE_CONCEPTS["no_single_hardcoded_path"]), (
            "no minimum-contract / multi-path workflow worked example"
        )

    def test_boundary_spy_example(self):
        text = read_reference()
        assert concept_present(
            text, REFERENCE_CONCEPTS["interaction_is_the_feature"]
        ), "no boundary-spy (interaction-is-the-feature) worked example"


class TestSharedTokenSourceIsStable:
    """The token module is the cross-task contract; guard its shape minimally."""

    def test_concept_map_is_nonempty_and_keyed_by_concept(self):
        assert REFERENCE_CONCEPTS, "REFERENCE_CONCEPTS is empty"
        # Every value is a non-empty tuple of alternative phrasings.
        for key, tokens in REFERENCE_CONCEPTS.items():
            assert isinstance(tokens, tuple) and tokens, f"{key} has no tokens"
