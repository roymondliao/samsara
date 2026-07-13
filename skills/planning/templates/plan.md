# Plan: <feature-name>

Planning judgment owner. Upstream design authority remains in `pre-thinking.md`.

## Source Contract

- Research: `1-kickoff.md`, `problem-autopsy.md`
- Design authority: `pre-thinking.md`
- Commitment: <Proceed | Accept gap>
- Accepted gaps: <refs and consequences | none>
- Evaluation: PT-EVAL (evaluation-contract)

## Planning Decisions

### PL-D1: <canonical planning label>

Source refs:
- PT-D1 (<canonical decision label>)
- PT-S1 (<canonical seam name>)
- <file:line when needed>

- Decision: <task boundary, file allocation, ordering, or acceptance mapping>
- Rationale: <why the sources force this Planning judgment>
- Consequence: <what downstream artifacts must do>
- If wrong: <what breaks and how it becomes visible>

## File Allocation

- `<path>` — owner: <task-id> — source refs: PL-D1 (<canonical planning label>), PT-D1 (<canonical decision label>)

## Acceptance Mapping

- AC-1 (<canonical scenario label>) → <task-id list> — planning ref: PL-D1 (<canonical planning label>)

## Task Decomposition

- `<task-id>` — boundary: <one responsibility> — refs: PL-D1 (<canonical planning label>), PT-D1 (<canonical decision label>)

## Planning Assumptions

- <assumption> — evidence: <source | missing input> — consequence if false: <...>

## File Allocation Consistency

- PT-D1 (<canonical decision label>) — <matches | contradicts | out of scope> — <evidence>
