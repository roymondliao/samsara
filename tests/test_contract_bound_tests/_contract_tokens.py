"""Canonical concept-group DATA for contract-bound-unit-tests.

DEATH-REASON OF THIS MODULE: "what concepts each instruction surface must carry."
Every value below is an *intent-bearing* token: a substring or regex that any honest
rewrite of the target surface must still contain because it carries the *concept*, not
the *wording*. None of these tokens is an exact heading string, a whole sentence, or
prose that a faithful rename/reword would delete. If a token here would false-fail when
a heading is renamed but the concept is preserved, that token is itself over-fit and
refutes this feature's thesis — fix the token, do not weaken the doc.

This module is DATA-ONLY. The token-matching + step-parsing ENGINE (rx, token_present,
concept_present, missing_concepts, concepts_covered_by, pinned_heading_offenders,
numbered_steps, step_index_of_concept, the Token alias, ROOT) lives in the sibling
`_token_lib.py`; iteration-fix-1 split the two death-reasons apart so a change to HOW a
concept is matched and a change to WHAT a surface must carry no longer touch one file.
This module imports `rx` and `Token` from `_token_lib` to construct its groups — a
one-directional dependency (data depends on engine, never the reverse). Downstream
evaluators import the ENGINE helpers from `_token_lib` and the GROUPS from here.
`test_module_split_death.py` reddens if an engine helper leaks back into THIS module:
do NOT add functions here.

Tasks 2-6 import SUBSETS of these groups to check their own instruction surfaces
(implementer.md, SKILL.md, reviewers, task-format.md, dispatch-template.md). The
group/key names are the stable public contract of this module: renaming a key breaks
every downstream evaluator, so keys are named after the *concept*, never after a
heading in any single document.

Matching contract (defined and documented in `_token_lib.py`):
    A "token" is matched against a target text with `token_present(text, token)`:
    plain tokens are case-insensitive substring matches; tokens wrapped via `rx(...)`
    are case-insensitive regex searches. A concept is "covered" when AT LEAST ONE token
    in its tuple is present, so tuples enumerate *alternative honest phrasings* of the
    same concept, not a conjunction of required strings.
"""

from __future__ import annotations

from tests.test_contract_bound_tests._token_lib import Token, rx

# Single-source the reference filename literal so a rename of
# references/test-contract.md is a one-line change here, not a scatter-edit across
# CONTRACT_BOUND_UNIT / TEST_CONTRACT_GATE / CONTRACT_REFERENCE_SUPPORT_FILE.
REFERENCE_PATH_RX = r"test-contract\.md"


# --- Concept groups ---------------------------------------------------------
#
# Each group is a dict {concept_key: (alternative honest tokens, ...)}.
# Downstream tasks import the groups (or merge them) they need.


# The Contract Gate: the two questions that decide if a test asserts a real
# contract. BOTH poles of the gate must be expressible — a behavior-preserving
# refactor must NOT break the test, and a real behavior break MUST break it.
CONTRACT_GATE = {
    "behavior_preserving_refactor": (
        "behavior-preserving refactor",
        "behaviour-preserving refactor",
        rx(
            r"refactor.{0,40}(without|with no|that does not).{0,20}chang\w*\s+behaviou?r"
        ),
        rx(r"behaviou?r[- ]preserving"),
    ),
    "behavior_actually_broke": (
        "behavior actually broke",
        "behaviour actually broke",
        rx(r"behaviou?r.{0,20}(actually )?(broke|breaks|broken|changed)"),
        rx(r"(real|actual).{0,20}behaviou?r.{0,20}(break|broke|change)"),
    ),
}

# Brittleness Filter: the over-fit pole. A test that fails when nothing the user
# cares about changed.
BRITTLENESS_FILTER = {
    "overfit_pole": (
        "over-fit",
        "overfit",
        "brittle",
    ),
    "implementation_detail": (
        "implementation detail",
        "implementation details",
    ),
}

# Silent-Green Guard: the tautology pole. A test that can never go red.
SILENT_GREEN_GUARD = {
    "tautology_pole": (
        "silent-green",
        "silent green",
        "tautolog",  # tautology / tautological
        rx(r"(can|could)\s+never\s+(go|turn)\s+red"),
        rx(r"never\s+fail"),
    ),
    "vague_assertion": (
        # Intent-bearing: the doc must name the vague/tautological assertion
        # concept, not merely happen to list "not null"/"is not none" as example
        # phrases. Keying on the example phrases was fragile: an honest rewrite
        # that changed the examples would false-negative even though the concept
        # was preserved.
        rx(r"vague\s+(unit\s+)?test"),
        rx(r"assert\w*\s+(almost\s+)?nothing"),
        rx(r"stays?\s+green"),
        rx(r"truthy"),
        rx(r"(>=|greater\s+than\s+or\s+equal).{0,6}0"),
    ),
}

# The fix for BOTH poles is the same shape: assert the contract precisely and
# assert nothing else. Not "assert less".
BOTH_POLES_FIX = {
    "assert_contract_precisely": (
        rx(r"assert\s+the\s+contract\s+precisely"),
        rx(r"assert\w*\s+the\s+contract.{0,30}and\s+(assert\s+)?nothing\s+else"),
        rx(r"precise\w*\s+contract"),
    ),
    "not_assert_less": (
        # Directional ONLY: the doc must REJECT "assert less", not merely mention
        # it. A bare "assert less" substring would pass on a doc that ENDORSES the
        # practice — green-by-construction — so it is forbidden here.
        rx(r"not\s+[\"']?assert\s+less"),
        rx(r"isn'?t\s+[\"']?assert\s+less"),
        rx(r"is\s+not\s+[\"']?assert\s+less"),
    ),
}

# Snapshot and Golden tests: permitted, but volatile fields must be normalized
# first. The doc must NOT ban snapshots outright.
SNAPSHOT_GOLDEN = {
    "normalize_before_snapshot": (
        rx(r"normaliz\w*.{0,40}(before|prior to|then)\s+snapshot"),
        "normalize-then-snapshot",
        "normalise-then-snapshot",
        rx(r"normaliz\w*\s+volatile"),
    ),
    "volatile_fields": (
        # The literal concept name is honest and specific.
        "volatile field",
        # A specific volatile field enumerated AS something to normalize / replace
        # with a placeholder. The volatile-word list is bound to a normalization
        # verb in proximity so this cannot match a doc that merely says "path" or
        # "version" in passing — that bare match was green-by-construction.
        rx(
            r"(normaliz|replac|placeholder|stable\s+placeholder)\w*[^.]{0,80}"
            r"(path|port|version|date|timestamp|random[- ]?id)"
        ),
        rx(
            r"(path|port|version|date|timestamp|random[- ]?id)[^.]{0,80}"
            r"(normaliz|replac|placeholder)\w*"
        ),
    ),
}

# Boundary Spy Exception: spies/mocks are allowed when the interaction at a
# boundary IS the observable feature.
BOUNDARY_SPY = {
    "interaction_is_the_feature": (
        rx(r"interaction\s+(itself\s+)?is\s+the\s+(observable\s+)?feature"),
        rx(r"boundary[- ]spy"),
        rx(r"spy.{0,40}(when|where).{0,20}interaction"),
    ),
    # NOTE: a bare ("spy", "spies", "mock") concept was removed here. It matched
    # any document mentioning the topic and could never go red — green-by-
    # construction, and redundant with `interaction_is_the_feature`, which proves
    # the actual protocol behavior (a spy is permitted only when the interaction
    # at a boundary IS the observable feature).
}

# Minimum-Contract Workflow Assertions: multi-path workflows assert a minimum
# legal contract (e.g. ">= 2 snapshots", "at least one click"), never a single
# hard-coded path.
MINIMUM_CONTRACT = {
    "minimum_contract": (
        "minimum-contract",
        "minimum contract",
        rx(r"at\s+least\s+(one|two|\d)"),
        rx(r">=\s*\d"),
    ),
    "no_single_hardcoded_path": (
        rx(r"(no|not|never)\s+(a\s+)?single\s+(hard[- ]?coded\s+)?path"),
        rx(r"multiple\s+(legal|valid)\s+paths?"),
        "multi-path",
        rx(r"hard[- ]?cod\w*\s+path"),
    ),
}

# Unit Tests vs Death Tests: the anti-overfit rule applies to UNIT tests. A
# death test MAY pin the exact failure mode because that failure mode IS its
# contract.
UNIT_VS_DEATH = {
    "death_pins_failure_mode": (
        rx(
            r"death\s+test\w*\s+(may|can|must|should).{0,40}(pin|assert|name).{0,40}(exact\s+)?(silent[- ])?failure"
        ),
        rx(r"failure\s+mode\s+is\s+(its|the)\s+contract"),
        rx(r"pin\w*\s+the\s+(exact\s+)?(silent[- ])?failure\s+mode"),
    ),
    "anti_overfit_is_unit_only": (
        rx(r"(anti[- ]?over[- ]?fit|brittl\w*).{0,60}(appl\w+|only).{0,30}unit\s+test"),
        rx(r"unit\s+test\w*,?\s+not\s+death\s+test"),
        rx(r"death\s+test\w*\s+are\s+(an\s+)?except"),
    ),
}

# Contract-Bound Unit Test Gate (implementer-surface concept). The implementer
# instruction must require that a UNIT test asserts a *named contract source*, not
# merely "write unit tests". The over-fit pole of THIS token would be keying on
# the bare word "contract" (which appears in scar-report prose all over the agent
# file) — so each token binds "contract" to the act of *asserting/binding a test
# to* one, or names a specific contract source from the canonical list.
CONTRACT_BOUND_UNIT = {
    "contract_bound_requirement": (
        rx(r"contract[- ]bound\s+unit\s+test"),
        rx(r"unit\s+test\w*\s+(must|should)\s+assert\w*\s+(a\s+|the\s+)?contract"),
        rx(
            r"assert\w*\s+(a\s+|the\s+)?(behavio?ural\s+)?contract,?\s+not\s+implementation"
        ),
    ),
    "names_a_contract_source": (
        # PRESENCE-NOT-BINDING guard. Bare source words (observable behaviour,
        # public api or schema, documented artifact shape) fire on a doc that
        # merely MENTIONS them without binding a unit test to them — e.g. "we
        # reference test-contract.md; observable behaviour is described elsewhere".
        # So each token requires the source to be BOUND to the act of asserting (a
        # unit test must assert <source>), or names the canonical reference PATH
        # (which legitimately points at WHERE the source list lives, not a passing
        # mention of a source word). A mention-only string is reported MISSING; see
        # test_mention_only_sources_are_missing_contract_source.
        rx(REFERENCE_PATH_RX),
        rx(
            r"unit\s+test\w*\s+must\s+assert.{0,80}"
            r"(observable\s+behavio?ur|public\s+api|artifact|schema)"
        ),
        rx(
            r"assert\w*\s+(a\s+)?named\s+contract\s+source.{0,80}"
            r"(observable\s+behavio?ur|public\s+api|artifact|schema)"
        ),
    ),
}

# Fix-the-Test caveat (implementer-surface concept). When a test fails because it
# is bound to the WRONG contract (an implementation detail), the correct action is
# to FIX THE TEST, not bend the implementation to a rotten test.
#
# DIRECTIONAL ONLY (presence-not-polarity guard). The dangerous tokenization here
# is a bare `rx(r"fix\s+the\s+test")`: in an OR tuple that is a silent-green
# backdoor — a doc that says "when a test fails, ALWAYS fix the test to make it
# pass" (endorsing the WRONG practice) would match identically to one that says
# "fix the test, NOT the implementation". So every token below carries the
# DIRECTION (test-not-implementation, or the wrong/rotten-contract trigger). A doc
# that merely says "fix the test" with no direction must be reported MISSING this
# concept. The polarity death test
# (test_endorsing_wrong_practice_is_missing_fix_concept) proves direction is
# required, not just word presence.
FIX_THE_TEST = {
    "fix_rotten_test_not_impl": (
        rx(r"fix\s+the\s+test,?\s+not\s+the\s+implementation"),
        rx(r"(wrong|rotten|incorrect)\s+contract.{0,60}fix"),
        rx(
            r"not\s+(every|all)\s+(failing\s+)?test\w*\s+mean\w*\s+(the\s+)?implementation"
        ),
        rx(r"do\s+not\s+bend\s+the\s+implementation"),
    ),
}

# Test Contract Gate (SKILL/orchestration-surface concept). The implement
# orchestration skill must name a *gate* — a mandatory checkpoint — that runs the
# contract check, and it must POINT to the canonical reference rather than re-paste
# its catalog. The over-fit pole of THIS token would be keying on the bare word
# "gate" (the skill mentions an "Execution strategy gate", a "Completion gate", an
# "Auto Mode Gate" — all unrelated) OR on a bare "contract gate" that any prose can
# carry ("deployment contract gate", "data contract gate"). So each token binds the
# gate to the *test* contract concept: the literal "test contract gate", or a
# "contract gate" tied to running BEFORE unit tests, or the canonical reference PATH
# (which legitimately points at WHERE the protocol lives). An unrelated "contract
# gate" mention (e.g. "deployment contract gate") is reported MISSING; see
# test_unrelated_contract_gate_prose_is_missing_contract_gate.
TEST_CONTRACT_GATE = {
    "contract_gate_named": (
        rx(r"test[- ]contract\s+gate"),
        rx(r"contract\s+gate[^.]{0,80}before[^.]{0,40}unit\s+test"),
        rx(r"before[^.]{0,40}unit\s+test[^.]{0,80}contract\s+gate"),
        rx(REFERENCE_PATH_RX),
    ),
}

# Contract-bound PRINCIPLE + reference POINTER (SKILL-surface). The lean skill must
# carry the PRINCIPLE ("a unit test asserts a behavioral contract, not implementation
# details") and a POINTER to the canonical reference — it must NOT re-enumerate the
# contract-source catalog (that enumeration is implementer-surface, task-2's concern,
# and a duplicated catalog drifts). So this group requires only the principle and the
# pointer; it deliberately does NOT require the full source list. The evaluator still
# reddens if the skill drops the principle (no behavioral-contract-not-impl statement)
# or the pointer (no test-contract.md reference).
CONTRACT_PRINCIPLE_AND_POINTER = {
    "contract_not_implementation_detail": (
        # behaviou?ral matches both "behavioral" (US) and "behavioural" (UK).
        rx(
            r"assert\w*\s+(a\s+|the\s+)?(behaviou?ral\s+)?contract,?\s+not\s+implementation"
        ),
        rx(r"contract[- ]bound\s+unit\s+test"),
        rx(
            r"unit\s+test\w*\s+(must|should)\s+assert\w*\s+(a\s+|the\s+)?(behaviou?ral\s+)?contract"
        ),
    ),
    "points_to_reference": (rx(REFERENCE_PATH_RX),),
}

# Gate-before-unit-test ordering (SKILL-surface). The gate is worthless if it can
# be placed AFTER unit tests are written — by then the tautological test is already
# on disk. The skill must state the gate runs BEFORE unit tests. Directional: a
# bare "before"/"unit test" co-mention is too weak; the token binds the contract/
# gate to running PRIOR TO writing unit tests.
GATE_BEFORE_UNIT = {
    "gate_precedes_unit_tests": (
        rx(
            r"(contract\s+gate|test[- ]contract|contract\s+check)[^.]{0,80}before[^.]{0,40}unit\s+test"
        ),
        rx(
            r"before[^.]{0,40}(writ\w*\s+)?unit\s+test\w*[^.]{0,80}(contract\s+gate|test[- ]contract|contract\s+check)"
        ),
        rx(r"gate[^.]{0,40}before[^.]{0,40}unit\s+test"),
    ),
}

# Death-test-first ordering preserved (SKILL-surface). Adding a Test Contract Gate
# must NOT displace the load-bearing "death test before unit test" rule. The skill
# must still state that death tests come first / cannot be swapped. Directional: a
# bare "death test"/"unit test" co-mention is too weak; the token binds the two in
# the ORDER death-before-unit, or names the non-swappable ordering rule.
DEATH_TEST_FIRST = {
    "death_before_unit_preserved": (
        rx(
            r"death\s+test\w*\s+(must\s+be\s+\w+\s+(and\s+\w+\s+)?)?before\s+unit\s+test"
        ),
        rx(r"death\s+test\s+first"),
        rx(r"(order|ordering)\s+(cannot|can\s+not|must\s+not)\s+be\s+swapped"),
    ),
}

# Contract-reference support file (SKILL-surface). The orchestration skill's
# Support Files list must register references/test-contract.md so an implementer
# dispatched by this skill can find the protocol. The literal PATH IS the contract
# here (the exact path is what must be present), so a literal path token is the
# honest assertion — there is no "concept wording" to preserve, only the path.
CONTRACT_REFERENCE_SUPPORT_FILE = {
    "reference_path_present": (rx(REFERENCE_PATH_RX),),
}


# Step-identity tokens for STRUCTURAL ordering. These match the BODY of a numbered
# execution-order step by its concept, not by an exact label string, so the parser
# survives a rewrap/reword that preserves the step's meaning. They are deliberately
# narrow: each identifies ONE step in the death→gate→unit sequence. Used only by the
# structural ordering check (step_index_of_concept), never for presence coverage.
STEP_DEATH_TEST = (rx(r"death\s+tests?"),)
STEP_CONTRACT_GATE = (rx(r"contract\s+gate"),)
STEP_UNIT_TEST = (
    # "Write unit tests" — the step that AUTHORS unit tests. Anchored to the START of
    # the step body ("Write unit tests ...") so it does not also match the gate step,
    # whose body says "... do not skip to writing unit tests" mid-sentence. Matching
    # the gate body would collapse gate_index == unit_index and silently defeat the
    # ordering check. We accept a markdown bold marker ("**Write") at the anchor.
    rx(r"^\**writ\w*\s+unit\s+tests?"),
)


# Planning task-format surface (task-5). The TEMPLATE skills/planning/task-format.md
# must REQUIRE a Unit Test Contract section so each generated task names its contract
# UPSTREAM, and the implementer references it instead of inferring a contract from the
# current implementation.
#
# `unit_test_contract_section_required`: the template registers a "Unit Test Contract"
# section as REQUIRED — not merely present.
#
# DIRECTIONAL (presence-not-requirement guard). A bare `rx(r"unit[- ]test\s+contract")`
# proves only PRESENCE: it fires on a template that says "Unit Test Contract section:
# optional", contradicting the key's claim of REQUIRED. So every token below binds the
# section NAME to an imperative ("must"): the template body's "a unit test MUST assert
# this named contract source" and Rule #4's "the Unit Test Contract section MUST name an
# observable contract source" both carry it. To avoid a bare-heading pin (the over-fit
# this feature kills, see pinned_heading_offenders) the tokens do NOT carry the markdown
# "##" prefix — they match the section NAME bound to a "must" wherever it appears, so an
# honest reflow that keeps the requirement survives. An "optional" template, or a
# template that merely MENTIONS the section without requiring it, is reported MISSING;
# the negative death test (test_optional_section_template_is_missing_required_concept)
# proves requiredness is load-bearing, not mere phrase presence.
#
# BOUNDARY CLASS (yin Important fix): the gap between the section name and `must` is
# `[^.?!>\n]`, NOT `[^.]`. A bare `[^.]` only stops at a literal period, so the BACKWARD
# token would let a `must` from the standard Death Test Requirements comment
# ("<!-- What death tests must be written BEFORE implementation? -->") bind to the
# "## Unit Test Contract" heading ~109 chars later — the two are separated only by `?`,
# `-->`, newlines and dashes, none of which is a `.`. That bleed made a FULL-FORM
# template that keeps the standard DTR block but marks the UTC section OPTIONAL
# false-pass (the exact silent-green disease this feature kills). Stopping the class at
# `?`, `!`, `>` and especially the NEWLINE forces `must` and the section name to belong
# to the SAME clause/line — Rule #4's same-line "Unit Test Contract section must name an
# observable contract source" still matches, but the cross-block DTR bleed cannot. The
# polarity death test test_optional_section_template_is_missing_required_concept uses a
# full-form-optional fixture (DTR block present + UTC optional) to pin this: it
# false-passes on `[^.]` and reports MISSING on `[^.?!>\n]`.
PLANNING_UNIT_TEST_CONTRACT_SECTION = {
    "unit_test_contract_section_required": (
        rx(r"unit[- ]test\s+contract[^.?!>\n]{0,120}\bmust\b"),
        rx(r"\bmust\b[^.?!>\n]{0,120}unit[- ]test\s+contract"),
    ),
}

# `forbids_generic_unit_test_wording`: DIRECTIONAL/POLARITY guard. The template must
# REJECT generic "appropriate tests" / "appropriate unit tests" wording in the Unit
# Test Contract section and require an OBSERVABLE contract source instead. A bare
# "appropriate tests" substring is a silent-green backdoor: it matches a template that
# ENDORSES the generic wording ("write appropriate tests") identically to one that
# FORBIDS it ("not 'appropriate tests' — name an observable contract source"). So
# every token below carries the DIRECTION: the generic wording is forbidden, OR an
# observable/named contract source is REQUIRED. A template that merely says "write
# appropriate tests" with no forbid-rule must be reported MISSING this concept. The
# polarity death test (test_endorsing_generic_wording_is_missing_forbid_rule) proves
# the direction is load-bearing, not mere word presence.
PLANNING_FORBID_GENERIC_UNIT_WORDING = {
    "forbids_generic_unit_test_wording": (
        rx(r"not\s+[\"']?appropriate\s+(unit\s+)?tests?"),
        rx(r"no\s+[\"']?appropriate\s+(unit\s+)?tests?"),
        rx(r"(name|names?|naming)\s+(an?\s+)?observable\s+contract\s+sources?"),
        rx(r"observable\s+contract\s+sources?,?\s+not\s+[\"']?appropriate"),
        rx(r"unit[- ]test\s+contract[^.]{0,80}observable\s+contract\s+source"),
    ),
}

# `decomposition_names_unit_test_contract_source` (SKILL-surface). The planning
# decomposition step must tell the planner that each task names its unit-test contract
# source ALONGSIDE the death test requirements — so the contract is named upstream, at
# planning time.
#
# DIRECTIONAL ONLY (presence-not-polarity guard). The dangerous tokenization here is a
# bare `rx(r"unit[- ]test\s+contract(\s+source)?")`: in an OR tuple that is a
# presence-not-polarity backdoor — it matches ANY mention of the compound phrase,
# INCLUDING a sentence that DROPS the obligation while naming it ("the unit-test
# contract source is NOT required at planning time" / "left to the implementer's
# discretion"). A SKILL.md that removes the decomposition obligation but still mentions
# the phrase would pass. So the bare token is removed; every token below binds the
# decomposition ACT to naming a unit-test contract (source) the way the step already
# names death test requirements, or states the contract is named UPSTREAM. A doc that
# merely mentions the phrase (or negates the obligation) must be reported MISSING; the
# polarity death test (test_negating_decomposition_obligation_is_missing_concept)
# proves direction is required, not mere phrase presence.
PLANNING_DECOMPOSITION_NAMES_CONTRACT = {
    "decomposition_names_unit_test_contract_source": (
        # The task NAMES its/the/each-task's unit-test contract source — a declarative
        # obligation, NOT a conditional "whether to name ... is left to discretion".
        # Binding the naming verb to a determiner (its/the/each task's) before the
        # phrase rejects the negating decoy "Whether to name a unit-test contract
        # source is optional", which lacks that declarative determiner.
        rx(
            r"names?\s+(its|the|each\s+task.{0,3}s?)\s+unit[- ]test\s+contract\s+source"
        ),
        rx(r"contract\s+(is\s+)?named\s+(upstream|at\s+planning)"),
    ),
}


# --- Reviewer + dispatch surface (task-4) -----------------------------------
#
# Task-4 closes the loop: the gate documented in the reference/implementer/skill
# surfaces is WORTHLESS unless a reviewer actually ASKS for test-quality review at
# dispatch time (death case DC4). These groups are imported ONLY by the reviewer
# evaluator (test_reviewer_test_contract.py); they are NOT merged into
# REFERENCE_CONCEPTS (the canonical reference describes the protocol; it is not the
# reviewer agent and is not required to carry reviewer-facing imperatives).

# Yin code reviewer: reviews TESTS as a first-class subject (their brittleness /
# tautology), separate from reviewing implementation correctness.
#
# OVER-FIT POLE of THIS token: keying on the bare word "test" (the agent says
# "test coverage", "death case test", "tests" everywhere). So every token binds the
# act of REVIEWING/INSPECTING to TESTS as the subject, or names the two failure
# poles (brittle / tautological) as review targets. A doc that merely mentions
# "tests" in passing must be reported MISSING; the decoy death test pins this.
REVIEWER_REVIEWS_TESTS = {
    "reviews_test_quality": (
        rx(
            r"review\w*[^.?!\n]{0,60}test\w*[^.?!\n]{0,40}(brittle|over[- ]?fit|tautolog|silent[- ]green)"
        ),
        rx(
            r"(brittle|over[- ]?fit|tautolog|silent[- ]green)[^.?!\n]{0,60}test\w*[^.?!\n]{0,40}review"
        ),
        rx(r"(inspect|review|examine)\w*\s+the\s+test\w*\s+(quality|contract)"),
        rx(r"test[- ]quality\s+review"),
    ),
}

# Yin code reviewer: the directional "fix the test, not the implementation" verdict
# power — the reviewer can say a FAILING test means the TEST is bound to the wrong
# contract and must be fixed, NOT that the implementation must bend to a rotten test.
#
# DIRECTIONAL ONLY (presence-not-polarity guard). A bare `rx(r"fix\s+the\s+test")`
# is a silent-green backdoor: a doc that says "always fix the test to make it pass"
# (endorsing the WRONG practice) would match identically to "fix the test, not the
# implementation". So every token carries the DIRECTION (test-not-implementation, or
# the wrong/rotten-contract trigger). A bare "fix the test" with no direction is
# reported MISSING; the polarity death test proves direction is load-bearing.
REVIEWER_FIX_THE_TEST = {
    "fix_test_not_implementation": (
        rx(r"fix\s+the\s+test,?\s+not\s+the\s+implementation"),
        rx(r"(wrong|rotten|incorrect)\s+contract[^.?!\n]{0,80}fix\s+the\s+test"),
        rx(
            r"do\s+not\s+(bend|change|modify)\s+the\s+implementation\s+to[^.?!\n]{0,60}test"
        ),
    ),
}

# Yin code reviewer: the Clean Scar challenge — the reviewer must REJECT a
# perfunctory/tautological contract LABEL (a slogan like "# contract: it works"
# that maps to no observable behavior, API/schema, artifact, or death/bug case).
#
# OVER-FIT POLE of THIS token: keying on the bare word "contract" (scar-report prose
# all over the agent files mentions "contract"). DIRECTIONAL: the token must require
# the reviewer to CHALLENGE/REJECT a perfunctory label, not merely mention "contract".
# A doc that mentions "contract" without the reject-perfunctory direction is reported
# MISSING; the polarity death test proves direction is load-bearing.
REVIEWER_CHALLENGE_CLEAN_SCAR = {
    "rejects_perfunctory_contract_label": (
        rx(
            r"(perfunctory|tautolog\w*|slogan|empty|hollow|vacuous|clean[- ]scar)[^.?!\n]{0,80}contract"
        ),
        rx(
            r"contract[^.?!\n]{0,80}(perfunctory|tautolog\w*|slogan|empty|hollow|vacuous|clean[- ]scar)"
        ),
        rx(
            r"(challenge|reject|flag|fail)\w*[^.?!\n]{0,60}contract[^.?!\n]{0,80}(no|maps?\s+to\s+no|without)[^.?!\n]{0,40}(observable|behavio?ur|api|schema|artifact|death|bug)"
        ),
        rx(
            r"contract\s+(declaration|label)[^.?!\n]{0,80}(maps?\s+to\s+no|no\s+observable|does\s+not\s+map)"
        ),
    ),
}

# Structural code-quality reviewer: must own STRUCTURAL test coupling — tests coupled
# to implementation STRUCTURE (private internals, call sequence, member layout) — as
# distinct from silent-rot/correctness (which it REFERS to the yin reviewer).
#
# OVER-FIT POLE: keying on bare "coupling" (the agent has a whole Coupling principle
# about code, not tests). So the token binds coupling/structure to TESTS as the
# subject. A doc that discusses code coupling without the TEST-coupling subject is
# reported MISSING; the decoy death test pins this.
REVIEWER_STRUCTURAL_TEST_COUPLING = {
    "reviews_structural_test_coupling": (
        rx(
            r"test\w*[^.?!\n]{0,60}coupl\w*[^.?!\n]{0,60}(implementation\s+structure|internal|private|call\s+sequence|structure)"
        ),
        rx(
            r"(implementation\s+structure|internal|private|call\s+sequence)[^.?!\n]{0,60}coupl\w*[^.?!\n]{0,40}test"
        ),
        rx(r"structural\s+test\s+coupling"),
        rx(r"test\w*\s+coupled\s+to[^.?!\n]{0,60}(implementation|structure|internal)"),
    ),
}

# Structural code-quality reviewer: must REFER silent-rot / correctness test concerns
# to the yin code reviewer (the role split — it does not score them itself).
#
# PRESENCE-NOT-POLARITY guard (yin Important fix). The dangerous tokenization here was
# a bare `rx(r"refer[^.?!\n]{0,60}(samsara:)?code[- ]reviewer")`: it fires on ANY
# referral to the yin reviewer, INCLUDING the generic hand-off line already in this
# agent's Scope-Boundary preamble ("If you encounter any of these issues ... → Refer
# to samsara:code-reviewer"). With that bare token in the OR-tuple, a future author
# could DELETE the specific "refer test silent-rot / correctness to the yin reviewer"
# sentence and the concept would stay falsely COVERED via the generic line — the
# concept this group exists to enforce (the test-subject role split) would silently rot
# while the check stays green. So the bare referral token is REMOVED. Every token below
# binds the referral ACT to the silent-rot / correctness / wrong-contract / tautological
# / test SUBJECT: the referral must be ABOUT test silent-rot, not a generic hand-off.
# The gap classes allow newlines (`[\s\S]`) because the real binding wraps across lines
# in code-quality-reviewer.md ("...**silent-rot/correctness** concerns. Refer\nthem to
# the yin reviewer..."). A generic-only hand-off (no silent-rot/test subject) is reported
# MISSING; the polarity death test
# (test_generic_handoff_without_subject_is_missing_referral_concept) proves direction is
# load-bearing, not mere referral presence.
REVIEWER_REFERS_SILENT_ROT = {
    "refers_silent_rot_to_yin": (
        # subject (silent-rot / correctness / tautological / wrong-contract / test
        # silent-rot) ... refer ... (yin | code-reviewer). The subject must precede the
        # referral act, binding the two.
        rx(
            r"(test\s+silent[- ]rot|silent[- ]rot\s*/\s*correctness|silent[- ]rot|"
            r"tautolog\w*|wrong[- ]contract|test\s+correctness)"
            r"[\s\S]{0,160}refer[\s\S]{0,40}((samsara:)?code[- ]reviewer|yin)"
        ),
        # refer ... subject: the referral act names the silent-rot / correctness subject
        # as what is being handed off.
        rx(
            r"refer[\s\S]{0,80}(test\s+silent[- ]rot|silent[- ]rot\s*/\s*correctness|"
            r"silent[- ]rot|tautolog\w*|wrong[- ]contract|test\s+correctness)"
        ),
    ),
}

# Dispatch propagation (DC4 — core of task-4): BOTH reviewer dispatch BLOCKS in
# skills/implement/dispatch-template.md must carry a test-quality review instruction,
# so the gate is actually ASKED at dispatch time. A reviewer agent that documents the
# rule while the dispatch never asks for it is exactly DC4.
#
# OVER-FIT POLE: keying on bare "test" / "review" (the template is full of both). So
# each token binds the REVIEW instruction to TEST QUALITY / brittle-or-tautological
# tests / the test contract. Checked SEPARATELY inside each dispatch block (not the
# whole doc), so a single prompt added to one block cannot satisfy both.
#
# PRESENCE-NOT-POLARITY guard (yin Important fix). The dangerous tokenization here was a
# bare `rx(r"test[- ]quality")`: it fires on a block that merely says "ensure test
# quality" / "## Test-Quality Review" with NO brittle / over-fit / tautological /
# silent-green / contract enforcement content. With that bare token in the OR-tuple, a
# future author could gut the enforcement instructions (delete the brittle/tautological/
# contract bullets) and keep only a "Test-Quality" heading, and the gate would stay
# falsely COVERED — the dispatch would no longer ASK for the review that makes the gate
# real (DC4), while the check stays green. So the bare `test[- ]quality` token is
# REMOVED. The concept now REQUIRES the dispatch block to actually ask for brittle /
# over-fit / tautological / silent-green / contract review, not merely say "test
# quality". A block that says only "ensure good test quality" is reported MISSING; the
# polarity death test (test_bare_test_quality_mention_is_missing_dispatch_concept) proves
# the enforcement content is load-bearing, not mere phrase presence.
DISPATCH_TEST_QUALITY_PROMPT = {
    "dispatch_asks_for_test_quality": (
        rx(
            r"(review|assess|check)\w*[^.?!\n]{0,60}test\w*[^.?!\n]{0,40}(brittle|over[- ]?fit|tautolog|silent[- ]green|contract)"
        ),
        rx(r"(brittle|over[- ]?fit|tautolog|silent[- ]green)[^.?!\n]{0,60}test"),
        rx(r"whether\s+the\s+tests?\s+assert\w*[^.?!\n]{0,60}contract"),
    ),
}


# DAMP Over DRY: tests favor readable, descriptive duplication over indirection.
# NOTE ON PLACEMENT: this is a REFERENCE-doc cohort group (it is merged into
# REFERENCE_CONCEPTS below, unlike the PLANNING_* groups above which are imported only
# by the planning evaluator). It sits here, after the PLANNING_* groups, purely for
# historical append-order; conceptually it belongs with CONTRACT_GATE..UNIT_VS_DEATH.
# Left in place to avoid a churny reorder; this comment marks the cohort it belongs to.
DAMP_OVER_DRY = {
    "damp_over_dry": (
        rx(r"damp\s+over\s+dry"),
        "damp",
        rx(r"descriptive\s+and\s+meaningful\s+phrases?"),
    ),
}


# Assertion discipline (iteration-fix-2). Across all six tasks of this feature the
# SAME failure-mode family was caught six times by review: an assertion that proves a
# topic is *mentioned* rather than *asserted in the right direction*. The reference's
# Contract Gate / both-poles material teaches the principle; this group pins the five
# CONCRETE sub-rules the build proved necessary. The unifying principle: an assertion is
# only as strong as its weakest clause, and must be able to fail in the DIRECTION the
# contract cares about. These concepts belong to the reference surface (the reference is
# where the discipline is taught), so this group joins REFERENCE_CONCEPTS below.
#
# SELF-DISCIPLINE (load-bearing): this is the worst possible place to commit the very
# bug it documents, so every token below itself obeys all five rules. None is a bare
# common word (no green-by-construction); each directional concept binds its keyword to
# its DIRECTION (no presence-not-polarity); no token is the loosest member of an OR that
# would set the floor. The hostile-decoy + wrong-direction death tests in
# `test_assertion_discipline.py` prove these tokens can go red.
#
# PLACEMENT (cohesion): like DAMP_OVER_DRY above, this is a REFERENCE-surface cohort group
# (merged into REFERENCE_CONCEPTS below) sitting here after the PLANNING_* groups purely by
# append-order, not by topic. Conceptually it belongs with CONTRACT_GATE..UNIT_VS_DEATH.
# Left in place to avoid a churny reorder; this comment marks the cohort it belongs to.
ASSERTION_DISCIPLINE = {
    # RULE 1 — weakest-token-in-an-OR floor. DIRECTIONAL: the doc must WARN that the
    # loosest token in an any()/OR tuple sets the floor and nullifies its strict
    # siblings. A bare "weakest"/"OR" mention is green-by-construction, so each token
    # binds the loosest/weakest CLAUSE to the act of setting a floor / nullifying /
    # dominating its strict siblings.
    "weakest_clause_sets_the_floor": (
        rx(r"(weakest|loosest)\s+(token|clause|member|alternative)"),
        rx(r"(weakest|loosest)[^.?!>\n]{0,80}(set\w*\s+the\s+floor|floor)"),
        rx(
            r"(loosest|weakest)[^.?!>\n]{0,80}(nullif\w*|silenc\w*|dominat\w*|swallow\w*)[^.?!>\n]{0,40}(strict|sibling)"
        ),
        rx(r"as\s+strong\s+as\s+its\s+weakest\s+(clause|token|member)"),
    ),
    # RULE 2 — presence-not-polarity. DIRECTIONAL: the doc must distinguish matching a
    # concept's KEYWORD from asserting its DIRECTION, and prescribe a wrong-direction
    # decoy (the real phrase in the WRONG direction → concept reported MISSING). A bare
    # "polarity"/"direction" mention is too weak; each token binds presence-vs-direction
    # to the cure (a wrong-direction / wrong-polarity decoy, or endorsing-the-wrong-
    # practice passing identically).
    #
    # SELF-EXEMPLAR (yin Important fix, iteration-fix-2 review): the FIRST token used to
    # be a bare `rx(r"presence[- ]not[- ]polarity")`. That fired on the section heading
    # itself REGARDLESS of whether the doc TEACHES the rule or ENDORSES the bug ("presence-
    # not-polarity is acceptable when the rule is obvious" would have matched) — the exact
    # weakest-OR floor (rule 1) and presence-not-polarity (rule 2) bug this section forbids,
    # committed in the section's own guard. Now the phrase is bound to its cure DIRECTION
    # (reject / wrong direction / must fail / polarity holds) within a TIGHT clause
    # (`[^.?!>\n]`, NOT `[^.]` — no boundary bleed, rule 5). The wrong-direction decoy
    # test_endorsing_presence_not_polarity_is_missing_concept proves it goes red on an
    # endorsement.
    "presence_not_polarity": (
        rx(
            r"presence[- ]not[- ]polarity[^.?!>\n]{0,80}(reject|wrong\s+direction|must\s+fail|polarity\s+holds)"
        ),
        rx(
            r"(reject|wrong\s+direction|must\s+fail|polarity\s+holds)[^.?!>\n]{0,80}presence[- ]not[- ]polarity"
        ),
        rx(r"(wrong[- ]direction|wrong[- ]polarity)\s+decoy"),
        rx(
            r"endors\w*[^.?!>\n]{0,80}(wrong|opposite)[^.?!>\n]{0,40}(practice|direction|polarity)"
        ),
        rx(
            r"match\w*\s+the\s+(keyword|concept)[^.?!>\n]{0,60}not\s+(its\s+)?(direction|polarity)"
        ),
    ),
    # RULE 3 — green-by-construction. DIRECTIONAL: the doc must warn that a token keyed
    # on a common word ("date", "test", "contract") matches almost any prose and can
    # never go red, and prescribe an unrelated-prose decoy asserting ZERO concepts
    # covered. A bare "common word" mention is too weak; each token binds the
    # common-word key to the failure (never goes red / matches any prose) or to the cure
    # (unrelated/hostile decoy → zero covered).
    #
    # SELF-EXEMPLAR (yin Important fix, iteration-fix-2 review): the FIRST token used to
    # be a bare `rx(r"green[- ]by[- ]construction")`. Worse than a weak floor — it was the
    # ONLY token matching the real section (the stricter siblings' gaps span the doc's
    # line-wrap, which the tight `[^.?!>\n]` clause correctly forbids), so the concept was
    # carried ENTIRELY by a heading-string match that fires whether the doc TEACHES or
    # ENDORSES the bug ("green-by-construction tokens are fine here" would have matched).
    # Now the phrase is bound to its failure DIRECTION (never go red / matches almost any
    # prose / tighten) within a TIGHT clause, and the doc carries a single-line directional
    # sentence the token matches. The wrong-direction decoy
    # test_endorsing_green_by_construction_is_missing_concept proves it goes red on an
    # endorsement.
    "green_by_construction": (
        rx(
            r"green[- ]by[- ]construction[^.?!>\n]{0,80}(never\s+(go|turn)\s+red|match\w*\s+(almost\s+)?any|tighten)"
        ),
        rx(
            r"(never\s+(go|turn)\s+red|match\w*\s+(almost\s+)?any|tighten)[^.?!>\n]{0,80}green[- ]by[- ]construction"
        ),
        rx(
            r"(common\s+word|bare\s+substring|bare\s+token)[^.?!>\n]{0,80}(never\s+(go|turn)\s+red|match\w*\s+(almost\s+)?any)"
        ),
        rx(
            r"(unrelated|hostile)\s+(prose|decoy)[^.?!>\n]{0,80}zero\s+(concept|coverage)"
        ),
        rx(
            r"(unrelated|hostile)\s+(prose|decoy)[^.?!>\n]{0,80}(all\s+)?(concepts?\s+)?missing"
        ),
    ),
    # RULE 4 — order-by-label. DIRECTIONAL: an ORDERING claim ("X before Y") must be a
    # STRUCTURAL position check (index_of(X) < index_of(Y)), NOT a label-presence token,
    # and a reversed-order fixture must go red. A bare "order"/"before" mention is too
    # weak (it is exactly the label-presence trap this rule forbids); each token binds
    # ordering to a STRUCTURAL/positional index comparison or to the reversed-order
    # fixture going red.
    "order_by_structural_position": (
        rx(r"index_of\([^)]*\)\s*<\s*index_of"),
        rx(
            r"(structural|positional)\s+(position|index|order)[^.?!>\n]{0,80}(order|before|preced)"
        ),
        rx(
            r"(order|ordering)[^.?!>\n]{0,80}(structural|positional)\s+(position|index)"
        ),
        rx(r"reversed[- ]order\s+fixture[^.?!>\n]{0,60}red"),
    ),
    # RULE 5 — boundary bleed. DIRECTIONAL: a proximity regex's stop class must be a
    # TIGHT clause (stop at .?!> and newline), NOT a loose [^.] that lets a far-away word
    # leak across a block boundary. A bare "boundary"/"regex" mention is too weak; each
    # token binds the loose stop class to the leak/bleed, or names the tight stop class
    # as the cure.
    "boundary_bleed_tight_clause": (
        rx(r"boundary\s+bleed"),
        rx(r"\[\^\.\]"),  # the loose stop class named as the offender
        rx(
            r"(stop\s+class|proximity\s+regex)[^.?!>\n]{0,80}(leak|bleed|cross\w*\s+(a\s+)?block)"
        ),
        rx(r"(tight|bound\w*)\s+(clause|stop\s+class)[^.?!>\n]{0,80}(newline|\.\?!)"),
    ),
}


# --- Aggregate map used by this task's evaluator ----------------------------
#
# The reference doc `references/test-contract.md` must cover EVERY concept below.
# Tasks 2-6 import the narrower groups above; this aggregate is the full catalog
# the canonical reference is responsible for.
#
# DELIBERATELY EXCLUDED: CONTRACT_BOUND_UNIT and FIX_THE_TEST are NOT merged here.
# They are *implementer-surface* concepts — instructions the implementer AGENT
# (agents/implementer.md) must carry (bind a unit test to a named contract source;
# fix a test bound to the WRONG contract instead of bending the implementation).
# The canonical reference DESCRIBES the protocol; it is not required to issue those
# agent-facing imperatives, so adding them here would false-fail the reference
# evaluator. Future task authors: do NOT blindly add new groups to this aggregate —
# add a group only if references/test-contract.md is genuinely responsible for the
# concept; agent/skill/reviewer-surface concepts stay in their own groups.
REFERENCE_CONCEPTS: dict[str, tuple[Token, ...]] = {
    **CONTRACT_GATE,
    **BRITTLENESS_FILTER,
    **SILENT_GREEN_GUARD,
    **BOTH_POLES_FIX,
    **SNAPSHOT_GOLDEN,
    **BOUNDARY_SPY,
    **MINIMUM_CONTRACT,
    **UNIT_VS_DEATH,
    **DAMP_OVER_DRY,
    **ASSERTION_DISCIPLINE,
}
