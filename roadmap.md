# Samsara Roadmap

Planned framework enhancements. Unlike `issue.md` (defects discovered during real-world usage), entries here are capability gaps identified through analysis — things samsara should grow, not things samsara got wrong.

---

## Loop Engineering Gap Analysis (RM-001 ~ RM-005)

**Recorded:** 2026-06-10
**Context:** Comparison of samsara against loop engineering / harness engineering as described in:
- https://addyo.substack.com/p/loop-engineering (Addy Osmani)
- https://cobusgreyling.substack.com/p/loop-engineering (Cobus Greyling)

**Conclusion of the analysis:** Samsara is a complete harness engineering artifact (equips a single agent run: skills, sub-agents with maker/checker split, per-feature durable state, session hooks). It has almost no loop engineering layer (the meta-layer that continuously orchestrates multiple runs: scheduling, discovery, parallelization, outward operation). The diagnostic question is "who triggers this mechanism?" — every samsara mechanism today is triggered by a human or by session start.

Counter-observation: samsara already leads on the discipline side that loop engineering articles warn about (verification discipline = death tests, comprehension debt = scar reports, cognitive surrender = STEP 0). The gaps below are mechanical, not philosophical — which makes samsara a safer-than-usual base to evolve into loops.

**Recommended sequencing:** RM-004 (global state, cheap and read-only) → RM-001 (heartbeat) → RM-002 (auto mode beyond session) → RM-003 (worktree parallelism) → RM-005 (connectors). Each step is independently verifiable.

---

## RM-001: No automation/scheduling heartbeat — discovery is entirely human-triggered

**Type:** Enhancement (loop engineering: Automations / Scheduling)
**Priority:** High — this is the root gap; without a heartbeat there is no loop, only one-off sessions

### Current State

Every samsara workflow starts with "使用者描述問題/任務" (the entry node of the routing graph). The only autonomous mechanism is the `SessionStart` hook, which fires when a human opens a session.

### The Gap

Samsara already produces exactly the signals a discovery loop should consume, but nothing consumes them:

- **Scar reports** (`changes/<feature>/` YAML) — known wounds awaiting resolution
- **Failure budgets** (ship manifests) — recorded debt at ship time
- **Codebase-map staleness** — `check-codebase-map` detected "STALE (47 days)" this session, but can only nag a human to run `/samsara:codebase-map`

This is the "manual checking" anti-pattern both articles describe. A scheduled triage loop (e.g. Claude Code `/loop`, `/schedule`, or cron-driven automation) should periodically read these signals, triage them, and surface actionable items to an inbox — instead of waiting for a human to remember.

### Required Enhancement

A scheduled triage entry point (skill or automation) that:
1. Scans scar reports, failure budgets, and map staleness across all features
2. Triages cheaply (no sub-agent spawning during triage — cost discipline per both articles)
3. Writes actionable findings to a triage inbox/state file for human or auto-mode pickup

---

## RM-002: Auto mode is session-scoped — the loop's decision organ exists, but has no heartbeat or senses

**Type:** Enhancement (loop engineering: autonomous orchestration)
**Priority:** Medium — auto-gatekeeper is the hardest prerequisite already solved; the rest is mechanical

### Current State

`samsara:auto-gatekeeper` answers workflow gate questions without human intervention and records append-only decisions in `changes/<feature>/auto-decisions.md`. README explicitly scopes this as session-level: an auto run starts when a human starts it, and ends when the workflow ends.

### The Gap

Auto mode solves loop engineering's hardest problem — "who answers gate questions unattended" — with better audit discipline (decision provenance via append-only records) than most loop implementations described in the articles. But it cannot:
- Wake itself up (no scheduling — depends on RM-001)
- Discover its own work (no signal consumption — depends on RM-001/RM-004)
- Chain runs (one feature per invocation; no "finish, pick next item from triage inbox, continue")

### Required Enhancement

Once RM-001/RM-004 exist: an auto-mode loop driver that picks items from the triage inbox, runs the existing auto workflow per item, and records cross-run state. The gatekeeper and its decision format need no change — they were designed for exactly this.

---

## RM-003: No worktree isolation or parallel task execution

**Type:** Enhancement (loop engineering: Worktrees / safe parallelism)
**Priority:** Medium

### Current State

`samsara:implement` dispatches sub-agents strictly sequentially in the same checkout: dispatch → death test → review → next task. Only the main agent commits, after all tasks complete. `index.yaml` already records task dependencies — the information needed for parallelization exists, but is only used for ordering.

### The Gap

Two implementers cannot work simultaneously without colliding on files. Both articles list git worktree isolation as a core building block: each agent works in its own checkout sharing repository history.

### Required Enhancement

In `samsara:implement`, for tasks whose dependencies (per `index.yaml`) are mutually independent: dispatch implementers into isolated worktrees and merge results back through the existing review gate. Sequential execution remains the default; parallelism is opt-in per dependency analysis.

### Constraint to Preserve

"Subagents don't commit" must survive parallelization — worktree merge-back happens under main-agent control, after review passes.

---

## RM-004: Per-feature state is an archaeological record, not a loop's working memory

**Type:** Enhancement (loop engineering: Durable State Management)
**Priority:** High — cheapest gap to close, and a prerequisite for RM-001/RM-002

### Current State

`changes/<feature>/` answers the three durable-state questions (what are we working on / what did we try / what awaits handoff) well — but only per feature. There is no global view.

### The Gap

To answer "across the whole project, which scars are unpaid, which failure budgets are overspent, which `accept_gap` auto-decisions are still open" requires a human to dig through every feature directory. The articles' durable-state pattern (STATE.md / LOOP-STATE) is a single place a loop reads first and writes last.

### Required Enhancement

A global state artifact (e.g. `changes/LOOP-STATE.yaml` or equivalent) aggregating:
1. Open scar items across all features (from scar report YAML)
2. Failure budget status (from ship manifests)
3. Open `accept_gap` decisions (from auto-decisions.md files)
4. Items awaiting human handoff

Build as a derived/regenerable view (read-only aggregation script or skill) so it cannot drift into a second source of truth — the per-feature artifacts remain authoritative.

---

## RM-005: Workflow ends as a commentator, not an operator — no outward connectors

**Type:** Enhancement (loop engineering: Plugins / Connectors)
**Priority:** Low — external tools (gh, create-pr) cover this manually today

### Current State

`samsara:validate-and-ship` produces a ship manifest and stops. Opening PRs, updating tickets, and notifying channels all happen outside the framework (gh CLI, kaleidoscope-tools create-pr).

### The Gap

Both articles describe connectors as what turns a loop "from commentator to operator." For unattended auto-mode runs (RM-002), a workflow that cannot open its own PR leaves completed work stranded until a human notices.

### Required Enhancement

An optional ship-time connector step in validate-and-ship: open a PR (with the ship manifest as body context) and update the triage inbox/global state. Must remain opt-in and gated — outward actions are exactly where "unattended loops make unattended mistakes" bites hardest, so default behavior stays unchanged.
