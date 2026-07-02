# Overview: placement-consistency-gate (A4 / ISSUE-001)

## Goal
Stop a plan from silently contradicting its own placement/ownership decisions — via a planning self-check (cheap first pass) and an independent code-reviewer placement dimension fed the plan's Key Decisions (the reliable backstop).

## Architecture
Two independent gates (defense-in-depth), scoped to placement/ownership decisions only. Gate 1 (planning): a hard-STOP File-Map↔Key-Decisions consistency step + anti-bias prompt — same agent, weaker, catches the obvious early. Gate 2 (review): the yin `code-reviewer`, a fresh agent without the planner's path-of-least-resistance bias, receives the plan's Key Decisions and judges placement — independence IS the anti-bias mechanism. The load-bearing piece is the **data flow**: Key Decisions must actually reach the reviewer dispatch in implement and iteration, or Gate 2 checks against nothing.

## Tech Stack
Markdown skill/agent docs (planning SKILL, code-reviewer agent, implement dispatch-template, iteration SKILL), pytest doc-contract tests (`tests/test_skills/`).

## Key Decisions
<!-- These ARE placement/ownership decisions — exactly what this feature checks. -->
- **KD1: Gate 2 lives in the yin `code-reviewer`, NOT `code-quality-reviewer`.** Placement = plan-compliance, the yin reviewer's scope; quality reviewer is unchanged.
- **KD2: No structured ownership field; `templates/overview.md` unchanged.** Independence of the reviewer is the anti-bias mechanism, not a parseable field (pure judgment).
- **KD3: Data flow reaches implement + iteration only; fast-track excluded.** Fast-track's small changes are not the placement-contradiction failure mode.
- **KD4: This is a framework change — all edits live in the framework's own files** (`skills/`, `agents/`, `tests/`), not under any plugin-specific subtree. (Self-consistency: the File Map below matches this.)

## Death Cases Summary
1. **Corruption signature (DC-1):** code-reviewer gains the placement dimension but the dispatch never passes Key Decisions → checks nothing, silently passes. Guarded by the data-flow test (the Primary-evaluator core).
2. **Soft check (DC-2):** planning consistency step is advisory not STOP → contradictions pass.
3. **Iteration forgotten (DC-5):** only implement dispatch carries Key Decisions → iteration fixes reviewed blind to placement.

## File Map
<!-- File Map Consistency Check (self-applied — this feature's own gate, dogfooded):
     every path below matches KD4 (framework files, not plugin-specific). No contradiction. -->
- `skills/planning/SKILL.md` — Gate 1: consistency-check STOP step + anti-bias prompt (KD1-adjacent: planning side) [Task 1]
- `agents/code-reviewer.md` — Gate 2: architectural-placement dimension (KD1) [Task 2]
- `skills/implement/dispatch-template.md` + `skills/implement/SKILL.md` — data flow: Key Decisions into yin-reviewer dispatch (KD3) [Task 2]
- `skills/iteration/SKILL.md` — data flow: Key Decisions into per-fix yin-reviewer dispatch (KD3) [Task 2]
- `tests/test_skills/test_planning_placement_check.py` (new) — Task 1 doc-contract test [Task 1]
- `tests/test_skills/test_placement_review_dataflow.py` (new) — Task 2 doc-contract test (placement dimension + data flow in both dispatch paths) [Task 2]

Consistency note: `templates/overview.md` and `code-quality-reviewer` are intentionally NOT in the File Map (KD2 / KD1) — their absence is a decision, not an omission.
