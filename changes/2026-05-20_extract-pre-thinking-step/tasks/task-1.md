# Task 1: Write death tests

## Context

Read: `overview.md`

This is a samsara skill change — there is no test runner. "Death tests" here are behavioral verification scenarios: descriptions of what an agent should do (or must NOT do) when the skill exists. They are written as a checklist in `death-tests.md` and used to verify implementation in Tasks 2–6.

This task must complete before any implementation task begins.

## Files

- Create: `changes/2026-05-20_extract-pre-thinking-step/death-tests.md`

## Death Test Requirements

These ARE the output of this task. Write a verification scenario for each:

1. **K3b interrupted session** — agent reads `pre-thinking.md` with no `## Step C — Commitment` section; must detect and inform user, not proceed to planning
2. **Quick-pass: no gaps** — agent runs pre-thinking, finds no gaps; `pre-thinking.md` has `gaps: none identified` in Step A, NO Step B, Step C with `Decision: Proceed`; no questions asked
3. **Group overflow** — agent has 5 questions in one topic cluster; must split into two AskUserQuestion calls (3 + 2), never one call with 5
4. **Append-only enforcement** — agent performs Step B append; pre-existing Step A content and prior Step B groups must NOT be overwritten
5. **File-edit detection** — user edits `pre-thinking.md` between Step A and Step B; agent reads file before append, detects difference, prints acknowledgment, incorporates edits before appending
6. **Commitment via AskUserQuestion** — Step C commitment must come from AskUserQuestion call, not inferred from conversation text
7. **Return to Research path** — user selects Return to Research in Step B or Step C; agent writes Step C section with `Decision: Return to Research` and non-empty `unresolved_gaps` list; does NOT invoke `samsara:planning`

## Implementation Steps

- [ ] Step 1: For each of the 7 scenarios above, write a verification scenario block in `death-tests.md`
- [ ] Step 2: Each scenario block must include: scenario name, setup (precondition), action (what triggers it), expected agent behavior, failure signal (what "wrong" looks like)
- [ ] Step 3: Review all 7 scenarios against `acceptance.yaml` — confirm each maps to at least one acceptance scenario
- [ ] Step 4: Confirm that the failure signal for each test is observable (i.e., a human reviewer can tell pass from fail)
- [ ] Step 5: Write scar report

## Expected Scar Report Items

- Potential shortcut: writing scenarios too abstractly ("agent behaves correctly") without specifying what observable output proves correctness
- Potential shortcut: omitting the "failure signal" section (what wrong behavior looks like) — this is as important as the expected behavior
- Assumption to verify: all 7 scenarios map to at least one scenario in `acceptance.yaml`

## Acceptance Criteria

- Covers: all 7 death cases from `2-plan.md`
- Covers: all `type: death_path` and `type: degradation` scenarios from `acceptance.yaml`
