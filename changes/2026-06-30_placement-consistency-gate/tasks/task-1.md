# Task 1: Planning-side gate — File-Map↔Key-Decisions STOP consistency check + anti-bias prompt

## Context
Read: overview.md

ISSUE-001: a plan can decide a placement/ownership fact in `Key Decisions` (e.g. "shared, not samsara-exclusive") and then contradict it in the `File Map` paths, with no check between the two independent sections. This task adds Gate 1 (the planning-side cheap first pass) to `skills/planning/SKILL.md`: a consistency-check step that STOPs on a genuine contradiction, plus an anti-bias prompt. Scoped to placement/ownership decisions only (not all Key Decisions — that fires on path-irrelevant decisions and becomes noise). Pure judgment, NO structured field, `templates/overview.md` unchanged.

## Files
- Modify: `skills/planning/SKILL.md` — add a **File Map Consistency Check** step (after the File Map is produced, before/at Task Decomposition) + an **anti-bias** line in the File-Map/Task-Decomposition area
- Create: `tests/test_skills/test_planning_placement_check.py`

## Death Test Requirements
- Test DC-2 (soft check): assert the consistency-check step uses STOP/blocking language (e.g. "stop" / "do not proceed to task decomposition" / "block"), NOT merely advisory ("consider"/"may").
- Test DC-3 (over-broad scope): assert the check is scoped to placement/ownership (the words "placement" and/or "ownership" appear in the step), and is NOT phrased as "every Key Decision must map to a path".
- Test DC-4 (anti-bias without gate): assert the consistency-check STOP step exists as a step distinct from the anti-bias prose — both must be present; the anti-bias line alone must not be the only addition.

## Unit Test Contract
- Contract source: the `skills/planning/SKILL.md` documented-artifact contract (the prescribed step's presence + enforcement + scope tokens). Assert behavioral tokens (consistency check, STOP, placement/ownership, derive-from-Key-Decisions), NOT exact prose.
- A test asserts the named tokens are present in the planning skill, not the file's byte layout.

## Implementation Steps
- [ ] Step 1: Read skills/planning/SKILL.md (Step 3 Task Decomposition + the overview/File Map references) to find the right insertion point
- [ ] Step 2: Write the doc-contract death tests (DC-2/3/4) in tests/test_skills/test_planning_placement_check.py — verify RED (clauses absent)
- [ ] Step 3: Add the File Map Consistency Check step (STOP on contradiction, scoped to placement/ownership) + the anti-bias line to skills/planning/SKILL.md
- [ ] Step 4: Run the tests — verify GREEN; run full suite — no regression
- [ ] Step 5: Write scar report
- [ ] Step 6: Report back (do not commit)

## Expected Scar Report Items
- Known shortcut: doc-presence test guards that the STOP step is WRITTEN and scoped, not that the planning agent actually STOPs at runtime (live-session limitation — defer to validate-and-ship dogfood).
- Assumption to verify: the chosen insertion point in planning SKILL.md is the spot where File Map exists and Task Decomposition has not yet happened (so STOP actually prevents decomposition).

## Acceptance Criteria
- Covers: "Degradation - soft/advisory check (DC-2)", "Degradation - over-broad scope (DC-3)", "Silent failure - anti-bias without STOP gate (DC-4)", "Success - both gates present" (planning half), "Success - non-placement decisions out of scope" (planning half)
