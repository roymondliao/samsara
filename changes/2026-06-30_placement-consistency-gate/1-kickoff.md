# Kickoff: placement-consistency-gate (ISSUE-001 / A4)

## Problem Statement

A Samsara plan can silently contradict itself on **where things go**. `overview.md` carries `Key Decisions` (architectural decisions, including placement/ownership like "shared, not samsara-exclusive") and `File Map` (the actual paths) as two **independently written** sections with no consistency gate between them. So a planning agent can decide "this is shared" and then place files under `samsara/`, and nothing catches the contradiction: planning has no cross-check, the implementer faithfully executes the wrong paths, and the code-reviewer audits code quality but never receives the plan's Key Decisions and has no architectural-placement dimension. The contradiction propagates to the human, post-implementation. Root cause is path-of-least-resistance / confirmation bias toward existing infrastructure — and exhortation already exists in the bootstrap ("no confirmation bias") yet failed, so the fix must be a **check boundary**, not a louder instruction. The reshaped design: a lightweight planning self-check as a cheap first pass, plus an **independent code-reviewer** (no planner bias) as the reliable backstop — scoped to placement/ownership decisions, not every Key Decision.

## Evidence

- `issue.md` ISSUE-001 (recorded 2026-04-17): in the continuous-learning feature, Research correctly decided "Shared, not samsara-exclusive" (human-confirmed), but the plan's File Map placed 3 of 4 components under `samsara/`. 4 tasks were fully implemented in the wrong locations before the human caught it.
- Live state verified (this branch, off main):
  - `skills/planning/SKILL.md` — no consistency check (grep: zero hits for consistency/key-decision↔file-map).
  - `skills/planning/templates/overview.md:12` `## Key Decisions` and `:22` `## File Map` are independent sections.
  - `agents/code-reviewer.md` — no architectural-placement / ownership / key-decision dimension.
  - `issue.md` still records the 3 Required Fixes with no "Fixed" status.
- The three Required Fixes were planned (issue.md + a `changes/2026-04-21_planning-file-map-consistency/` directory) but **never landed in live skills** — the defect-prevention防線 itself drifted.

## Risk of Inaction

Placement/ownership drift keeps shipping undetected: features built under the wrong plugin / wrongly coupled to samsara, caught late (post-implementation rework) or never (wrong architecture ships and ossifies). Because the implementer "correctly executes wrong input," every downstream gate looks green while the architecture silently diverges from the decision the human approved — the most expensive kind of late catch.

## Scope

### Must-Have (with death conditions)

- **Code-reviewer architectural-placement dimension + Key Decisions reach the reviewer (fix #2 — the core).** The code-reviewer (a fresh, independent agent without the planner's bias) receives the plan's Key Decisions and judges whether file placement matches the placement/ownership decisions. Death condition: if placement/ownership stops being expressed in Key Decisions, the reviewer has nothing to check against — must be tied to the planning artifact contract (a Key Decision that names placement).
- **Planning lightweight self-check (fix #1 — option b, judgment not structured field).** At the end of planning, walk each File Map path against the placement/ownership Key Decisions; on a genuine contradiction, STOP before task decomposition. Death condition: if this produces high false-positive friction and planning learns to skip it, downgrade to advisory or remove — a gate that fires on non-contradictions is worse than none (Q2-C).
- **Anti-bias prompt in planning (fix #3).** Derive paths from Key Decisions; do not default to existing infrastructure. Death condition: low-cost; remove only if it demonstrably adds noise without reducing drift.
- **Doc-contract guard tests.** Each landed rule guarded so it cannot silently rot: planning consistency-check clause present; code-reviewer placement dimension present; and critically the **data-flow** (Key Decisions are actually included in the reviewer dispatch payload). Death condition: none — floor (Issue-001/Task 3 proved unguarded doc-rules rot, and this very防線 already rotted once).

### Nice-to-Have
- Structured machine-checkable `ownership:` field in Key Decisions (deferred — user chose judgment + independence over structure; revisit only if reviewer judgment proves unreliable in practice).

### Explicitly Out of Scope
- A structured/parseable ownership field as the primary mechanism (user chose b: independence-of-the-reviewer is the anti-bias mechanism, not a field).
- Checking ALL Key Decisions for consistency — only **placement/ownership** decisions vs File Map paths.
- Resurrecting/merging the stale `changes/2026-04-21_planning-file-map-consistency/` plan directory.
- Enforcing placement at runtime via code (it is an agent-judgment doc contract, like the codebase-map fail-honest contract — guarded by presence/data-flow tests, real obedience proven by dogfood).

## North Star

```yaml
metric:
  name: "placement-drift caught before implementation completes"
  definition: "A plan whose File Map contradicts a placement/ownership Key Decision is flagged by the planning self-check OR the code-reviewer placement dimension BEFORE the human catches it post-implementation (defense-in-depth: only fails if BOTH independent gates miss it)"
  current: "0 gates — neither planning nor review checks placement; 100% of placement drift reaches the human post-impl (n=1 known incident, ISSUE-001)"
  target: "a placement-contradicting plan is stopped by at least one of the two gates before task decomposition / before review passes"
  invalidation_condition: "If placement/ownership decisions are so rare or so obvious that no plan ever contradicts them, the two gates are ceremony — the mechanism should not exist"
  corruption_signature: "The reviewer dimension is added to code-reviewer.md but the implement dispatch never actually passes Key Decisions — the reviewer 'checks placement' against nothing and silently passes. Looks reviewed, isn't."

sub_metrics:
  - name: "Key-Decisions-reach-reviewer data flow"
    current: "absent — reviewer dispatch only gets diff + task requirements"
    target: "the reviewer dispatch payload includes the plan's Key Decisions"
    proxy_confidence: high
    decoupling_detection: "A doc-contract test asserting the implement/iteration dispatch template includes Key Decisions in the reviewer payload — if the placement dimension exists but this test is absent/red, the gate is decoupled (checks nothing)"
  - name: "false-positive friction"
    current: "n/a (no gate yet)"
    target: "the planning self-check fires only on genuine placement contradictions, not every path"
    proxy_confidence: medium
    decoupling_detection: "Watch for planning runs that STOP on non-contradictions, or that start omitting the check step — either signals the gate became noise"
```

## Stakeholders
- **Decision maker:** roymond (user) — confirmed problem real, scope = placement/ownership only, design = lightweight planning self-check (b) + independent reviewer as reliable backstop
- **Impacted teams:** all Samsara users (planning + review run on every feature)
- **Damage recipients:** every planning run (extra self-check step — friction if mis-designed); the planning author (false-positive reconciliation); future maintainers (new check + reviewer dimension + Key-Decisions→reviewer data flow to maintain)
