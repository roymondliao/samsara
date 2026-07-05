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

## Unit Test Contract
<!-- Name the OBSERVABLE contract a unit test may assert — NOT "write appropriate tests". -->
<!-- The contract source must be observable: public API/return value, documented artifact
     shape, emitted output, or a source named in references/test-contract.md. This is
     named UPSTREAM here so the implementer asserts it, instead of inferring a contract
     from the current implementation (which produces over-fit, brittle tests). -->
- Contract source: <observable behaviour / public API / artifact shape — name it>
- A unit test must assert this named contract source, not implementation details.

## Structure Refs
<!-- Required, even when empty. List the structure-spec.yaml module/pattern/
     dependency_rule ids this task touches. An empty array confirms the task
     was checked against structure-spec.yaml and touches no structural
     boundary — that is a different fact from the section being MISSING,
     which means the task was never checked (a schema violation). -->
- structure_refs: [<spec-entry-id>, ...]  <!-- or [] to confirm no structural touch -->

## Implementation Steps
- [ ] Step 1: Write death tests
- [ ] Step 2: Run death tests — verify they fail
- [ ] Step 3: Write unit tests asserting the named Unit Test Contract source (the contract gate: a unit test binds to the observable contract above, not implementation details)
- [ ] Step 4: Run unit tests — verify they fail
- [ ] Step 5: Implement minimal code to pass all tests
- [ ] Step 6: Run all tests — verify they pass
- [ ] Step 7: Write scar report
- [ ] Step 8: Report back (do not commit)

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
4. **Unit Test Contract names an observable contract source** — not "appropriate tests." The Unit Test Contract section must name an observable contract source (public API/return value, documented artifact shape, emitted output, or a source from `references/test-contract.md`). Generic "write appropriate tests" / "appropriate unit tests" wording names no contract and is forbidden — a unit test must assert the named observable contract source, not implementation details.
5. **Expected scar items** — helps the agent know what to watch for during implementation.
6. **Structure Refs is mandatory, even when empty** — 欄位缺失與空陣列必須可區分：`structure_refs: []`（空陣列）代表任務已對照 `structure-spec.yaml` 確認無結構觸及；`## Structure Refs` 整段**欄位缺失**（漏標）則是 schema violation. Enforcement is owned by implement's dispatch check (a missing section blocks dispatch); a present-but-empty array is a valid, confirmed absence.
