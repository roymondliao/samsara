# Plan: user-facing-communication-contract

Planning judgment owner. Upstream design authority remains in `pre-thinking.md`.

## Source Contract

- Research: `1-kickoff.md`, `problem-autopsy.md`
- Design authority: `pre-thinking.md`
- Commitment: Proceed
- Accepted gaps: Cross-model scoring remains future evidence.
- Evaluation: PT-EVAL (evaluation-contract)

## Planning Decisions

### PL-D1: bootstrap-presentation-authority

Source refs:
- PT-D1 (progressive disclosure)
- PT-D2 (request-shaped opening)
- PT-D3 (evidence-conditioned detail)
- PT-D4 (dual-reader identifiers)
- PT-S1 (artifact-to-response)
- `skills/samsara-bootstrap/SKILL.md`

- Decision: Bootstrap alone owns the user-facing communication contract and states the response shapes, detail order, identifier rule, and safety floor.
- Rationale: A session-wide behavior needs one injected authority; stage skills keep ownership of their artifacts and payloads.
- Consequence: Every workflow stage receives the same presentation rule without maintaining parallel copies.
- If wrong: Stage-specific needs may require a narrow projection, but Bootstrap remains the canonical source.

### PL-D2: semantic-contract-evaluation

Source refs:
- PT-EVAL (evaluation-contract)
- PT-D1 (progressive disclosure)
- PT-D3 (evidence-conditioned detail)
- PT-D4 (dual-reader identifiers)
- PT-S2 (result-to-detail)

- Decision: Guard load-bearing semantics and live Codex conversion, then record before/after behavior for five representative request shapes.
- Rationale: Exact prose assertions would make harmless wording edits expensive; semantic assertions protect behavior instead.
- Consequence: Contract loss, competing authority, bare IDs, and arbitrary brevity fail mechanically.
- If wrong: Tests can preserve words without improving model output, so the evaluation record remains explicit evidence rather than a success claim.

## File Allocation

- `skills/samsara-bootstrap/SKILL.md` — owner: task-1 — source refs: PL-D1 (bootstrap-presentation-authority)
- `tests/test_skills/test_bootstrap_communication_contract.py` — owner: task-2 — source refs: PL-D2 (semantic-contract-evaluation), PT-EVAL (evaluation-contract)
- `changes/2026-07-22_user-facing-communication-contract/evaluation-result.md` — owner: task-2 — source refs: PL-D2 (semantic-contract-evaluation), PT-S2 (result-to-detail)

## Acceptance Mapping

- AC-1 (request-shaped-opening) → task-1 — planning ref: PL-D1 (bootstrap-presentation-authority)
- AC-2 (evidence-preserved-without-repetition) → task-1, task-2 — planning refs: PL-D1 (bootstrap-presentation-authority), PL-D2 (semantic-contract-evaluation)
- AC-3 (human-readable-machine-reference) → task-1, task-2 — planning refs: PL-D1 (bootstrap-presentation-authority), PL-D2 (semantic-contract-evaluation)
- AC-4 (safety-survives-brevity) → task-1, task-2 — planning refs: PL-D1 (bootstrap-presentation-authority), PL-D2 (semantic-contract-evaluation)
- AC-5 (codex-conversion-preserves-contract) → task-2 — planning ref: PL-D2 (semantic-contract-evaluation)

## Task Decomposition

- `task-1` — boundary: canonical Bootstrap presentation rules — refs: PL-D1 (bootstrap-presentation-authority), PT-S1 (artifact-to-response)
- `task-2` — boundary: semantic guards and representative evaluation — refs: PL-D2 (semantic-contract-evaluation), PT-EVAL (evaluation-contract)

## Planning Assumptions

- Bootstrap content is preserved by the live Codex converter — evidence: `ConversionEngine("codex")` — consequence if false: task-2 must fix conversion before calling the contract shipped.
- User-facing machine references occur in prose rather than canonical YAML fields — evidence: existing dual-key artifact design — consequence if false: keep machine YAML canonical and apply labels only in prose projection.

## File Allocation Consistency

- PT-D1 (progressive disclosure) — matches — task-1 owns the canonical sequence.
- PT-D2 (request-shaped opening) — matches — task-1 owns request classification output.
- PT-D3 (evidence-conditioned detail) — matches — task-1 defines content; task-2 guards it.
- PT-D4 (dual-reader identifiers) — matches — task-1 defines the prose rule; task-2 rejects bare-ID semantics.
