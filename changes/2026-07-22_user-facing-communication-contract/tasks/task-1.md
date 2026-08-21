# Task 1: Define the canonical presentation contract

**Task ID:** task-1

## Goal

Bootstrap gives every user-facing response a request-shaped, result-first opening
and evidence-preserving progressive disclosure without creating stage-specific
presentation authorities.

## Source References

- Planning: PL-D1 (bootstrap-presentation-authority)
- Design: PT-D1 (progressive disclosure), PT-D2 (request-shaped opening), PT-D3 (evidence-conditioned detail), PT-D4 (dual-reader identifiers), PT-S1 (artifact-to-response), PT-S2 (result-to-detail)
- Acceptance: AC-1 (request-shaped-opening), AC-2 (evidence-preserved-without-repetition), AC-3 (human-readable-machine-reference), AC-4 (safety-survives-brevity)
- Seam: artifact-to-response

## Context Projection

Read the complete Overview before writing. Treat the external communication
repository as a reference, not an authority or runtime dependency.

## Files

- Modify: `skills/samsara-bootstrap/SKILL.md`

## Constraints

- Keep the first paragraph standalone.
- Preserve applicable changed-file, verification, blocker, uncertainty, and unresolved-risk evidence.
- Do not add fixed word counts, hard list caps, mandatory estimates, or forced next actions.
- Do not copy the contract into stage skills, agents, schemas, or philosophy documents.
- Keep full lifecycle reasoning in its owning artifact.

## Death Test Requirements

- A completion response cannot hide unresolved decision-changing exposure to appear concise.
- A user-visible machine ID without a semantic label is invalid.
- A complete result does not receive a filler next action.
- A destructive action still requires confirmation.

## Unit Test Contract — required observable contract source

- Contract source: `skills/samsara-bootstrap/SKILL.md#user-facing-communication-contract`.

## Assumptions to Verify

- Bootstrap remains the only session-wide presentation owner — source: skill routing architecture — if false: identify the true injected authority before adding another rule.
