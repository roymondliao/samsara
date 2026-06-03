# Plan: contract-bound-unit-tests

## Pre-thinking Commitments Consumed

This plan is based on the May 30, 2026 review discussion rather than a separate
pre-thinking artifact.

- Decision: Proceed
- Accepted gaps: none
- System design constraints:
  - Keep `skills/implement/SKILL.md` lean; put the heavy testing catalog in a
    reference file.
  - The implementer agent owns test-writing behavior.
  - The reviewer agents and dispatch template must enforce the test-quality gate.
  - Planning task files should name the observable unit-test contract upstream.
- Primary evaluator: fixture-driven source inspection of the Samsara skill,
  agent, dispatch-template, task-format, and reference files.
- Pass signal: every test-writing, orchestration, review, and planning path
  requires contract-bound unit tests and catches both over-fit and silent-green
  tests.
- Fail signal: any path can still say only "write unit tests" without naming the
  contract source, brittleness filter, and tautology guard.
- Feedback loop: update the missing instruction surface and re-run the focused
  evaluator.

## Goal

Make Samsara's implementation workflow produce unit tests that assert behavioral
contracts instead of implementation details, while still failing on real
regressions.

## Problem Statement

Current implement instructions require death tests before unit tests, but unit
tests are not constrained by test shape. Agents can satisfy TDD mechanically with
tests that pin private helpers, internal call sequences, arbitrary fixture
counts, incidental order, or full snapshots. Those tests can fail under valid
feature iteration, optimization, refactor, or bugfix work even when behavior is
preserved.

The opposite failure is also dangerous: after being told to avoid brittle tests,
an agent can write vague tests that only assert "not empty", "does not throw",
"contains something", or mock existence. These tests survive refactors but fail
to catch real regressions.

The fix is not "assert less." The fix is: assert the contract precisely and
assert nothing else.

## Architecture

Add a new testing reference at `references/test-contract.md`. Keep detailed
catalogs and examples there, and wire a short mandatory gate through the
implementer, implement skill, review agents, dispatch template, and planning
task format.

Current note: the evaluator architecture described in this plan was later
superseded by `changes/2026-06-03_prune-contract-bound-tests`. The live suite no
longer uses `_contract_tokens.py` or prose-wide concept-token coverage; it keeps
only high-value workflow-invariant tests. The implementation tasks below remain
historical context for how the feature was first built.

Role split:

- `agents/implementer.md` changes behavior at the test-writing point.
- `skills/implement/SKILL.md` carries orchestration-level constraints and points
  to the reference.
- `references/test-contract.md` carries the detailed rules and examples.
- `agents/code-reviewer.md` owns the yin-side review of rotten tests as silent
  rot paths.
- `agents/code-quality-reviewer.md` owns structural coupling in test design.
- `skills/implement/dispatch-template.md` makes reviewer prompts actually ask
  for test-quality review.
- `skills/planning/task-format.md` makes the contract source visible before
  implementation begins.
- The original plan used `tests/test_contract_bound_tests/_contract_tokens.py`
  as a shared concept-token source. That layer has been removed from the live
  suite; see the current note above.

## I/O With Unknown Output

Instruction and evaluator outputs use three states:

- `success`: all required instruction surfaces contain the contract-bound test
  protocol and the evaluator verifies it.
- `failure`: one or more required surfaces omit the contract source, brittle
  filter, tautology guard, reviewer gate, or planning contract origin.
- `unknown`: the evaluator cannot determine whether an instruction surface is
  covered because the file is missing, the heading changed, or the instruction
  uses generic language that cannot be tied to the test-contract protocol.

Unknown is a failure for this feature because a vague testing instruction is the
silent failure path.

## Contract-Bound Test Protocol

Every unit test must identify what contract it asserts. Valid contract sources:

- task acceptance criteria
- death case or bug reproduction
- public API/schema
- user-visible behavior
- documented artifact format
- stable boundary interaction, when the interaction is the feature

Every unit test must pass two questions:

1. Would this test still pass after a behavior-preserving refactor?
2. Would this test fail if the behavior actually broke?

If the answer to either question is no, the test is rotten. The fix may be to
fix the test, not the implementation.

## Death Cases

### Death Case 1: Brittle Test Passes Review

Trigger condition: an implementer writes a unit test tied to private helpers,
internal call sequence, arbitrary fixture count, incidental ordering, or a full
snapshot.

The lie: the test looks precise and gives fast TDD feedback.

The truth: a valid refactor, feature addition, fixture expansion, or
implementation cleanup can break the test even though behavior is preserved.

Detection: evaluator verifies implementer and reviewer instructions reject
over-fit tests and require contract source.

### Death Case 2: Silent-Green Test Passes Review

Trigger condition: an implementer avoids hard coding by writing only vague
assertions such as non-empty output, no exception, contains any value, or mock
exists.

The lie: the test is refactor-safe.

The truth: behavior can regress while the test stays green.

Detection: evaluator verifies the both-poles guard exists in implementer,
implement skill, reference, and reviewer prompts.

### Death Case 3: Rotten Test Forces Wrong Implementation

Trigger condition: a test fails after a legitimate refactor because it asserts an
implementation detail.

The lie: the implementation regressed.

The truth: the test's contract is wrong.

Detection: instructions explicitly allow and require fixing the test when the
test is bound to the wrong contract.

### Death Case 4: Reviewer Gate Is Not Invoked

Trigger condition: reviewer agents mention test quality, but
`skills/implement/dispatch-template.md` does not ask reviewers to inspect tests.

The lie: the review system covers brittle tests.

The truth: review dispatch may never activate the gate.

Detection: evaluator verifies dispatch prompts include test-quality review
questions for both reviewers.

### Death Case 5: Planning Provides No Contract Source

Trigger condition: a task asks for unit tests but does not name the observable
contract the unit tests may assert.

The lie: the implementer can infer the right contract from the task.

The truth: the implementer may infer the contract from current implementation
shape.

Detection: evaluator verifies `skills/planning/task-format.md` includes a
`Unit Test Contract` section.

### Death Case 6: Protocol Documented But Behavior Unchanged

Trigger condition: every instruction surface contains the protocol, but an agent
running a real implement task still writes brittle or vague unit tests.

The lie: the protocol is on every surface, so the feature is done.

The truth: source inspection proves presence, not behavior change.
Documentation present != behavior changed. The Goal is a behavioral claim that
the static evaluator cannot verify.

Detection: this gap is recorded as an accepted gap in `acceptance.yaml`, and
task-6 recommends a representative live implement run as the behavioral check.
The feature must not be declared behaviorally verified on source inspection
alone.

### Death Case 7: The Evaluator Refutes Its Own Thesis

Trigger condition: the focused evaluator asserts exact heading strings or prose,
or five separate per-task evaluators each hard-code their own phrase list.

The lie: the evaluator guards the protocol.

The truth: an evaluator that pins headings/prose is itself an over-fit test — it
falsely fails on an honest rename and proves the feature wrong on contact.
Divergent phrase lists are duplicated incidental constants, the exact
brittleness this feature forbids.

Detection: evaluators assert intent-bearing concept tokens that survive any
honest rewrite (e.g. both "behavior-preserving refactor" and "behavior actually
broke", and "fix the test"), and all import the single shared token source in
task-1. `references/test-contract.md` and its evaluator are the worked exemplar
of the principle (tokens = contract; headings = incidental).

### Death Case 8: Evaluator Enforces Section on Historical Tasks

Trigger condition: 64 of 70 existing task files predate the Unit Test Contract
section; the evaluator or format validation checks for it across all task files.

The lie: enforcing the required section is harmless.

The truth: a global check bricks the suite on pre-existing artifacts.

Detection: enforcement targets `skills/planning/task-format.md` (the template)
and newly generated tasks only — never retroactively across `changes/`.

### Death Case 9: Perfunctory Contract Label Satisfies the Gate

Trigger condition: an implementer adds a generic label such as
"# contract: it works" to pass the gate.

The lie: the test now names its contract.

The truth: a slogan is the Clean Scar anti-pattern — it ticks the box without
binding to anything observable.

Detection: the reviewer challenges perfunctory or tautological contract
declarations (mirroring scar-report.md's Clean Scar challenge); a named contract
must map to observable behavior, public API/schema, artifact shape, or
death/bug case.

## Implementation Plan

### Task 1: Add Test Contract Reference

Create `references/test-contract.md` with the canonical protocol:

- Contract Gate question.
- Brittleness filter.
- Silent-green / tautology guard.
- Unit-vs-death distinction.
- Snapshot/golden test rules.
- Minimum-contract / property assertions for multi-path workflows.
- Boundary-spy exception for interactions that are the feature.
- DAMP-over-DRY note for tests.
- Guidance to centralize incidental constants rather than pinning scattered
  fixture values.
- Define `tests/test_contract_bound_tests/_contract_tokens.py` as the single
  shared source of canonical concept tokens that tasks 2-6 import.
- State explicitly that `references/test-contract.md` and its evaluator are the
  worked exemplar of the protocol: the evaluator asserts concept tokens, never
  exact headings/prose.

### Task 2: Update Implementer Agent

Modify `agents/implementer.md`:

- Restore STEP 0 Q4. Canonical bootstrap wording is confirmed:
  "目前做的事情在未來是否還活著？" (with its explanatory sentence). The implementer
  agent currently lists three of the bootstrap's four questions.
- Change "answer these three questions" to four.
- Clarify death tests pin exact silent failure modes because those modes are the
  contract.
- Change unit-test step to require contract-bound unit tests.
- Amend the execution-order line itself (currently "Implement minimal code to
  pass all tests") to carry the fix-the-test caveat — e.g. "...unless a test
  asserts the wrong contract, in which case fix the test." Do not leave the
  caveat only as a separate note; the contradiction must not survive in the
  canonical order.
- Add self-review checks for both poles.
- Update report format so test contract notes are visible.

### Task 3: Update Implement Orchestration

Modify `skills/implement/SKILL.md`:

- Add a lean Test Contract Gate in per-task execution order.
- Add `references/test-contract.md` to Support Files.
- Add Yin-side constraint for contract-bound unit tests.
- Add red flags for over-fit and silent-green unit tests.
- Ensure the auto-mode gatekeeper name remains consistent with the existing
  contract if this file is touched near auto-mode wording.

### Task 4: Add Reviewer Enforcement

Modify:

- `agents/code-reviewer.md`
- `agents/code-quality-reviewer.md`
- `skills/implement/dispatch-template.md`

Code reviewer:

- Review tests before implementation correctness.
- Treat brittle or tautological tests as silent rot paths.
- Require contract source and both-poles check.
- Challenge perfunctory or tautological contract declarations (a slogan like
  "# contract: it works" is the Clean Scar anti-pattern); the named contract
  must map to an observable behavior, API/schema, artifact, or death/bug case.
- Permit "fix the test" when the test is wrong.

Code-quality reviewer:

- Check structural test coupling, duplicated incidental constants, snapshots
  without stabilization, and helpers that obscure the contract.
- Refer correctness/silent-rot concerns to code reviewer with file:line evidence.

Dispatch template:

- Add explicit test-quality instructions to both reviewer prompts.
- Require changed tests, test contract source, and diff context.

### Task 5: Add Planning Contract Origin

Modify:

- `skills/planning/task-format.md`
- optionally `skills/planning/SKILL.md`

Add a required `Unit Test Contract` section to the task format. Each task should
name what unit tests may assert, using observable contract sources rather than
implementation details.

Scope constraint (hard): enforce the section on `skills/planning/task-format.md`
(the template) and newly generated tasks only. Do NOT enforce it retroactively
across `changes/` — 64 of 70 existing task files predate the section, and a
global check would brick the suite. The evaluator inspects the template and
format validation, not historical task artifacts.

### Task 6: Add Evaluator Coverage and Validate

Add focused tests, likely under `tests/test_contract_bound_tests/`, to inspect
the instruction artifacts and fail if any required surface omits the protocol.

- Assert intent-bearing concept tokens imported from
  `tests/test_contract_bound_tests/_contract_tokens.py`, never exact headings or
  prose. The evaluator must survive an honest rename/rephrase of any instruction
  surface — if it would fail on a heading rename, it is itself over-fit.
- Scope: inspect the instruction surfaces and `skills/planning/task-format.md`.
  Do not assert the Unit Test Contract section on historical task files under
  `changes/`.
- Behavioral validation (recommended, addresses the accepted gap): run one
  representative live implement task and confirm the unit tests it produces are
  contract-bound. Source inspection proves the protocol is present; only a live
  run proves behavior changed. If the live run is skipped this iteration, leave
  the accepted gap visible in the scar report rather than claiming behavioral
  verification.

Run:

```bash
source .venv/bin/activate && uv run pytest tests/test_contract_bound_tests
source .venv/bin/activate && uv run pytest tests/test_auto_mode
source .venv/bin/activate && uv run pytest tests/integration/test_format_validation.py
source .venv/bin/activate && uv run pre-commit run --all-files
```

## Acceptance Mapping

- Brittle test passes review: Tasks 1, 2, 3, 4, 6.
- Silent-green test passes review: Tasks 1, 2, 3, 4, 6.
- Rotten test forces wrong implementation: Tasks 1, 2, 4, 6.
- Reviewer gate not invoked: Tasks 4, 6.
- Planning provides no contract source: Tasks 5, 6.
- Happy path contract-bound workflow exists: Tasks 1 through 6.
- Protocol documented but behavior unchanged: Task 6 (behavioral validation +
  accepted gap).
- Evaluator refutes its own thesis: Tasks 1, 6 (shared concept-token source).
- Evaluator enforces section on historical tasks: Tasks 5, 6 (template-only
  scope).
- Perfunctory contract label satisfies the gate: Task 4 (reviewer Clean Scar
  challenge).

## Resolved Decisions

- STEP 0 Q4 is included in this feature. Canonical bootstrap wording confirmed
  ("目前做的事情在未來是否還活著？"); the implementer agent is out of sync at three
  of four questions, so this is a same-feature drift fix, not a separate cleanup.
- The behavioral claim (agents write contract-bound tests) is NOT verified by
  static inspection. Task-6 recommends a representative live implement run as the
  behavioral check; if skipped, the residual is recorded as an accepted gap
  (`acceptance.yaml`) and left visible in the scar report rather than claimed.

## Open Questions

- Should brittle tests be represented in scar reports with a new schema field?
  Current plan uses existing `silent_failure_conditions` with no schema change.
