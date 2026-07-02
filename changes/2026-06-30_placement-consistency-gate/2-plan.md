# Plan: placement-consistency-gate (A4 / ISSUE-001)

## Pre-thinking Commitments Consumed

- **Decision:** Proceed
- **Accepted gaps:** none
- **System design constraints:**
  - Scope = placement/ownership Key Decisions vs File Map paths only.
  - Two independent gates: planning self-check (#1, judgment, hard STOP) + yin `code-reviewer` architectural-placement dimension (#2, reliable backstop) + planning anti-bias prompt (#3).
  - Independence of the fresh reviewer is the anti-bias mechanism; NO structured ownership field; `templates/overview.md` unchanged; `code-quality-reviewer` unchanged.
  - Data flow: Key Decisions reach the **yin reviewer** dispatch in implement + iteration; fast-track excluded.
  - Every landed rule guarded by a doc-contract test; the data-flow test is the corruption-signature floor.
  - Acceptance bar = defense-in-depth: a contradicting plan stopped by at least one of the two gates.
- **Primary evaluator:** pytest doc-contract suite — (1) planning STOP consistency step, (2) code-reviewer placement dimension, (3) Key Decisions in BOTH implement + iteration yin-reviewer dispatch.
- **Pass / Fail signal:** all three green, esp. (3); fail if placement dimension exists but a dispatch doesn't carry Key Decisions.
- **Feedback loop:** if (3) red while (2) green, fix the dispatch data flow first.

## Step 2: Technical Specification

### Components

| Component | Change | Gate |
|---|---|---|
| `skills/planning/SKILL.md` | Add a **File Map Consistency Check** step (after File Map written, before/at Task Decomposition): for each File Map path, judge it against placement/ownership Key Decisions; on a genuine contradiction, **STOP** — do not proceed to task decomposition. Add an **anti-bias** line: derive paths from Key Decisions, do not default to existing infrastructure. | #1, #3 (planning self-check) |
| `agents/code-reviewer.md` | Add an **Architectural Placement** review dimension (scoped to placement/ownership Key Decisions): does each new/changed file's location match the plan's stated placement decision? Mismatch = Important/Critical (unlabeled contradiction, Mother Rule 2). | #2 (review backstop) |
| `skills/implement/dispatch-template.md` + `skills/implement/SKILL.md` | The yin `code-reviewer` dispatch payload includes a **Plan Key Decisions** section (curated from `overview.md`) so the reviewer has the placement decisions to check against. | data flow |
| `skills/iteration/SKILL.md` | The per-fix yin `code-reviewer` dispatch likewise includes the plan's Key Decisions. | data flow |

### I/O with Unknown Output — the placement-check verdict (three states)

The placement check (both planning self-check and reviewer) must classify each path/decision as exactly one of:
- `matches` — the path is consistent with a placement/ownership decision → ok
- `contradicts` — the path violates a placement/ownership decision → STOP (planning) / flag Important+ (review)
- `not-a-placement-decision` (unknown) — the Key Decision is not about placement, OR no placement decision constrains this path → **out of scope, do NOT treat as a pass or a fail.** Silently treating an unconstrained path as "matches" is acceptable (nothing to check); silently treating a real contradiction as "not-a-placement-decision" is the defect.

### Death Cases (not edge cases)

**DC-1 — corruption signature (the core).** Trigger: `code-reviewer.md` gains the placement dimension but the dispatch template never passes Key Decisions. Appears: review "checks placement" and passes. Truth: the reviewer had nothing to check against. Detect: data-flow test asserts Key Decisions appear in BOTH implement dispatch-template AND iteration reviewer dispatch.

**DC-2 — soft check.** Trigger: planning consistency step lands as advisory ("consider checking") not a hard STOP. Appears: a step exists. Truth: contradictions pass anyway. Detect: test asserts STOP/blocking language (e.g., "stop"/"do not proceed to task decomposition").

**DC-3 — over-broad scope (friction → ignored).** Trigger: the check is phrased as "every Key Decision must map to a path." Appears: thorough. Truth: fires on path-irrelevant decisions → noise → planning learns to skip it. Detect: test asserts the check is scoped to placement/ownership (the words "placement"/"ownership" present), not "all decisions."

**DC-4 — anti-bias without the gate.** Trigger: only #3 (anti-bias prose) lands, not #1 (the STOP check). Appears: planning mentions placement. Truth: no gate. Detect: test asserts the consistency STOP step specifically, separate from the anti-bias line.

**DC-5 — iteration forgotten.** Trigger: only implement dispatch gets Key Decisions; iteration fix-review doesn't. Appears: implement reviews check placement. Truth: iteration-phase fixes reviewed blind to placement. Detect: data-flow test checks BOTH implement AND iteration.

## Step 2.5: Acceptance Criteria

See `acceptance.yaml`. Order: silent-failure (DC-1 corruption signature, DC-4) → degradation (DC-2 soft check, DC-3 over-broad) → unknown (DC-5 iteration) → happy (both gates present + data flow live).

## Step 3: Task Decomposition

- **Task 1 — planning-side gate** (`skills/planning/SKILL.md`): consistency-check STOP step (#1) + anti-bias prompt (#3), scoped to placement/ownership. Owns DC-2, DC-3, DC-4. Depends on: none.
- **Task 2 — review-side gate + data flow** (`agents/code-reviewer.md` placement dimension #2 + Key Decisions in `skills/implement` dispatch-template/SKILL + `skills/iteration` dispatch). Owns DC-1 (corruption signature — the Primary-evaluator core), DC-5. Depends on: none (independent of Task 1; defense-in-depth).

Both are doc/agent-behavior changes guarded by doc-contract tests (`tests/test_skills/`). Runtime obedience (planning actually STOPs; reviewer actually catches a contradiction) is **out of scope** per the Evaluation Contract — deferred to dogfood. Task 1 and Task 2 are independent but will run sequentially (no parallel implementers).
