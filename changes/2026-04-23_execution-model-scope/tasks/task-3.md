# Task 3: Refactor code-reviewer with reference file protocol + router

## Context

Read: overview.md

The `code-reviewer` agent (`agents/code-reviewer.md`) currently has all behavioral review patterns baked into its agent definition. This task:

1. **Extracts** domain-specific behavioral patterns into `references/code-review.md`
2. **Adds** a Reference File Protocol (same pattern as `code-quality-reviewer`)
3. **Adds** Step 0 router (same two-pass detection as Task 1)
4. **Adds** `## Applicability` section to the new reference file

### What stays in the agent definition

- **Three Mother Rules** (domain-agnostic judgment standard):
  1. Any structure must be able to articulate its death
  2. Any boundary must label its assumptions
  3. Any abstraction must make errors easier to see, not harder
- **Review procedure framework** (Step 1-5 order: Deletion Analysis → Naming Honesty → Silent Rot Paths → Scar Report Integrity → Correctness)
- **Step 4 (Scar Report Integrity)** — scar reports are samsara artifacts, domain-agnostic
- **Issue Classification** (Critical / Important / Suggestion definitions)
- **Output Format**
- **Constraints**
- **Reference File Protocol** (new — read domain reference before starting review)
- **Step 0: Router** (new — same two-pass detection as code-quality-reviewer)

### What gets extracted to references/code-review.md

- **Step 1 (Deletion Analysis)** patterns: dead code, uncalled functions, abstractions serving no current purpose
- **Step 2 (Naming Honesty)** patterns: `is_done` meaning more than done, `is_success` including uncertain outcomes, `handle_error` that swallows errors
- **Step 3 (Silent Rot Paths)** patterns: errors caught but not re-raised/logged, fallbacks without degraded state marking, default values turning unknown→known, retry without idempotency, timeout with silent continuation
- **Step 5 (Correctness)** patterns: logic errors, off-by-one, race conditions, security vulnerabilities

### Router specification

Same as Task 1's router. Reference file resolution: `samsara/references/{domain}-review.md`

Same three failure modes as Task 1 (UNKNOWN for unrecognized domain, UNKNOWN for missing reference file).

### Critical constraint: No regression

After this refactoring, the code-reviewer reviewing imperative code must produce **functionally equivalent output** to the pre-refactoring agent. The extraction must be complete — no patterns lost, no nuance dropped.

## Files

- Create: `references/code-review.md` — imperative code behavioral patterns (extracted from current agent)
- Modify: `agents/code-reviewer.md` — add Reference File Protocol, add Step 0 router, replace inline behavioral patterns with reference to `code-review.md`

## Death Test Requirements

- Test: code-reviewer with new reference file protocol reviews a Python file with known silent rot (try/except that swallows) → must identify the issue (same as before refactoring)
- Test: code-reviewer with new reference file protocol reviews a Python file with dishonest naming → must identify the issue (same as before refactoring)
- Test: code-reviewer receives `.tf` file → router selects domain `iac`. If `iac-review.md` doesn't exist yet → must return UNKNOWN, not fall back to `code-review.md`
- Test: code-reviewer receives unknown file type → must return UNKNOWN with clear message

## Implementation Steps

- [ ] Step 1: Snapshot current code-reviewer behavior — review a sample Python file and record output
- [ ] Step 2: Write death tests (regression tests based on snapshot + router failure modes)
- [ ] Step 3: Run death tests against current agent — regression tests should pass, router tests should fail
- [ ] Step 4: Create `references/code-review.md` — extract behavioral patterns from `agents/code-reviewer.md`
- [ ] Step 5: Add `## Applicability` section to `code-review.md` (domain: code, no excluded principles)
- [ ] Step 6: Refactor `agents/code-reviewer.md` — add Reference File Protocol, Step 0 router, replace inline patterns with reference
- [ ] Step 7: Run all death tests — verify they pass (regression + router)
- [ ] Step 8: Write scar report
- [ ] Step 9: Commit

## Expected Scar Report Items

- Potential shortcut: Extraction may simplify nuanced patterns. Original agent definition has inline context ("asked 'who calls this?'") that gives implicit guidance — extracted form may lose this contextual flow.
- Assumption to verify: The Three Mother Rules are truly domain-agnostic. For IaC, "structure" might mean "resource" or "module" — the rules still apply but interpretation differs. Verify that keeping them in the agent definition (not the reference) is correct.
- Assumption to verify: Scar Report Integrity (Step 4) staying domain-agnostic is correct. If IaC scar reports have different patterns, Step 4 may need domain-specific guidance in the future.

## Acceptance Criteria

- Covers: "Silent failure - code-review.md extraction loses behavioral patterns"
- Covers: "Success - imperative code review unchanged after refactoring"
