# Task 2: Update implementer agent test-writing protocol

## Context

Read: `changes/2026-05-30_contract-bound-unit-tests/overview.md`

The implementer agent is the highest-leverage file because it writes death tests
and unit tests. Its current execution order says only "Write unit tests", which
allows hard-coded or tautological tests.

## Files

- Modify: `agents/implementer.md`
- Create: `tests/test_contract_bound_tests/test_implementer_test_contract.py`

## Unit Test Contract

The evaluator imports concept tokens from
`tests/test_contract_bound_tests/_contract_tokens.py` (defined in task-1) and
may assert that `agents/implementer.md`:

- requires contract-bound unit tests;
- asks both-poles questions in self-review;
- allows fixing a rotten test when the test is bound to the wrong contract, and
  the execution-order line itself carries that caveat (not only a separate note);
- preserves the death-test distinction;
- lists four STEP 0 questions including the longevity question
  "目前做的事情在未來是否還活著？" (canonical bootstrap wording, confirmed).

## Death Test Requirements

- Test: implementer instructions must fail if they say only "Write unit tests"
  without contract binding.
- Test: implementer instructions must fail if they prevent brittle tests but do
  not prevent silent-green tests.
- Test: implementer instructions must fail if they imply all failing tests mean
  implementation is wrong.
- Test: implementer instructions must fail if death tests are weakened by the
  unit-test anti-overfit rule.

## Implementation Steps

- [ ] Step 1: Write evaluator tests for implementer contract-bound unit-test protocol.
- [ ] Step 2: Run tests with `source .venv/bin/activate` and `uv run pytest tests/test_contract_bound_tests/test_implementer_test_contract.py` - verify they fail.
- [ ] Step 3: Add STEP 0 Q4 "目前做的事情在未來是否還活著？" and change "answer these three questions" to four.
- [ ] Step 4: Update execution order — require contract-bound unit tests, and amend the "implement minimal code to pass all tests" line to add the fix-the-test caveat. Update self-review with both-poles checks.
- [ ] Step 5: Add report-format visibility for unit-test contract notes if needed.
- [ ] Step 6: Run the task test set - verify all pass.
- [ ] Step 7: Write scar report at `changes/2026-05-30_contract-bound-unit-tests/scar-reports/task-2-scar.yaml`.
- [ ] Step 8: Do not commit from the subagent; report back to the main agent.

## Expected Scar Report Items

- Potential shortcut: adding a slogan about behavior tests without a checkable
  contract source.
- Potential shortcut: treating every test failure as implementation failure.
- Assumption to verify: amending the STEP 0 question count in `implementer.md`
  does not desync any other consumer that counts on "three questions". (Q4
  inclusion itself is a resolved decision — see plan Resolved Decisions.)

## Acceptance Criteria

- Covers: "Silent failure - brittle unit test passes review"
- Covers: "Silent failure - vague unit test stays green when behavior breaks"
- Covers: "Silent failure - rotten test forces wrong implementation change"
- Covers: "Success - death tests keep exact failure-mode pinning"
