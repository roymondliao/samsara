"""Death tests for the CONSOLIDATED coverage manifest + self-refuting meta-test (Task 6).

Tasks 1-5 each wired the contract-bound-unit-test protocol into ONE instruction
surface and gave that surface its own evaluator. But nothing yet asserts the FULL
SET of surfaces is covered: a future edit could delete an entire evaluator file (or
an entire surface) and every remaining test would still pass — the protocol would
silently drop off a surface and ship green. Task-6 adds a consolidated guard:

  * COVERAGE MANIFEST (test_coverage_manifest.py): one list naming every required
    instruction surface paired with the concept groups it must carry, plus a
    COMPLETENESS check that the manifest's surface set equals a canonical expected
    set — so dropping a surface from the manifest reddens.

  * SELF-REFUTING META-TEST (this file): the evaluator suite must not itself commit
    the over-fit sin it exists to kill. Two guards:
      (a) ROUTING: every `*_test_contract.py` / coverage evaluator imports from
          `_token_lib` (the shared engine) and routes concept coverage through the
          shared helpers (concept_present / missing_concepts / concepts_covered_by). An
          evaluator that stops importing the shared engine has gone private and can drift.
      (b) HEADING-AS-COVERAGE: no evaluator asserts CONCEPT COVERAGE via a pinned
          `## heading` string literal. CRITICAL NUANCE: several evaluators
          legitimately use `## heading` strings as SECTION ANCHORS to LOCATE/slice a
          section before checking concepts within it (module-level constants like
          REVIEW_ORDER_HEADING, SUPPORT_FILES_HEADING, EXECUTION_ORDER_HEADING,
          YIN_BLOCK_HEADING). Those are locators, NOT coverage-by-heading. The
          meta-test must DISTINGUISH a locator from a heading asserted AS coverage.

These death tests run BEFORE the unit tests and target SILENT failure paths — the
ones that stay GREEN while the consolidated guard has rotted:

  DC-MANIFEST-INCOMPLETE A required surface is dropped from the manifest list →
      that surface's protocol can rot undetected (no row checks it). Pinned by a
      synthetic manifest missing a row, which must redden the completeness check.
  DC-MANIFEST-EXTRA The manifest names a surface NOT in the canonical set (typo /
      stale path) → a row checks a file that is not a real protocol surface, a false
      sense of coverage. Pinned by a synthetic manifest with a bogus row.
  DC-ROUTING-PRIVATE An evaluator stops importing `_token_lib` / routing
      through the shared helpers → it has gone private and the central engine
      contract no longer binds it. Pinned by the routing scan over a synthetic
      "private" evaluator source.
  DC-HEADING-AS-COVERAGE An evaluator asserts coverage via a pinned `## heading`
      string used as the coverage assertion (not as a section locator) → the exact
      over-fit this feature kills. Pinned by an AST scan that reddens on a synthetic
      heading-as-coverage evaluator but stays green on a synthetic locator-only one.

Each death test names the silent-failure mode it pins; that failure mode IS this
death test's contract, so (per the protocol) it is allowed to be exact here.
"""

from __future__ import annotations

from tests.test_contract_bound_tests._token_lib import ROOT
from tests.test_contract_bound_tests.test_coverage_manifest import (
    CANONICAL_REQUIRED_SURFACES,
    COVERAGE_MANIFEST,
    HEADING_LOCATOR_CONSTANT_SUFFIX,
    SHARED_COVERAGE_HELPERS,
    SHARED_TOKEN_MODULE,
    _scan_heading_as_coverage,
    heading_as_coverage_offenders,
    manifest_surface_set,
    routing_offenders,
)


# --- DC-MANIFEST-INCOMPLETE / DC-MANIFEST-EXTRA -----------------------------


class TestManifestCompletenessDeath:
    """The manifest's surface set must EQUAL the canonical expected set.

    A subset (a surface dropped) or a superset (a stale/typo path) both mean the
    consolidated guard no longer faithfully tracks the protocol's surfaces.
    """

    def test_real_manifest_surface_set_equals_canonical(self):
        # DEATH [DC-MANIFEST-INCOMPLETE/EXTRA]: the live manifest must name EXACTLY
        # the canonical required surfaces — no more, no less. If a future edit deletes
        # a row (drops a surface) or adds a stale row, this reddens.
        manifest_set = manifest_surface_set(COVERAGE_MANIFEST)
        assert manifest_set == CANONICAL_REQUIRED_SURFACES, (
            "SILENT FAILURE [DC-MANIFEST-INCOMPLETE/EXTRA]: the coverage manifest's "
            f"surface set does not equal the canonical required set.\n"
            f"  missing from manifest (dropped surface): "
            f"{sorted(CANONICAL_REQUIRED_SURFACES - manifest_set)}\n"
            f"  extra in manifest (stale/typo path): "
            f"{sorted(manifest_set - CANONICAL_REQUIRED_SURFACES)}\n"
            "A dropped surface means its protocol can rot with no row checking it."
        )

    def test_completeness_check_reddens_when_a_surface_is_dropped(self):
        # MUTATE-TO-RED: simulate a future edit that DROPS a row from the manifest and
        # assert the completeness comparison catches it. This is the proof a bare
        # "loop over the rows" check cannot give: the row is simply gone, so a loop
        # would happily pass — only the SET comparison against the canonical set
        # reddens.
        assert COVERAGE_MANIFEST, "fixture sanity: manifest must be non-empty"
        mutated = COVERAGE_MANIFEST[1:]  # drop the first surface row
        mutated_set = manifest_surface_set(mutated)
        assert mutated_set != CANONICAL_REQUIRED_SURFACES, (
            "SILENT FAILURE [DC-MANIFEST-INCOMPLETE]: dropping a surface row from the "
            "manifest did NOT change the surface set vs the canonical set. The "
            "completeness check cannot detect a dropped surface — it is not comparing "
            "against a canonical expected set."
        )

    def test_completeness_check_reddens_on_stale_extra_surface(self):
        # MUTATE-TO-RED: simulate a stale/typo extra row (a path not in the canonical
        # set) and assert the completeness comparison catches it.
        bogus = ROOT / "skills" / "planning" / "does-not-exist.md"
        mutated_set = manifest_surface_set(COVERAGE_MANIFEST) | {bogus}
        assert mutated_set != CANONICAL_REQUIRED_SURFACES, (
            "SILENT FAILURE [DC-MANIFEST-EXTRA]: adding a bogus surface to the manifest "
            "did NOT change the surface set vs the canonical set. The completeness "
            "check cannot detect a stale/typo extra surface."
        )

    def test_every_canonical_surface_is_a_real_file(self):
        # A canonical surface that does not exist on disk is a dead anchor: the
        # manifest would silently never check it. The canonical set is the source of
        # truth, so every entry must be a real file.
        for surface in CANONICAL_REQUIRED_SURFACES:
            assert surface.is_file(), (
                f"SILENT FAILURE [DC-MANIFEST-EXTRA]: canonical required surface "
                f"{surface} is not a file on disk. The manifest would check a path "
                f"that does not exist, masking a moved/renamed surface."
            )


# --- DC-ROUTING-PRIVATE ------------------------------------------------------


class TestEvaluatorRoutingDeath:
    """Every coverage evaluator must import `_token_lib` and route concept
    coverage through the shared helpers. An evaluator that goes private can drift
    from the single canonical matching engine — the disease the shared module prevents.
    """

    def test_every_evaluator_imports_shared_tokens_and_routes_through_helpers(self):
        # DEATH [DC-ROUTING-PRIVATE]: scan every coverage evaluator's source. Each
        # must (a) import from `_token_lib` and (b) reference at least one shared
        # coverage helper. An evaluator that stops doing both has gone private.
        offenders = routing_offenders()
        assert not offenders, (
            "SILENT FAILURE [DC-ROUTING-PRIVATE]: these coverage evaluators do not "
            f"import from {SHARED_TOKEN_MODULE} and/or do not route coverage through "
            f"the shared helpers {sorted(SHARED_COVERAGE_HELPERS)}: {offenders}. An "
            "evaluator that goes private can drift from the canonical token source."
        )

    def test_routing_scan_reddens_on_synthetic_private_evaluator(self):
        # MUTATE-TO-RED: a synthetic evaluator that does its own coverage with raw
        # `in` checks and NEVER imports the shared tokens must be flagged. Proves the
        # routing scan is not green-by-construction. Feeds the synthetic source through
        # the SAME production `routing_offenders` algorithm (no parallel re-derivation
        # that could drift from the real scan).
        private_source = (
            "def read_surface():\n"
            "    return open('agents/implementer.md').read()\n"
            "\n"
            "def test_contract_present():\n"
            "    text = read_surface()\n"
            "    assert 'contract-bound unit test' in text.lower()\n"
        )
        offenders = routing_offenders({"synthetic_private.py": private_source})
        assert offenders == ["synthetic_private.py"], (
            "The routing scan did NOT flag a synthetic private evaluator that does raw "
            "`in` coverage and never imports the shared tokens. The scan cannot detect "
            f"a privatized evaluator. (imports {SHARED_TOKEN_MODULE} / routes through "
            f"{sorted(SHARED_COVERAGE_HELPERS)} expected to BOTH be false.)"
        )


# --- DC-HEADING-AS-COVERAGE --------------------------------------------------


class TestHeadingAsCoverageMetaDeath:
    """No evaluator may assert CONCEPT COVERAGE via a pinned `## heading` literal.

    The subtle part: a `## heading` literal assigned to a module-level LOCATOR
    constant (REVIEW_ORDER_HEADING, SUPPORT_FILES_HEADING, ...) and used to LOCATE a
    section is ALLOWED. A `## heading` literal used AS the coverage assertion (e.g.
    `assert "## Foo" in read_surface()`) is the over-fit BUG. The meta-test must
    distinguish them; these death tests pin both the allow and the reject side.
    """

    def test_no_evaluator_asserts_coverage_via_pinned_heading(self):
        # DEATH [DC-HEADING-AS-COVERAGE]: scan every evaluator's AST for a `## heading`
        # string literal used as a COVERAGE assertion against a surface read, rather
        # than as a section-locator constant. Any offender is the over-fit this feature
        # exists to kill.
        offenders = heading_as_coverage_offenders()
        assert not offenders, (
            "SILENT FAILURE [DC-HEADING-AS-COVERAGE]: an evaluator asserts concept "
            f"coverage via a pinned '## heading' literal instead of routing through "
            f"shared concept tokens: {offenders}. A heading literal makes the check "
            "pass only while that exact heading survives — over-fit by construction. "
            f"Section LOCATOR constants (names ending '{HEADING_LOCATOR_CONSTANT_SUFFIX}') "
            "are exempt; use one of those to slice a section, then check concepts "
            "within it via the shared tokens."
        )

    def test_meta_scan_reddens_on_synthetic_heading_as_coverage(self):
        # MUTATE-TO-RED: a synthetic evaluator that asserts a `## heading` IS the
        # coverage (`assert "## Foo" in text`) must be flagged by the scan.
        bug_source = (
            "def read_surface():\n"
            "    return ''\n"
            "\n"
            "def test_has_section():\n"
            "    text = read_surface()\n"
            "    assert '## Review Order' in text\n"
        )
        offenders = _scan_heading_as_coverage(bug_source, "synthetic_bug.py")
        assert offenders, (
            "The meta-scan did NOT flag a synthetic evaluator that asserts a "
            "'## heading' literal IS the coverage. It cannot detect the over-fit bug."
        )

    def test_meta_scan_stays_green_on_synthetic_locator_constant(self):
        # MUTATE-TO-GREEN (the NUANCE): a synthetic evaluator that assigns a
        # `## heading` to a module-level LOCATOR constant and uses it to SLICE a
        # section (never as a coverage assertion) must NOT be flagged. This is the
        # legitimate pattern tasks 3/4 use; flagging it would be a false positive that
        # forces removing valid section anchors.
        locator_source = (
            "REVIEW_ORDER_HEADING = '## review order'\n"
            "\n"
            "def section(lines):\n"
            "    start = next(i for i, ln in enumerate(lines)\n"
            "                 if ln.strip().lower().startswith(REVIEW_ORDER_HEADING))\n"
            "    return lines[start:]\n"
        )
        offenders = _scan_heading_as_coverage(locator_source, "synthetic_locator.py")
        assert not offenders, (
            "The meta-scan FALSELY flagged a legitimate section-locator constant "
            f"('{HEADING_LOCATOR_CONSTANT_SUFFIX}'-named) used to slice a section. The "
            "scan does not distinguish a locator from a coverage assertion, so it "
            "would force removing valid section anchors."
        )
