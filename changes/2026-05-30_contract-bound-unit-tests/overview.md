# Overview: contract-bound-unit-tests

## Current Note

This feature's original source-inspection evaluator architecture was later
pruned by `changes/2026-06-03_prune-contract-bound-tests`. The live platform now
keeps only high-value workflow-invariant tests for named surfaces, implement
ordering, reviewer dispatch, and planning scope. The historical task/scar files
below still describe the original implementation path and should not be read as
current evaluator architecture.

## Goal

Make Samsara's live instructions require writing and reviewing unit tests that
assert behavioral contracts rather than implementation details. Source
inspection verifies the protocol surfaces; it does not prove runtime agent
obedience without a representative live implement run.

## Architecture

Add a `references/test-contract.md` catalog and wire a lean mandatory gate
through implementer, implement orchestration, reviewer agents, dispatch
templates, and planning task format. The feature is instruction/protocol level
and is verified by fixture-driven source inspection tests.

## Tech Stack

Markdown-based Samsara skills and agents, pytest-based source inspection tests,
existing converter/format validation test suites.

## Key Decisions

- Contract-bound tests: unit tests must assert behavior, public API/schema,
  user-visible output, documented artifact shape, stable boundary interaction,
  or bug/death-case contract.
- Both-poles guard: brittle over-fit tests and vague silent-green tests are both
  failures.
- Reference file: detailed test-pattern catalog lives in
  `references/test-contract.md` to keep `skills/implement/SKILL.md` lean.
- Reviewer enforcement: `code-reviewer` owns rotten tests as silent rot;
  `code-quality-reviewer` owns structural test coupling.
- Planning origin: task files should name unit-test contract source before
  implementation begins.
- No scar schema change: brittle tests can be recorded under existing
  `silent_failure_conditions`.
- Self-exemplar (superseded): this feature originally used concept-token
  evaluators as its own exemplar. That evaluator layer was later pruned because
  it over-constrained markdown evolution; live tests now guard workflow
  invariants instead of prose coverage.
- Behavioral gap is accepted, not hidden: static source inspection proves the
  protocol is present, not that agents write contract-bound tests. Task-6
  recommends a representative live implement run as the behavioral check.
- No retroactive migration: the required Unit Test Contract section is enforced
  on the task template and new tasks only, not on the 64 historical task files.
- Fix-the-test reconciliation: the implementer execution-order line
  "implement minimal code to pass all tests" is amended, not just annotated.

## Death Cases Summary

1. Brittle unit tests pass review and later fail under behavior-preserving
   refactor or fixture expansion.
2. Vague unit tests pass review and stay green when behavior actually breaks.
3. Reviewer agents document test-quality rules but dispatch prompts never ask
   them to apply those rules.
4. The protocol is documented on every surface but agent behavior never changes
   (documentation present != behavior changed).
5. The evaluator itself is over-fit (pins headings/prose) and the feature
   refutes its own thesis; or five evaluators drift with divergent token lists.
6. The evaluator enforces the new section on historical task files and bricks
   the suite.
7. A perfunctory contract label ("# contract: it works") satisfies the gate.

## File Map

- `references/test-contract.md` - canonical contract-bound unit-test protocol and catalog.
- `agents/implementer.md` - test writer behavior, STEP 0 drift check, self-review gate.
- `skills/implement/SKILL.md` - orchestration-level Test Contract Gate and red flags.
- `skills/implement/dispatch-template.md` - reviewer prompt propagation.
- `agents/code-reviewer.md` - yin-side test-quality gate and silent-rot classification.
- `agents/code-quality-reviewer.md` - structural test coupling review.
- `skills/planning/task-format.md` - upstream Unit Test Contract section.
- `skills/planning/SKILL.md` - optional task decomposition wording.
- `tests/test_contract_bound_tests/` - current high-value workflow-invariant
  tests; the original concept-token helper/evaluator files were pruned by
  `changes/2026-06-03_prune-contract-bound-tests`.
