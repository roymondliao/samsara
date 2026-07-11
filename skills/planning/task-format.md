# Task Work-Order Format

Artifact shape only. Implement owns execution procedure.

```markdown
# Task N: <title>

**Task ID:** <task-N>

## Goal

<One observable task outcome.>

## Source References

- Planning: <PL-D1, ...>
- Design: <PT-D1, PT-S1, ...>
- Acceptance: <AC-1, ...>
- Seam: <semantic-name | none>

## Context Projection

The dispatcher supplies the cited Overview projections and this task's anchors
from `index.yaml`. Read the live anchor files before writing; never treat an
Overview projection as decision authority.

## Files

- Create: `exact/path`
- Modify: `exact/path`
- Test: `tests/exact/path`

## Constraints

- <task-local consequence of a cited decision>

## Death Test Requirements

- <observable silent-failure or unknown-outcome contract>

## Unit Test Contract — required observable contract source

- Contract source: <public behavior, API, artifact shape, or emitted output>

## Assumptions to Verify

- <assumption> — source: <ref | missing input> — if false: <consequence>
```
