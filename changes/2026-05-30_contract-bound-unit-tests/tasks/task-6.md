# Task 6: Add evaluator coverage and run validation

## Context

Read: `changes/2026-05-30_contract-bound-unit-tests/overview.md`

After tasks 1-5, add or consolidate evaluator coverage so future edits cannot
remove the contract-bound unit-test protocol from any instruction surface.

## Files

- Modify/Create: `tests/test_contract_bound_tests/`
- Test: `tests/test_contract_bound_tests`
- Test: `tests/test_auto_mode`
- Test: `tests/integration/test_format_validation.py`

## Unit Test Contract

The evaluator asserts all required source files contain the protocol, checked via
the shared concept tokens in `_contract_tokens.py` — intent-bearing phrases that
survive an honest rewrite — not exact headings, line numbers, or incidental
prose. Scope is the instruction surfaces plus `skills/planning/task-format.md`,
never historical task files under `changes/`.

## Death Test Requirements

- Test: the evaluator must fail if any required instruction surface is omitted
  from the inspection list.
- Test: the evaluator must fail if the dispatch template lacks reviewer
  test-quality prompts.
- Test: the evaluator must fail (be flagged as self-refuting) if it pins exact
  line numbers, exact heading strings, or incidental prose instead of importing
  concept tokens from `_contract_tokens.py`.
- Test: the evaluator must fail if it asserts the Unit Test Contract section on
  historical task files rather than the template.

## Implementation Steps

- [ ] Step 1: Consolidate focused evaluator tests under `tests/test_contract_bound_tests/`.
- [ ] Step 2: Run `source .venv/bin/activate` and `uv run pytest tests/test_contract_bound_tests`.
- [ ] Step 3: Run `source .venv/bin/activate` and `uv run pytest tests/test_auto_mode`.
- [ ] Step 4: Run `source .venv/bin/activate` and `uv run pytest tests/integration/test_format_validation.py`.
- [ ] Step 5: Run `source .venv/bin/activate` and `uv run pre-commit run --all-files`.
- [ ] Step 6: Behavioral validation (recommended) — run one representative live implement task and confirm the unit tests it produces are contract-bound. If skipped this iteration, record it as an accepted gap in the scar report; do NOT claim behavioral verification on source inspection alone.
- [ ] Step 7: Write scar report at `changes/2026-05-30_contract-bound-unit-tests/scar-reports/task-6-scar.yaml`.
- [ ] Step 8: Do not commit from the subagent; report back to the main agent.

## Expected Scar Report Items

- Potential shortcut: evaluator only checks keywords and misses instruction
  surfaces.
- Potential shortcut: evaluator itself becomes brittle by pinning line numbers or
  incidental prose.
- Assumption to verify: source inspection is sufficient first validation before
  running a live representative implementation task.

## Acceptance Criteria

- Covers: "Silent failure - brittle unit test passes review"
- Covers: "Silent failure - vague unit test stays green when behavior breaks"
- Covers: "Silent failure - reviewer gate is documented but not dispatched"
- Covers: "Silent failure - planning leaves unit-test contract implicit"
- Covers: "Silent failure - protocol documented but agent behavior unchanged"
- Covers: "Silent failure - evaluator pins headings or prose instead of contract concepts"
- Covers: "Silent failure - evaluator enforces contract section on historical task files"
- Covers: "Success - contract-bound unit-test workflow exists end to end"
