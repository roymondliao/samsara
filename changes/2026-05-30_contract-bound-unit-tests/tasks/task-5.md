# Task 5: Add planning task contract origin

## Context

Read: `changes/2026-05-30_contract-bound-unit-tests/overview.md`

Contract-bound tests work best when the contract is named upstream. Task files
should give implementers a `Unit Test Contract` section instead of forcing them
to infer contract from current implementation.

## Files

- Modify: `skills/planning/task-format.md`
- Modify: `skills/planning/SKILL.md`
- Create: `tests/test_contract_bound_tests/test_planning_test_contract.py`

## Unit Test Contract

The evaluator imports concept tokens from `_contract_tokens.py` (task-1) and may
assert that `skills/planning/task-format.md` (the template) requires a `Unit Test
Contract` section and that planning decomposition mentions unit-test contract
source alongside death test requirements.

Scope (hard): the evaluator inspects the template only. It must NOT enforce the
section on historical task files under `changes/` — 64 of 70 existing task files
predate it, and a global check would brick the suite.

## Death Test Requirements

- Test: task format must fail if it has death test requirements but no unit-test
  contract section.
- Test: planning skill must fail if task decomposition does not mention
  unit-test contract source.
- Test: task format must fail if the unit-test section allows generic
  "appropriate tests" wording without observable contract sources.
- Test: the evaluator must fail if it asserts the `Unit Test Contract` section on
  historical task files instead of the template — enforcing it globally across
  `changes/` would brick the suite on pre-existing artifacts.

## Implementation Steps

- [ ] Step 1: Write evaluator tests for planning task contract origin.
- [ ] Step 2: Run tests with `source .venv/bin/activate` and `uv run pytest tests/test_contract_bound_tests/test_planning_test_contract.py` - verify they fail.
- [ ] Step 3: Update `skills/planning/task-format.md` with a required `Unit Test Contract` section, and add a Rule that the section must name observable contract sources (not "appropriate tests"). The template's Implementation Steps "Write unit tests" line should reference the contract gate.
- [ ] Step 4: Update `skills/planning/SKILL.md` task decomposition wording if needed.
- [ ] Step 5: Run the task test set - verify all pass.
- [ ] Step 6: Write scar report at `changes/2026-05-30_contract-bound-unit-tests/scar-reports/task-5-scar.yaml`.
- [ ] Step 7: Do not commit from the subagent; report back to the main agent.

## Expected Scar Report Items

- Potential shortcut: adding a heading without requiring observable contract
  sources.
- Potential shortcut: making planning too verbose by embedding the full testing
  catalog in every task.
- Assumption to verify: existing task files do not need migration for this
  feature unless tests enforce historical artifacts.

## Acceptance Criteria

- Covers: "Silent failure - planning leaves unit-test contract implicit"
- Covers: "Success - contract-bound unit-test workflow exists end to end"
