# Task Work-Order Format

Artifact shape only. Implement owns execution procedure.

```markdown
# Task N: <title>

**Task ID:** <task-N>

## Goal

<One observable task outcome.>

## Source References

- Planning: PL-D1 (<canonical planning label>)
- Design: PT-D1 (<canonical decision label>), PT-S1 (<canonical seam name>)
- Acceptance: AC-1 (<canonical scenario label>)
- Seam: <semantic-name | none>

## Context Projection

The dispatcher supplies the cited Overview projections and this task's anchors
from `index.yaml`. Read the live anchor files before writing; never treat an
Overview projection as decision authority.

## Files

- Create: `exact/path`
- Modify: `exact/path`
- Test: `tests/exact/path`

These paths are the declared write scope used to prove whether an Implement
parallel wave is safe. A required path outside this list is a scope change and
must return to orchestration before that file is modified.

## Constraints

- <task-local consequence of a cited decision>

## Death Test Requirements

- <observable silent-failure or unknown-outcome contract>

## Unit Test Contract — required observable contract source

- Contract source: <public behavior, API, artifact shape, or emitted output>

## Assumptions to Verify

- <assumption> — source: <ref | missing input> — if false: <consequence>
```
