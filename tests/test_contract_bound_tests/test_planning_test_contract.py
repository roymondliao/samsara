"""Evaluator for planning's task-contract origin (Task 5).

Contract-bound unit tests work best when the contract is named UPSTREAM, at planning
time, so the implementer references it instead of inferring a contract from the current
implementation. Two surfaces carry that obligation:

  * The TEMPLATE `skills/planning/task-format.md` — every generated task gets a
    required `Unit Test Contract` section, and a Rule forbids generic "appropriate
    tests" wording (a contract source must be OBSERVABLE/named).
  * The decomposition step of `skills/planning/SKILL.md` — it must tell the planner to
    name each task's unit-test contract source alongside the death test requirements.

CRITICAL SCOPE (hard): the evaluator inspects the TEMPLATE only. It must NEVER glob
`changes/**/task-*.md` and enforce the section on historical task files — 64 of 70
existing task files predate the section, so a global check would BRICK the suite on
pre-existing artifacts. A dedicated death test pins this non-enforcement so a future
"tighten the check" edit that starts globbing all task files goes RED.

Death tests run BEFORE the unit tests and target SILENT failure paths — the ones that
stay GREEN while the planning surface has rotted:

  DC1 The template has Death Test Requirements but no Unit Test Contract section →
      every generated task leaves the unit-test contract implicit; implementers infer
      a contract from the implementation (over-fit by construction).
  DC2 The decomposition step never tells the planner to name the unit-test contract
      source → the contract is never named upstream; the whole feature is hollow.
  DC3 The template adds a section heading but ALLOWS generic "appropriate tests"
      wording → the section is satisfied by "write appropriate tests", which names no
      observable contract source (label-not-structure).
  DC4-HISTORICAL The evaluator asserts the Unit Test Contract section on HISTORICAL
      task files instead of the template → enforcing it globally bricks the suite on
      64 pre-existing artifacts. Pinned so a future glob-everything edit reddens.
  DC-DECOY The new planning-surface tokens are green-by-construction (key on bare
      common words) → they can never go red.
  DC-POLARITY The forbid-generic-wording token matches a template that ENDORSES the
      generic wording → the polarity is not actually checked.

Each death test names the silent-failure mode it pins; that failure mode IS this death
test's contract, so (per the protocol) it is allowed to be exact here.
"""

from __future__ import annotations

from tests.test_contract_bound_tests._contract_tokens import (
    PLANNING_DECOMPOSITION_NAMES_CONTRACT,
    PLANNING_FORBID_GENERIC_UNIT_WORDING,
    PLANNING_UNIT_TEST_CONTRACT_SECTION,
)
from tests.test_contract_bound_tests._token_lib import (
    ROOT,
    concept_present,
    concepts_covered_by,
    missing_concepts,
    pinned_heading_offenders,
)

# Path to THIS evaluator's own source — grepped by the non-enforcement death test to
# prove the evaluator never globs historical task files.
EVALUATOR_SOURCE = (
    ROOT / "tests" / "test_contract_bound_tests" / "test_planning_test_contract.py"
)

# Load-bearing anchors: the evaluator is meaningless against any other file. A move of
# either file is a single-line change here. These pin the evaluator to the TEMPLATE and
# the orchestration SKILL — NEVER a glob of changes/**/task-*.md (see the historical
# non-enforcement death test below).
TASK_FORMAT = ROOT / "skills" / "planning" / "task-format.md"
SKILL = ROOT / "skills" / "planning" / "SKILL.md"

# A KNOWN historical task file that LACKS the Unit Test Contract section but DOES carry
# Death Test Requirements. It is the fixture for the non-enforcement death test: it
# proves the evaluator does NOT read historical artifacts. If this file is ever
# migrated to add the section, pick another pre-2026-05-30 task file that still lacks
# it — the point is that SOME historical file lacks the section and the suite stays
# green, NOT that this exact file is frozen.
HISTORICAL_TASK_WITHOUT_SECTION = (
    ROOT / "changes" / "2026-04-21_security-privacy-review" / "tasks" / "task-1.md"
)


def read_task_format() -> str:
    return TASK_FORMAT.read_text(encoding="utf-8")


def read_planning_skill() -> str:
    # Distinct name from the implement-skill evaluator's read_skill(): that one reads
    # skills/implement/SKILL.md, this reads skills/planning/SKILL.md. Same bare name
    # across two evaluators is a confusion hazard, so this one is qualified.
    return SKILL.read_text(encoding="utf-8")


# --- Death tests -----------------------------------------------------------


class TestTemplateRequiresUnitTestContractSectionDeath:
    def test_template_with_death_tests_must_have_unit_test_contract_section(self):
        # DEATH [DC1-IMPLICIT-CONTRACT]: the template lists Death Test Requirements as a
        # required section. If it requires death tests but NOT a Unit Test Contract
        # section, every generated task leaves the unit-test contract implicit and
        # implementers infer the contract from the implementation — over-fit by
        # construction. The precondition (death-test section present) makes the gap a
        # real asymmetry, not a vacuous pass.
        text = read_task_format()
        assert "death test" in text.lower(), (
            "precondition: task-format.md must require a Death Test Requirements "
            "section for this asymmetry to bite; the template structure changed "
            "unexpectedly."
        )
        for key, tokens in PLANNING_UNIT_TEST_CONTRACT_SECTION.items():
            assert concept_present(text, tokens), (
                f"SILENT FAILURE [DC1-IMPLICIT-CONTRACT]: task-format.md requires "
                f"Death Test Requirements but not the Unit Test Contract concept "
                f"'{key}'. Generated tasks leave the unit-test contract implicit; "
                f"implementers infer a contract from the implementation."
            )


class TestTemplateForbidsGenericWordingDeath:
    def test_template_forbids_generic_appropriate_tests_wording(self):
        # DEATH [DC3-LABEL-NOT-STRUCTURE]: a Unit Test Contract heading that ALLOWS
        # "write appropriate tests" is a label with no structure — it names no
        # observable contract source. The template must carry a forbid-rule (parallel
        # to the existing "Death tests listed explicitly — not 'add appropriate death
        # tests'" rule) requiring an observable/named contract source.
        text = read_task_format()
        for key, tokens in PLANNING_FORBID_GENERIC_UNIT_WORDING.items():
            assert concept_present(text, tokens), (
                f"SILENT FAILURE [DC3-LABEL-NOT-STRUCTURE]: task-format.md does not "
                f"forbid generic unit-test wording / require an observable contract "
                f"source (concept '{key}'). The section is satisfiable by 'write "
                f"appropriate tests', which names no contract."
            )


class TestDecompositionNamesContractSourceDeath:
    def test_skill_decomposition_names_unit_test_contract_source(self):
        # DEATH [DC2-NEVER-NAMED-UPSTREAM]: the decomposition step already tells the
        # planner each task "includes death test requirements". If it never tells the
        # planner to name the unit-test contract source ALONGSIDE that, the contract is
        # never named upstream and the whole feature is hollow.
        text = read_planning_skill()
        assert "death test" in text.lower(), (
            "precondition: SKILL.md decomposition must name death test requirements "
            "for the parallel obligation to have an anchor; the skill changed "
            "unexpectedly."
        )
        for key, tokens in PLANNING_DECOMPOSITION_NAMES_CONTRACT.items():
            assert concept_present(text, tokens), (
                f"SILENT FAILURE [DC2-NEVER-NAMED-UPSTREAM]: SKILL.md decomposition "
                f"names death test requirements but not the unit-test contract source "
                f"concept '{key}'. The contract is never named upstream at planning "
                f"time."
            )


class TestNoHistoricalEnforcementDeath:
    """DC4-HISTORICAL: the evaluator must inspect the TEMPLATE, never a glob of
    historical task files.

    64 of 70 existing task files predate the Unit Test Contract section. A "tighten the
    check" edit that starts asserting the section on `changes/**/task-*.md` would brick
    the suite on those pre-existing artifacts. These tests pin the non-enforcement:
    (a) the evaluator's declared target is the single template path, and
    (b) a KNOWN historical task file LACKS the section yet the evaluator stays green —
        proving the evaluator does not read historical artifacts.
    """

    def test_evaluator_target_is_the_template_not_a_glob(self):
        # The evaluator's anchors are single file paths, not directory globs. If a
        # future edit replaces TASK_FORMAT with a glob over changes/, this assertion
        # (that the target is a FILE, ending in the template name) goes RED.
        assert TASK_FORMAT.is_file(), (
            "SILENT FAILURE [DC4-HISTORICAL]: the evaluator's TASK_FORMAT target is "
            "not a single file. It must be the template skills/planning/task-format.md, "
            "never a glob over changes/**/task-*.md."
        )
        assert TASK_FORMAT.name == "task-format.md", (
            "SILENT FAILURE [DC4-HISTORICAL]: TASK_FORMAT no longer points at the "
            "template task-format.md."
        )
        # The template path must NOT live under changes/ (historical artifacts do).
        assert "changes" not in TASK_FORMAT.parts, (
            "SILENT FAILURE [DC4-HISTORICAL]: TASK_FORMAT points under changes/ — the "
            "evaluator would be reading a historical artifact, not the template."
        )

    def test_evaluator_source_has_no_directory_walk_and_historical_task_would_brick(
        self,
    ):
        # NON-ENFORCEMENT PROVEN TWO WAYS (the name now states both halves; the prior
        # name "lacks_section_and_suite_stays_green" only described the fixture check and
        # never asserted the evaluator ignores historical files):
        #
        # (a) ENFORCEMENT IMPOSSIBILITY: parse THIS evaluator's OWN source to AST and
        #     assert it makes NO directory-walk call — `.glob`, `.rglob`, `.iterdir`,
        #     `os.walk`, `os.listdir`, `os.scandir`, or `glob.glob`. A directory walk is
        #     the ONLY mechanism by which the evaluator could start enforcing the section
        #     on `changes/**/task-*.md`. AST (not substring grep) is used so the check is
        #     immune to the docstring/comment that legitimately MENTIONS the forbidden
        #     pattern to document this guard — a substring grep would false-fail on its
        #     own prose. This catches a SECOND walk added ANYWHERE in the file, which the
        #     TASK_FORMAT-constant guard alone did not.
        #
        # (b) BRICK PROOF: a real historical task file LACKS the (now-directional,
        #     required) Unit Test Contract section yet HAS Death Test Requirements, and
        #     the section concept is MISSING from it. So IF (a) were ever violated and the
        #     evaluator walked this file, the section requirement WOULD fail and the suite
        #     WOULD brick — the concrete harm the template-only scope prevents.
        import ast

        source = EVALUATOR_SOURCE.read_text(encoding="utf-8")
        tree = ast.parse(source)
        walk_methods = {"glob", "rglob", "iterdir", "scandir"}
        os_walks = {"walk", "listdir", "scandir"}
        offending: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                attr = node.func.attr
                # Path.glob/.rglob/.iterdir/.scandir — any receiver.
                if attr in walk_methods:
                    offending.append(f".{attr}(")
                # os.walk / os.listdir / os.scandir / glob.glob
                if isinstance(node.func.value, ast.Name):
                    base = node.func.value.id
                    if base == "os" and attr in os_walks:
                        offending.append(f"os.{attr}(")
                    if base == "glob" and attr == "glob":
                        offending.append("glob.glob(")
        assert not offending, (
            "SILENT FAILURE [DC4-HISTORICAL]: the planning evaluator's source makes a "
            f"directory-walk call {sorted(set(offending))}. The evaluator must read "
            "single named files (TASK_FORMAT, SKILL) only and NEVER walk changes/ — a "
            "global check bricks the suite on 64 pre-existing historical task files."
        )

        # (b) Brick proof on a real historical fixture.
        assert HISTORICAL_TASK_WITHOUT_SECTION.is_file(), (
            f"fixture missing: {HISTORICAL_TASK_WITHOUT_SECTION} no longer exists. Pick "
            f"another pre-2026-05-30 task file that lacks the Unit Test Contract "
            f"section to keep the non-enforcement guarantee anchored."
        )
        historical = HISTORICAL_TASK_WITHOUT_SECTION.read_text(encoding="utf-8")
        assert "death test" in historical.lower(), (
            "fixture invalid: the chosen historical task file does not carry Death "
            "Test Requirements; it cannot demonstrate the death-without-contract "
            "asymmetry that a global check would brick on."
        )
        # The required-section CONCEPT must be MISSING from the historical file: that is
        # exactly what a glob would fail on. (Now that the concept is directional —
        # name+MUST — this asserts the historical file lacks the *required* section, the
        # precise thing the brick would trip over.)
        missing = missing_concepts(historical, PLANNING_UNIT_TEST_CONTRACT_SECTION)
        assert missing, (
            "SILENT FAILURE [DC4-HISTORICAL]: the Unit Test Contract section concept is "
            "NOT missing from the historical task file — so this fixture can no longer "
            "demonstrate that a global glob would brick the suite. Repoint the fixture."
        )


class TestNewConceptsAreNotGreenByConstructionDeath:
    """DC-DECOY: the new planning-surface tokens must be able to go RED."""

    def test_new_concepts_fail_on_hostile_decoy(self):
        # Sprinkle the common words ("unit", "test", "contract", "appropriate",
        # "death", "source") WITHOUT the planning concepts and assert every new concept
        # is reported missing. Any concept covered here is green-by-construction.
        decoy = (
            "The unit of measure is a metre. We test the soup before serving. The "
            "social contract binds citizens. Wear appropriate attire. A river has a "
            "source in the mountains. Death of summer comes with the first frost."
        )
        new_groups = {
            **PLANNING_UNIT_TEST_CONTRACT_SECTION,
            **PLANNING_FORBID_GENERIC_UNIT_WORDING,
            **PLANNING_DECOMPOSITION_NAMES_CONTRACT,
        }
        covered = concepts_covered_by(decoy, new_groups)
        assert not covered, (
            "SILENT FAILURE [DC-DECOY]: these new planning-surface concepts were "
            f"reported covered by unrelated decoy prose: {sorted(covered)}. Their "
            "tokens key on common words and can never go red. Tighten them to "
            "intent-bearing tokens bound to the unit-test contract concept."
        )

    def test_new_concept_tokens_are_not_pinned_headings(self):
        # A token must not BE a markdown heading string ("## ..."), or the check passes
        # only while a specific heading survives — the exact over-fit this feature
        # kills. Uses the authoritative shared scan.
        new_groups = {
            **PLANNING_UNIT_TEST_CONTRACT_SECTION,
            **PLANNING_FORBID_GENERIC_UNIT_WORDING,
            **PLANNING_DECOMPOSITION_NAMES_CONTRACT,
        }
        offenders = pinned_heading_offenders(new_groups)
        assert not offenders, (
            "SILENT FAILURE [DC-PINNED-HEADING]: a new concept token is a markdown "
            f"heading string: {offenders}. Tokens must be intent-bearing concepts."
        )

    def test_endorsing_generic_wording_is_missing_forbid_rule(self):
        # DC-POLARITY: the forbid-generic-wording concept must be DIRECTIONAL. A
        # template that ENDORSES the generic wording ("for unit tests, write
        # appropriate tests as you see fit") must be reported MISSING the forbid rule —
        # it names no observable contract source. If this prose satisfied the concept,
        # the polarity would be unchecked and a hollow section would pass review.
        endorsing = (
            "## Unit Test Contract\n"
            "For unit tests, write appropriate tests as you see fit. Add appropriate "
            "unit tests that cover the behaviour. The unit test contract section is "
            "where you note appropriate tests."
        )
        assert not concepts_covered_by(
            endorsing, PLANNING_FORBID_GENERIC_UNIT_WORDING
        ), (
            "SILENT FAILURE [DC-POLARITY]: PLANNING_FORBID_GENERIC_UNIT_WORDING was "
            "reported covered by prose that ENDORSES 'appropriate tests'. The token "
            "must require the forbid-rule / an observable contract source, or a hollow "
            "section that says 'write appropriate tests' passes review."
        )

    def test_negating_decomposition_obligation_is_missing_concept(self):
        # DC-POLARITY-DECOMP (CRITICAL — presence-not-polarity): a hostile decoy that
        # USES the compound phrase "unit-test contract source" in a NON-endorsing
        # context (negation / disclaimer) must be reported MISSING the decomposition
        # concept. The earlier bare token rx(r"unit[- ]test\s+contract(\s+source)?")
        # matched ANY mention of the phrase, so a SKILL.md that DROPS the decomposition
        # obligation but still names the phrase would pass. The DC-DECOY test missed
        # this because its decoy AVOIDED the compound phrase; this decoy USES it while
        # negating the obligation, so it pins that the concept requires the decomposition
        # ACT (naming the source / named upstream), not phrase presence.
        negating = (
            "Note: the unit-test contract source is NOT required at planning time. "
            "Whether to name a unit-test contract source is left to the implementer's "
            "discretion; the unit test contract need not be specified during "
            "decomposition."
        )
        assert not concepts_covered_by(
            negating, PLANNING_DECOMPOSITION_NAMES_CONTRACT
        ), (
            "SILENT FAILURE [DC-POLARITY-DECOMP]: PLANNING_DECOMPOSITION_NAMES_CONTRACT "
            "was reported covered by prose that NEGATES the decomposition obligation "
            "while USING the phrase 'unit-test contract source'. The token matches mere "
            "phrase presence, not the decomposition act — a SKILL.md that drops the "
            "obligation but mentions the phrase would pass review. Tokens must bind the "
            "naming ACT / 'named upstream' direction."
        )

    def test_optional_section_template_is_missing_required_concept(self):
        # DC-POLARITY-REQUIRED (presence-not-requirement, BOUNDARY-BLEED hardened): a
        # FULL-FORM template that keeps the STANDARD Death Test Requirements comment
        # block ("<!-- What death tests must be written BEFORE implementation? -->") AND
        # marks the Unit Test Contract section OPTIONAL must be reported MISSING the
        # `unit_test_contract_section_required` concept.
        #
        # WHY FULL-FORM (yin Important): the earlier fixture OMITTED the DTR comment, so
        # it did not catch the realistic adversarial case. With a `[^.]` boundary class
        # the BACKWARD token (\bmust\b ... unit-test contract) lets the `must` inside the
        # DTR comment bleed ~109 chars across `?`, `-->`, newlines and dashes (none of
        # which is a `.`) and bind to the "## Unit Test Contract" heading below — so a
        # template that OPTIONALIZES the section but keeps the standard DTR block
        # false-passes (silent-green). The fixture below reproduces exactly that layout:
        # it MUST report MISSING after the boundary is tightened to `[^.?!>\n]` (which
        # stops the bleed at the newline), and it would FALSELY pass on the old `[^.]`
        # token — the mutate-to-red proof for the boundary fix.
        full_form_optional_template = (
            "## Death Test Requirements\n"
            "<!-- What death tests must be written BEFORE implementation? -->\n"
            "- Test: <silent failure scenario>\n"
            "- Test: <unknown outcome scenario>\n"
            "\n"
            "## Unit Test Contract\n"
            "Unit Test Contract section: optional. You may add a unit test contract "
            "section if it helps; the unit-test contract is not mandatory and can be "
            "skipped at planning time."
        )
        assert not concepts_covered_by(
            full_form_optional_template, PLANNING_UNIT_TEST_CONTRACT_SECTION
        ), (
            "SILENT FAILURE [DC-POLARITY-REQUIRED]: PLANNING_UNIT_TEST_CONTRACT_SECTION "
            "was reported covered by a FULL-FORM template that keeps the standard Death "
            "Test Requirements comment block but marks the Unit Test Contract section "
            "OPTIONAL. The key claims 'required', but a `[^.]` boundary lets the `must` "
            "inside the DTR comment bleed across newlines and bind to the section name "
            "below. Tighten the boundary class (e.g. `[^.?!>\\n]`) so `must` and the "
            "section name share a clause/line."
        )


# --- Unit tests ------------------------------------------------------------


class TestPlanningTaskFormatContractOrigin:
    def test_template_requires_unit_test_contract_section(self):
        text = read_task_format()
        missing = missing_concepts(text, PLANNING_UNIT_TEST_CONTRACT_SECTION)
        assert not missing, (
            f"task-format.md must require a Unit Test Contract section; missing "
            f"concepts: {missing}"
        )

    def test_template_forbids_generic_unit_test_wording(self):
        text = read_task_format()
        missing = missing_concepts(text, PLANNING_FORBID_GENERIC_UNIT_WORDING)
        assert not missing, (
            f"task-format.md must forbid generic 'appropriate tests' wording and "
            f"require an observable contract source; missing concepts: {missing}"
        )


class TestPlanningSkillDecompositionContractOrigin:
    def test_decomposition_names_unit_test_contract_source(self):
        text = read_planning_skill()
        missing = missing_concepts(text, PLANNING_DECOMPOSITION_NAMES_CONTRACT)
        assert not missing, (
            f"SKILL.md decomposition must name the unit-test contract source alongside "
            f"death test requirements; missing concepts: {missing}"
        )
