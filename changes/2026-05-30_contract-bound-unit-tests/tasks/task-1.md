# Task 1: Add test contract reference

## Context

Read: `changes/2026-05-30_contract-bound-unit-tests/overview.md`

Samsara currently requires death tests before unit tests but does not define what
makes a unit test healthy. Add the canonical reference that defines
contract-bound unit tests and the traps this feature must prevent.

## Files

- Create: `references/test-contract.md`
- Create: `tests/test_contract_bound_tests/_contract_tokens.py`
- Create: `tests/test_contract_bound_tests/test_test_contract_reference.py`

## Unit Test Contract

`_contract_tokens.py` is the single shared source of canonical concept tokens for
this feature. Tasks 2-6 import from it; no later evaluator hard-codes its own
phrase list. This file IS the worked exemplar of the protocol: it expresses each
concept as an intent-bearing token that survives any honest rewrite, never as an
exact heading string.

The evaluator may assert that `references/test-contract.md` covers these
concepts — checked via the shared tokens, NOT by pinning exact heading text:

- Contract Gate (the two questions: behavior-preserving refactor / behavior
  actually broke)
- Brittleness Filter (over-fit pole)
- Silent-Green Guard (tautology pole)
- Snapshot and Golden Tests (normalize volatile fields first)
- Boundary Spy Exception (interaction is the feature)
- Minimum-Contract Workflow Assertions (multi-path, no single hard-coded path)
- Unit Tests vs Death Tests (death tests pin the failure mode as their contract)
- DAMP Over DRY

## Death Test Requirements

- Test: missing `references/test-contract.md` must fail because implementers
  would have no canonical test contract protocol.
- Test: missing over-fit or silent-green guard must fail because the reference
  would protect only one side of the failure.
- Test: missing unit-vs-death distinction must fail because death tests could be
  weakened by unit-test anti-overfit language.
- Test: the evaluator must assert concept tokens from `_contract_tokens.py`; a
  test that pins an exact heading string or sentence is itself over-fit and must
  not be how coverage is checked (renaming a heading must not break the test
  while the concept is preserved).

## Implementation Steps

- [ ] Step 1: Define `_contract_tokens.py` with the canonical concept tokens (intent-bearing phrases, not heading strings) that tasks 2-6 will import.
- [ ] Step 2: Write evaluator tests that import those tokens and assert the reference covers each concept.
- [ ] Step 3: Run tests with `source .venv/bin/activate` and `uv run pytest tests/test_contract_bound_tests/test_test_contract_reference.py` - verify they fail.
- [ ] Step 4: Create `references/test-contract.md`.
- [ ] Step 5: Include examples for normalize-then-snapshot, minimum-contract workflow assertions, and boundary-spy exceptions.
- [ ] Step 6: Run the task test set - verify all pass.
- [ ] Step 7: Write scar report at `changes/2026-05-30_contract-bound-unit-tests/scar-reports/task-1-scar.yaml`.
- [ ] Step 8: Do not commit from the subagent; report back to the main agent.

## Expected Scar Report Items

- Potential shortcut: reference only says "test behavior" without naming how to
  detect brittle and silent-green tests.
- Potential shortcut: snapshot rules ban snapshots entirely instead of allowing
  normalized contract snapshots.
- Assumption to verify: `references/` is the correct home for cross-role testing
  protocol rather than `skills/implement/`.

## Acceptance Criteria

- Covers: "Silent failure - brittle unit test passes review"
- Covers: "Silent failure - vague unit test stays green when behavior breaks"
- Covers: "Silent failure - evaluator pins headings or prose instead of contract concepts"
- Covers: "Degradation - snapshot or golden tests are needed"
- Covers: "Success - death tests keep exact failure-mode pinning"
