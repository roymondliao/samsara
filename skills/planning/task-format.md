# Self-Contained Task Format

Each task must be independently executable by an agent with zero prior context.

## Required Sections

```markdown
# Task N: <title>

## Context
<!-- What does the agent need to know? Reference overview.md for architecture. -->
Read: overview.md

## Files
- Create: `exact/path/to/file`
- Modify: `exact/path/to/existing:line-range`
- Test: `tests/exact/path/to/test`

## Death Test Requirements
<!-- What death tests must be written BEFORE implementation? -->
- Test: <silent failure scenario>
- Test: <unknown outcome scenario>

## Implementation Steps
- [ ] Step 1: Write death tests
- [ ] Step 2: Run death tests — verify they fail
- [ ] Step 3: Write unit tests
- [ ] Step 4: Run unit tests — verify they fail
- [ ] Step 5: Implement minimal code to pass all tests
- [ ] Step 6: Run all tests — verify they pass
- [ ] Step 7: Write scar report
- [ ] Step 8: Commit

## Expected Scar Report Items
<!-- What shortcuts or assumptions should the agent watch for? -->
- Potential shortcut: <description>
- Assumption to verify: <description>

## Acceptance Criteria
<!-- From acceptance.yaml — which scenarios does this task cover? -->
- Covers: <scenario name>
```

## Rules

1. **No references to other tasks** — each task is self-contained. If task-3 needs context from task-1, include that context directly.
2. **Exact file paths** — no "create appropriate file" or "add to the right place."
3. **Death tests listed explicitly** — not "add appropriate death tests."
4. **Expected scar items** — helps the agent know what to watch for during implementation.
