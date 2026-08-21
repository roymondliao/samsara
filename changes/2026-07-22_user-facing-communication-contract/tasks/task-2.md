# Task 2: Guard and evaluate communication behavior

**Task ID:** task-2

## Goal

Semantic tests detect contract drift and Codex conversion loss, while a compact
evaluation record shows how representative responses change before and after.

## Source References

- Planning: PL-D2 (semantic-contract-evaluation)
- Design: PT-D1 (progressive disclosure), PT-D3 (evidence-conditioned detail), PT-D4 (dual-reader identifiers), PT-EVAL (evaluation-contract), PT-S1 (artifact-to-response), PT-S2 (result-to-detail)
- Acceptance: AC-2 (evidence-preserved-without-repetition), AC-3 (human-readable-machine-reference), AC-4 (safety-survives-brevity), AC-5 (codex-conversion-preserves-contract)
- Seam: result-to-detail

## Context Projection

Read the complete Overview. Guard meaning and ownership; do not assert exact
paragraph counts, exact wording, or other presentational details that can change
without changing behavior.

## Files

- Create: `tests/test_skills/test_bootstrap_communication_contract.py`
- Create: `changes/2026-07-22_user-facing-communication-contract/evaluation-result.md`

## Constraints

- Prove Bootstrap is the sole authority.
- Exercise the live Codex conversion path.
- Evaluate command/status, explanation/review, completion, blocked/unknown, and destructive-action shapes.
- Distinguish observed test evidence from qualitative design review.

## Death Test Requirements

- Removing progressive disclosure, a request shape, applicable evidence, or the semantic-label rule fails a guard.
- Adding a competing heading under another skill or agent fails a guard.
- Adding a fixed word cap, hard list cap, or unsupported estimate requirement fails a guard.

## Unit Test Contract — required observable contract source

- Contract source: Bootstrap communication section and converted Codex Bootstrap output.

## Assumptions to Verify

- ConversionEngine writes the Bootstrap skill under the installed Codex skill tree — source: converter integration tests — if false: update the test to the canonical converted location rather than weakening the assertion.
