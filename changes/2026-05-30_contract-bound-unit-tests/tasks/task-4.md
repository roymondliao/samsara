# Task 4: Add reviewer enforcement and dispatch propagation

## Context

Read: `changes/2026-05-30_contract-bound-unit-tests/overview.md`

Reviewer enforcement must be real, not only documented. The code reviewer owns
silent-rot risk in tests. The code-quality reviewer owns structural coupling in
test design. The dispatch template must ask both reviewers to inspect tests.

## Files

- Modify: `agents/code-reviewer.md`
- Modify: `agents/code-quality-reviewer.md`
- Modify: `skills/implement/dispatch-template.md`
- Create: `tests/test_contract_bound_tests/test_reviewer_test_contract.py`

## Unit Test Contract

The evaluator imports concept tokens from `_contract_tokens.py` (task-1) and may
assert that:

- `agents/code-reviewer.md` reviews tests before implementation correctness,
  can flag brittle or tautological tests, and challenges perfunctory or
  tautological contract declarations (the Clean Scar anti-pattern: a slogan like
  "# contract: it works" does not satisfy the gate);
- `agents/code-quality-reviewer.md` reviews structural test coupling and refers
  silent-rot concerns to code reviewer;
- `skills/implement/dispatch-template.md` includes test-quality review prompts
  for both reviewers.

## Death Test Requirements

- Test: reviewer protocol must fail if code reviewer does not inspect tests
  before correctness.
- Test: reviewer protocol must fail if dispatch template omits test-quality
  instructions.
- Test: reviewer protocol must fail if code-quality reviewer has no structural
  test-coupling guidance.
- Test: reviewer protocol must fail if no reviewer can say "fix the test" when
  the test contract is wrong.
- Test: reviewer protocol must fail if the code reviewer cannot challenge a
  perfunctory contract label (Clean Scar), i.e. a named contract that maps to no
  observable behavior, API/schema, artifact, or death/bug case.

## Implementation Steps

- [ ] Step 1: Write evaluator tests for reviewer and dispatch protocol.
- [ ] Step 2: Run tests with `source .venv/bin/activate` and `uv run pytest tests/test_contract_bound_tests/test_reviewer_test_contract.py` - verify they fail.
- [ ] Step 3: Update `agents/code-reviewer.md`.
- [ ] Step 4: Update `agents/code-quality-reviewer.md`.
- [ ] Step 5: Update both reviewer prompts in `skills/implement/dispatch-template.md`.
- [ ] Step 6: Run the task test set - verify all pass.
- [ ] Step 7: Write scar report at `changes/2026-05-30_contract-bound-unit-tests/scar-reports/task-4-scar.yaml`.
- [ ] Step 8: Do not commit from the subagent; report back to the main agent.

## Expected Scar Report Items

- Potential shortcut: reviewer agent contains rules, but dispatch prompt never
  activates them.
- Potential shortcut: both reviewers duplicate the same responsibility instead
  of splitting yin silent-rot and structural coupling.
- Assumption to verify: code-reviewer can apply the test-contract reference
  without weakening its domain reference protocol.

## Acceptance Criteria

- Covers: "Silent failure - brittle unit test passes review"
- Covers: "Silent failure - vague unit test stays green when behavior breaks"
- Covers: "Silent failure - rotten test forces wrong implementation change"
- Covers: "Silent failure - reviewer gate is documented but not dispatched"
- Covers: "Silent failure - reviewer accepts a perfunctory contract label"
