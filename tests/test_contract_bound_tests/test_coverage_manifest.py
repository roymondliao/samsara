"""CONSOLIDATED coverage manifest + self-refuting meta-test (Task 6).

This is the final, consolidating evaluator of the contract-bound-unit-test feature.
Tasks 1-5 each wired the protocol into ONE instruction surface and gave that surface
its own focused evaluator (reference, implementer, implement-skill, reviewers +
dispatch, planning). Each of those evaluators independently checks its OWN surface.
What none of them does is assert that the FULL SET of surfaces is covered: delete an
entire evaluator file, or stop carrying the protocol on a whole surface, and every
remaining test still passes — the protocol silently drops off a surface and ships
green.

Two consolidated guards close that gap:

  1. COVERAGE MANIFEST. `COVERAGE_MANIFEST` lists EVERY required instruction surface
     paired with the concept groups it must carry, checked via the SHARED tokens
     (`missing_concepts` / `concepts_covered_by`) — never headings, line numbers, or
     incidental prose. A COMPLETENESS check asserts the manifest's surface set equals
     `CANONICAL_REQUIRED_SURFACES`, so dropping (or adding a stale) surface reddens.
     The dispatch template is checked PER BLOCK (the gate must be asked of BOTH
     reviewers), mirroring task-4's per-block scope.

  2. SELF-REFUTING META-TEST. The evaluator suite must not commit the over-fit sin it
     exists to kill. `routing_offenders()` asserts every coverage evaluator imports
     `_token_lib` (the shared engine) and routes coverage through the shared helpers;
     `heading_as_coverage_offenders()` AST-scans every evaluator and flags a
     `## heading` literal used AS a coverage assertion — while EXEMPTING `## heading`
     literals that are section-LOCATOR constants (REVIEW_ORDER_HEADING, ...) used to
     slice a section before checking concepts within it.

SCOPE (hard): the manifest covers the instruction surfaces plus
`skills/planning/task-format.md`. It NEVER globs historical task files under
`changes/` — task-5's evaluator pins that non-enforcement for its own surface; this
consolidated guard inherits the same scope by listing single named files only.

Death tests for the silent-failure paths live in the sibling
`test_coverage_manifest_death.py` and run first.
"""

from __future__ import annotations

import ast

from tests.test_contract_bound_tests._contract_tokens import (
    # Reference surface
    REFERENCE_CONCEPTS,
    # Implementer surface
    CONTRACT_BOUND_UNIT,
    FIX_THE_TEST,
    # Implement-skill surface
    CONTRACT_PRINCIPLE_AND_POINTER,
    CONTRACT_REFERENCE_SUPPORT_FILE,
    DEATH_TEST_FIRST,
    GATE_BEFORE_UNIT,
    TEST_CONTRACT_GATE,
    # Reviewer surfaces
    REVIEWER_CHALLENGE_CLEAN_SCAR,
    REVIEWER_FIX_THE_TEST,
    REVIEWER_REFERS_SILENT_ROT,
    REVIEWER_REVIEWS_TESTS,
    REVIEWER_STRUCTURAL_TEST_COUPLING,
    # Dispatch surface (per-block)
    DISPATCH_TEST_QUALITY_PROMPT,
    # Planning surfaces
    PLANNING_DECOMPOSITION_NAMES_CONTRACT,
    PLANNING_FORBID_GENERIC_UNIT_WORDING,
    PLANNING_UNIT_TEST_CONTRACT_SECTION,
)
from tests.test_contract_bound_tests._token_lib import (
    ROOT,
    missing_concepts,
)

# Single-source the directory this package lives in. Every coverage evaluator is a
# `test_*.py` file beside this module.
PKG_DIR = ROOT / "tests" / "test_contract_bound_tests"

# --- Surface anchors (single named files; NEVER a glob of changes/) ----------
REFERENCE = ROOT / "references" / "test-contract.md"
IMPLEMENTER = ROOT / "agents" / "implementer.md"
IMPLEMENT_SKILL = ROOT / "skills" / "implement" / "SKILL.md"
CODE_REVIEWER = ROOT / "agents" / "code-reviewer.md"
CODE_QUALITY_REVIEWER = ROOT / "agents" / "code-quality-reviewer.md"
DISPATCH_TEMPLATE = ROOT / "skills" / "implement" / "dispatch-template.md"
TASK_FORMAT = ROOT / "skills" / "planning" / "task-format.md"
PLANNING_SKILL = ROOT / "skills" / "planning" / "SKILL.md"

# The canonical set of surfaces the protocol is responsible for.
#
# CRITERION (marked bet) — what counts as a "required protocol surface": a single named
# instruction file that an agent or skill READS as authoritative behavior and that must
# carry contract-bound-unit-test concepts (an agent prompt, a skill instruction doc, a
# dispatch/task template). It is NOT a historical artifact (task files under changes/),
# NOT generated/dist output, and NOT a per-surface evaluator. The set lists single named
# files only and never globs changes/ — task-5 pins that non-enforcement.
#
# The manifest's surface set MUST equal this; a dropped surface (or a stale extra) is
# caught by the completeness death test. ADD a surface here ONLY together with a manifest
# row for it — that pairing is the guarantee a future surface cannot be carried in code
# while left unchecked.
CANONICAL_REQUIRED_SURFACES: frozenset = frozenset(
    {
        REFERENCE,
        IMPLEMENTER,
        IMPLEMENT_SKILL,
        CODE_REVIEWER,
        CODE_QUALITY_REVIEWER,
        DISPATCH_TEMPLATE,
        TASK_FORMAT,
        PLANNING_SKILL,
    }
)


# --- Coverage manifest -------------------------------------------------------
#
# Each row binds a surface to the concept groups it MUST carry, and a `per_block` flag.
# The concept groups are the SAME ones each focused evaluator (tasks 1-5) imports — the
# manifest re-asserts them centrally so a whole surface cannot silently lose the protocol
# (e.g. an evaluator file is deleted) without this consolidated guard reddening. The
# per-block dispatch row mirrors task-4: the gate must be asked of BOTH reviewer blocks,
# so it is checked inside each block, not over the whole document.


def _merge(*maps: dict) -> dict:
    merged: dict = {}
    for m in maps:
        merged.update(m)
    return merged


# (surface_path, merged_concept_groups, per_block) — per_block is the dispatch boundary
# heading prefixes when the surface must be checked per sub-block, else None.
COVERAGE_MANIFEST: list[tuple] = [
    (REFERENCE, REFERENCE_CONCEPTS, None),
    (IMPLEMENTER, _merge(CONTRACT_BOUND_UNIT, FIX_THE_TEST), None),
    (
        IMPLEMENT_SKILL,
        _merge(
            CONTRACT_PRINCIPLE_AND_POINTER,
            TEST_CONTRACT_GATE,
            GATE_BEFORE_UNIT,
            DEATH_TEST_FIRST,
            CONTRACT_REFERENCE_SUPPORT_FILE,
        ),
        None,
    ),
    (
        CODE_REVIEWER,
        _merge(
            REVIEWER_REVIEWS_TESTS,
            REVIEWER_FIX_THE_TEST,
            REVIEWER_CHALLENGE_CLEAN_SCAR,
        ),
        None,
    ),
    (
        CODE_QUALITY_REVIEWER,
        _merge(REVIEWER_STRUCTURAL_TEST_COUPLING, REVIEWER_REFERS_SILENT_ROT),
        None,
    ),
    # Dispatch: per-block. BOTH reviewer dispatch blocks must carry the test-quality
    # prompt — checked inside each block so a single prompt cannot satisfy both.
    (
        DISPATCH_TEMPLATE,
        DISPATCH_TEST_QUALITY_PROMPT,
        ("### yin reviewer", "### code quality reviewer"),
    ),
    (
        TASK_FORMAT,
        _merge(
            PLANNING_UNIT_TEST_CONTRACT_SECTION, PLANNING_FORBID_GENERIC_UNIT_WORDING
        ),
        None,
    ),
    (PLANNING_SKILL, PLANNING_DECOMPOSITION_NAMES_CONTRACT, None),
]


def manifest_surface_set(manifest: list[tuple]) -> frozenset:
    """The set of surface paths named by a manifest. Used by the completeness check to
    compare against CANONICAL_REQUIRED_SURFACES — a dropped row shrinks this set, a
    stale row grows it, and either inequality reddens the death test."""
    return frozenset(row[0] for row in manifest)


def _dispatch_block(text: str, heading: str) -> str | None:
    """Return the named '### ' dispatch sub-block (heading to next '### '/'## '), or
    None if absent. Mirrors task-4's per-block scoping so a single test-quality prompt
    in one block cannot satisfy the other."""
    lines = text.splitlines()
    start = next(
        (i for i, ln in enumerate(lines) if ln.strip().lower().startswith(heading)),
        None,
    )
    if start is None:
        return None
    end = next(
        (
            j
            for j in range(start + 1, len(lines))
            if lines[j].startswith("### ") or lines[j].startswith("## ")
        ),
        len(lines),
    )
    return "\n".join(lines[start:end])


# --- Self-refuting meta-test machinery ---------------------------------------
#
# The shared ENGINE module and the coverage helpers a routed evaluator must use. An
# evaluator that imports neither has gone private and can drift from the canonical
# matching engine — the disease the single shared engine exists to prevent.
#
# iteration-fix-1 split the engine (matching/parsing helpers) into `_token_lib` and kept
# the concept-catalog DATA in `_contract_tokens`. The routing guarantee is ABOUT routing
# coverage through the shared HELPERS, so the module name that must be imported is now
# the engine module `_token_lib` (where concept_present / missing_concepts /
# concepts_covered_by live). An evaluator that does its own raw `in` coverage without
# importing the engine has gone private — exactly what this scan still catches.
SHARED_TOKEN_MODULE = "_token_lib"
SHARED_COVERAGE_HELPERS: frozenset = frozenset(
    {"concept_present", "concepts_covered_by", "missing_concepts"}
)

# Section-LOCATOR constant naming convention. A `## heading` string assigned to a
# module-level NAME with this suffix (REVIEW_ORDER_HEADING, SUPPORT_FILES_HEADING,
# EXECUTION_ORDER_HEADING, YIN_BLOCK_HEADING, QUALITY_BLOCK_HEADING) is a SECTION ANCHOR
# used to LOCATE/slice a section. This suffix is a documentation convention surfaced in
# the death-test diagnostics; it is NOT consulted by the scan. Locators are exempt by
# construction (a named constant is an ast.Name reference, not a Compare operand), so the
# scan needs no allow-list — see heading_as_coverage_offenders.
HEADING_LOCATOR_CONSTANT_SUFFIX = "_HEADING"

# This module is itself an evaluator-package file but is NOT a per-surface coverage
# evaluator in the same shape (it imports many groups and defines the meta machinery);
# its OWN routing is proven by the unit test below, and the death-test sibling is a
# death-only module. The scan globs the per-surface evaluators by this pattern.
EVALUATOR_GLOB = "test_*_test_contract.py"


def evaluator_source_files() -> list:
    """The per-surface coverage evaluator source files (tasks 1-5's `*_test_contract.py`
    plus this module). The reference evaluator is named `test_test_contract_reference*.py`
    so it also matches; that is intended — it too must route through shared tokens."""
    files = sorted(PKG_DIR.glob(EVALUATOR_GLOB))
    # Include the reference evaluator (different name shape) and THIS module explicitly,
    # so the routing guarantee covers every evaluator that does concept coverage.
    extra = [
        PKG_DIR / "test_test_contract_reference.py",
        PKG_DIR / "test_coverage_manifest.py",
    ]
    seen = {f.name for f in files}
    for e in extra:
        if e.is_file() and e.name not in seen:
            files.append(e)
            seen.add(e.name)
    return files


def _source_routes_through_shared_tokens(source: str) -> bool:
    """True iff `source` BOTH imports from `_token_lib` (the shared engine module) AND
    references at least one shared coverage helper. AST-based (not substring grep) so a
    docstring that merely MENTIONS the module/helper cannot mask a privatized evaluator.

    ROUTING PROXY (marked bet + its limit): "references a helper" is approximated by
    `ast.Name` membership — the helper's bare name appearing anywhere in the tree. This
    is a PROXY for actual routing, not proof of a call. It does NOT detect aliasing
    (`from _token_lib import missing_concepts as mc`, where the used name is `mc`)
    nor dynamic dispatch (`getattr(mod, "missing_concepts")`). Accepted because the
    evaluators are hand-written in a fixed style; a future evaluator using either pattern
    would be a false-negative here, backstopped only by review.
    """
    tree = ast.parse(source)
    imports_shared = any(
        isinstance(n, ast.ImportFrom)
        and n.module is not None
        and SHARED_TOKEN_MODULE in n.module
        for n in ast.walk(tree)
    )
    names_used = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
    routes = bool(names_used & SHARED_COVERAGE_HELPERS)
    return imports_shared and routes


def routing_offenders(sources: dict[str, str] | None = None) -> list[str]:
    """Return the names of coverage evaluators that do NOT import `_token_lib`
    or do NOT reference any shared coverage helper.

    By default scans the real evaluator source files. Pass `sources` (a {label: source}
    mapping) to scan provided source text instead — used by the death test to feed a
    synthetic privatized evaluator through the SAME authoritative routing algorithm
    rather than re-deriving it.
    """
    if sources is None:
        sources = {
            path.name: path.read_text(encoding="utf-8")
            for path in evaluator_source_files()
        }
    return [
        label
        for label, source in sources.items()
        if not _source_routes_through_shared_tokens(source)
    ]


def _scan_heading_as_coverage(source: str, label: str) -> list[str]:
    """AST-scan one evaluator source for a `## heading` STRING LITERAL used AS a concept-
    COVERAGE assertion, distinguished from a legitimate section LOCATOR.

    DISTINCTION (the subtle nuance the task calls out):
      * ALLOWED — a `## heading` literal assigned to a module-level constant named
        `*_HEADING` and used to LOCATE/slice a section (passed to startswith / a section
        extractor). The constant NAME is the signal of intent.
      * ALLOWED — a MULTI-LINE synthetic fixture string (contains a newline). Several
        death tests build hostile fixtures like `"## Unit Test Contract\\n..."` and feed
        them to `concepts_covered_by` to PROVE polarity. These are inputs to the shared
        helpers, not coverage-by-heading on a real surface, and they are never a bare
        comparison operand.
      * BUG — a single-line `## heading` literal that is a DIRECT operand of a comparison
        (`in` / `==` / `!=`): e.g. `assert "## Review Order" in text`. That asserts the
        exact heading IS the coverage — over-fit by construction.

    Returns a list of human-readable offender descriptions (empty == clean). The
    distinction is conservative: only a heading literal sitting directly in a Compare is
    flagged, so a locator constant (a plain Assign / Name) and a multi-line fixture
    (passed as a Call arg) are never false-flagged.
    """
    tree = ast.parse(source)
    offenders: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Compare):
            continue
        operands = [node.left, *node.comparators]
        for operand in operands:
            if isinstance(operand, ast.Constant) and isinstance(operand.value, str):
                literal = operand.value
                # Single-line heading literal only. Multi-line synthetic fixtures
                # (with embedded newlines) are exempt — they are helper inputs, and they
                # never appear directly inside a Compare in this codebase anyway.
                if "\n" in literal:
                    continue
                if literal.lstrip().startswith("##"):
                    line = getattr(operand, "lineno", "?")
                    offenders.append(
                        f"{label}:{line}: '{literal}' used as a coverage comparison "
                        f"operand (heading-as-coverage over-fit)"
                    )
    return offenders


def heading_as_coverage_offenders() -> list[str]:
    """Scan every coverage evaluator for heading-as-coverage over-fit.

    Section-LOCATOR constants (e.g. REVIEW_ORDER_HEADING) are exempt BY CONSTRUCTION,
    not by an allow-list: a locator is used via its named constant, so it appears in the
    AST as an `ast.Name` reference (e.g. inside a `startswith(REVIEW_ORDER_HEADING)`
    call), never as an `ast.Constant` operand of a Compare. The scan flags ONLY a
    single-line `## heading` string literal that is a direct operand of an `ast.Compare`,
    so a locator constant can never be flagged — there is no list to maintain. Only an
    inline `## heading` literal used directly as a Compare operand (the over-fit this
    feature kills) is reported.
    """
    offenders: list[str] = []
    for path in evaluator_source_files():
        source = path.read_text(encoding="utf-8")
        offenders.extend(_scan_heading_as_coverage(source, path.name))
    return offenders


# --- Unit tests --------------------------------------------------------------


class TestCoverageManifestCompleteness:
    def test_manifest_surface_set_equals_canonical(self):
        assert manifest_surface_set(COVERAGE_MANIFEST) == CANONICAL_REQUIRED_SURFACES, (
            "the coverage manifest must name exactly the canonical required surfaces"
        )

    def test_manifest_rows_are_well_formed(self):
        for surface, groups, per_block in COVERAGE_MANIFEST:
            assert surface.is_file(), f"manifest surface {surface} is not a file"
            assert groups, f"manifest row for {surface.name} has no concept groups"
            for key, tokens in groups.items():
                assert isinstance(tokens, tuple) and tokens, (
                    f"{surface.name}: concept '{key}' has no tokens"
                )


class TestEverySurfaceCarriesItsProtocol:
    """The consolidating guard: every required surface still carries its protocol
    concepts, checked via the SHARED tokens. A whole surface losing the protocol (e.g.
    an evaluator file deleted) reddens HERE even though the deleted evaluator's own tests
    no longer run."""

    def test_every_non_block_surface_covers_its_concepts(self):
        for surface, groups, per_block in COVERAGE_MANIFEST:
            if per_block is not None:
                continue
            text = surface.read_text(encoding="utf-8")
            missing = missing_concepts(text, groups)
            assert not missing, (
                f"{surface.name} no longer carries its protocol concepts "
                f"(checked via shared tokens, not headings): {missing}"
            )

    def test_dispatch_template_carries_prompt_in_every_block(self):
        for surface, groups, per_block in COVERAGE_MANIFEST:
            if per_block is None:
                continue
            text = surface.read_text(encoding="utf-8")
            for heading in per_block:
                block = _dispatch_block(text, heading)
                assert block is not None, (
                    f"{surface.name}: dispatch block '{heading}' not found (renamed?)"
                )
                missing = missing_concepts(block, groups)
                assert not missing, (
                    f"{surface.name}: dispatch block '{heading}' is missing the "
                    f"test-quality prompt concepts: {missing}"
                )


class TestSelfRefutingMetaGuardsAreLive:
    """The meta-test machinery must itself be exercised, not merely defined."""

    def test_all_evaluators_route_through_shared_tokens(self):
        assert not routing_offenders(), (
            "every coverage evaluator must import _token_lib and route coverage "
            "through the shared helpers"
        )

    def test_no_evaluator_asserts_coverage_via_pinned_heading(self):
        assert not heading_as_coverage_offenders(), (
            "no evaluator may assert concept coverage via a pinned '## heading' literal"
        )

    def test_evaluator_glob_finds_the_focused_evaluators(self):
        # Sanity: the scan must actually find the per-surface evaluators, or the routing
        # / heading guards would be vacuously green over an empty file set.
        names = {p.name for p in evaluator_source_files()}
        for expected in (
            "test_implementer_test_contract.py",
            "test_implement_skill_test_contract.py",
            "test_reviewer_test_contract.py",
            "test_planning_test_contract.py",
            "test_test_contract_reference.py",
            "test_coverage_manifest.py",
        ):
            assert expected in names, (
                f"coverage evaluator {expected} not found by the scan; the routing and "
                f"heading guards would skip it. Found: {sorted(names)}"
            )
