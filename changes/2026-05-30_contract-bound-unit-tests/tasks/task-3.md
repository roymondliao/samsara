# Task 3: Update implement orchestration gate

## Context

Read: `changes/2026-05-30_contract-bound-unit-tests/overview.md`

`skills/implement/SKILL.md` orchestrates implementer execution. It should stay
lean but must make the Test Contract Gate mandatory and point to the detailed
reference.

## Files

- Modify: `skills/implement/SKILL.md`
- Create: `tests/test_contract_bound_tests/test_implement_skill_test_contract.py`

## Unit Test Contract

The evaluator imports concept tokens from `_contract_tokens.py` (task-1) and may
assert that `skills/implement/SKILL.md`:

- names `references/test-contract.md` as a support file;
- requires a Test Contract Gate before unit tests;
- contains over-fit and silent-green red flags;
- states that unit tests assert contracts, not implementation details;
- preserves death-test-first ordering.

## Death Test Requirements

- Test: implement skill must fail if it references unit tests without the Test
  Contract Gate.
- Test: implement skill must fail if it prevents over-fit tests but omits
  silent-green tests.
- Test: implement skill must fail if it omits `references/test-contract.md` from
  support files.

## Implementation Steps

- [ ] Step 1: Write evaluator tests for implement skill protocol.
- [ ] Step 2: Run tests with `source .venv/bin/activate` and `uv run pytest tests/test_contract_bound_tests/test_implement_skill_test_contract.py` - verify they fail.
- [ ] Step 3: Update per-task execution order with the lean Test Contract Gate.
- [ ] Step 4: Add Yin-side constraints and red flags.
- [ ] Step 5: Add `references/test-contract.md` to Support Files.
- [ ] Step 6: Run the task test set - verify all pass.
- [ ] Step 7: Write scar report at `changes/2026-05-30_contract-bound-unit-tests/scar-reports/task-3-scar.yaml`.
- [ ] Step 8: Do not commit from the subagent; report back to the main agent.

## Expected Scar Report Items

- Potential shortcut: duplicating the whole catalog in the skill file instead
  of pointing to the reference.
- Potential shortcut: adding a gate that is not placed before unit test writing.
- Assumption to verify: touching implement skill near auto-mode wording does not
  introduce gatekeeper naming drift.

## Acceptance Criteria

- Covers: "Silent failure - brittle unit test passes review"
- Covers: "Silent failure - vague unit test stays green when behavior breaks"
- Covers: "Success - contract-bound unit-test workflow exists end to end"
