# Task 2: Review-side gate + data flow — code-reviewer placement dimension + Key Decisions into implement & iteration dispatch

## Context
Read: overview.md

Gate 2 — the reliable backstop. The yin `samsara:code-reviewer` (a fresh agent without the planner's bias) must judge whether file placement matches the plan's placement/ownership Key Decisions. Two parts, and the SECOND is the corruption-signature core: (a) add an Architectural Placement dimension to `agents/code-reviewer.md`; (b) the **data flow** — the yin code-reviewer dispatch must actually carry the plan's Key Decisions (curated from `overview.md`) in BOTH implement and iteration. A placement dimension WITHOUT the data flow is the corruption signature: the reviewer "checks placement" against nothing and silently passes.

Live facts (verified): the yin reviewer dispatch in `skills/implement/dispatch-template.md` currently passes only Task Requirements (acceptance) + Changed Files + Diff. `skills/iteration/SKILL.md` Step 3 dispatches both reviewers with `iteration_budget_context` + fix context, no Key Decisions. `code-reviewer.md` review order has 6 steps, none for placement. `code-quality-reviewer` is NOT changed.

## Files
- Modify: `agents/code-reviewer.md` — add an Architectural Placement review dimension (scoped to placement/ownership Key Decisions; mismatch = Important/Critical per Mother Rule 2). Document the three-state handling: matches / contradicts / not-a-placement-decision (out of scope, not a pass/fail).
- Modify: `skills/implement/dispatch-template.md` — add a "Plan Key Decisions" section to the yin code-reviewer dispatch template (curated from overview.md)
- Modify: `skills/implement/SKILL.md` — reference that the yin reviewer dispatch includes Key Decisions (keep consistent with dispatch-template)
- Modify: `skills/iteration/SKILL.md` — the per-fix yin code-reviewer dispatch includes the plan's Key Decisions
- Create: `tests/test_skills/test_placement_review_dataflow.py`

## Death Test Requirements
- Test DC-1 (corruption signature — the Primary-evaluator core): assert the plan's Key Decisions are referenced in the yin code-reviewer dispatch in BOTH `skills/implement/dispatch-template.md` AND `skills/iteration/SKILL.md`. If the placement dimension exists in code-reviewer.md but Key Decisions are absent from a dispatch path → FAIL.
- Test DC-5 (iteration forgotten): the assertion above must check BOTH paths independently — implement-only is a FAIL.
- Test (placement dimension present): assert `agents/code-reviewer.md` contains an Architectural Placement dimension referencing placement/ownership + Key Decisions.
- Test (three-state honesty): assert code-reviewer.md documents that a non-placement decision is out-of-scope (not forced to pass/fail).

## Unit Test Contract
- Contract source: the documented-artifact contract across `agents/code-reviewer.md`, `skills/implement/dispatch-template.md`, `skills/iteration/SKILL.md` — the presence of the placement dimension AND the Key-Decisions-in-dispatch data flow in BOTH paths. Assert behavioral tokens (architectural placement, key decisions, placement/ownership), NOT exact prose. The data-flow assertion (Key Decisions in both dispatch files) is the load-bearing one.

## Implementation Steps
- [ ] Step 1: Read agents/code-reviewer.md (review order), skills/implement/dispatch-template.md (yin reviewer section), skills/iteration/SKILL.md (Step 3 dispatch) for exact insertion points
- [ ] Step 2: Write the doc-contract death tests (DC-1 data flow in BOTH paths, DC-5, dimension present, three-state) in tests/test_skills/test_placement_review_dataflow.py — verify RED
- [ ] Step 3: Add the Architectural Placement dimension to code-reviewer.md (with three-state handling)
- [ ] Step 4: Add the "Plan Key Decisions" section to the yin reviewer dispatch in implement dispatch-template + reference in implement SKILL; add Key Decisions to the iteration per-fix yin dispatch
- [ ] Step 5: Run the tests — verify GREEN; run full suite — no regression
- [ ] Step 6: Write scar report
- [ ] Step 7: Report back (do not commit)

## Expected Scar Report Items
- Known shortcut: doc-presence test guards that Key Decisions are WIRED into the dispatch text, not that the reviewer at runtime actually judges placement correctly (live-session limitation — dogfood).
- Silent failure to watch: adding the placement dimension to code-reviewer.md but forgetting one dispatch path (the corruption signature) — the DC-1 test must check BOTH implement and iteration, or this task can silently ship a gate that checks nothing.
- Assumption to verify: the yin reviewer (not the quality reviewer) is the dispatch whose payload gains Key Decisions — do not add it to the code-quality-reviewer dispatch.

## Acceptance Criteria
- Covers: "Silent failure - corruption signature (DC-1)", "Unknown - iteration dispatch forgotten (DC-5)", "Success - both gates present and data flow live" (review half), "Success - non-placement decisions out of scope" (review half)
