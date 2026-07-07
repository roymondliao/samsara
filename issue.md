# Samsara Issues

Issues discovered during real-world usage that require fixes to the samsara framework itself.

---

## ISSUE-001: Planning template allows File Map to contradict Key Decisions

**Discovered:** 2026-04-17
**Context:** continuous-learning feature implementation
**Severity:** High — silent architectural violation propagated through entire implementation chain

### What Happened

During the continuous-learning feature, Research concluded "Shared, not samsara-exclusive — knowledge belongs to the project, not the tool." This was confirmed by the user and recorded in Key Decisions.

However, when the main agent wrote `2-plan.md`, the File Map placed 3 out of 4 components inside `samsara/`:

```
Key Decisions: "Shared, not samsara-exclusive"
File Map:
  - samsara/hooks/check-learnings       ← contradicts "shared"
  - samsara/hooks/hooks.json            ← contradicts "shared"
  - samsara/skills/recall/SKILL.md      ← contradicts "shared"
  - scripts/learnings-rebuild.sh        ← correctly shared
```

The plan self-contradicted. Task specs inherited the wrong paths. Subagent implementers faithfully executed the wrong paths. Code reviewers did not check architectural placement. The user caught the error post-implementation.

### Error Chain

```
Research (correct) → Planning (contradiction introduced) → Task Specs (inherited) → Subagents (executed) → Review (not caught) → User (caught)
```

| Phase | Actor | Error? | Detail |
|-------|-------|--------|--------|
| Research | Main agent + user | No | "Shared" decision correctly made and confirmed |
| Planning | Main agent | **YES** | File Map contradicts Key Decisions. Agent chose samsara/ because existing hook infrastructure (check-codebase-map) was the path of least resistance |
| Task decomposition | Main agent | Amplified | Task specs copied wrong paths from plan's File Map |
| Implementation | Subagents | No | Executed plan as written — correct behavior given wrong input |
| Code review | Subagents | Not caught | Review checklist covers code quality, not architectural placement vs design decisions |
| Post-implementation | User | Caught | "這個 continuous-learning 不應該是屬於 Samsara 的功能" |

### Root Causes

**Root Cause 1: Planning template has no cross-check between File Map and Key Decisions.**

The `overview.md` template has both `Key Decisions` and `File Map` sections, but they are independent. No step in the planning process requires verifying that file paths are consistent with architectural decisions. A decision like "shared" in Key Decisions has no enforcement mechanism on the File Map below it.

**Root Cause 2: Path-of-least-resistance bias in planning.**

When the main agent wrote the File Map, it was influenced by samsara's existing infrastructure:
- `samsara/hooks/check-codebase-map` exists as a SessionStart hook pattern
- `samsara/skills/` is the familiar skill directory
- `samsara/hooks/hooks.json` is where hooks are registered

The agent unconsciously defaulted to the familiar structure instead of deriving the correct paths from the "shared" decision. This is a form of confirmation bias — the agent confirmed its pre-existing mental model (samsara = home for new features) rather than applying the research conclusion.

**Root Cause 3: Code reviewer scope does not include architectural compliance.**

The `samsara:code-reviewer` agent checks:
- Deletable code
- Naming honesty
- Silent rot paths
- Spec compliance (code-level)

It does NOT check:
- Whether file placement matches design decisions
- Whether the implementation architecture matches the plan's Key Decisions
- Cross-reference between plan-level decisions and implementation-level structure

### Required Fixes

#### Fix 1: Add cross-check step to planning skill

In `samsara/skills/planning/SKILL.md`, after the File Map is written, add a mandatory verification step:

```
### File Map Consistency Check

For each file in the File Map, verify:
1. Does the file's location (which plugin/directory) match the ownership decision in Key Decisions?
2. If Key Decisions says "shared" — is the file outside any specific plugin directory?
3. If Key Decisions says "plugin-specific" — is the file inside the correct plugin?

If any path contradicts a Key Decision, stop and resolve before proceeding to task decomposition.
```

#### Fix 2: Add architectural compliance to code-reviewer

In `samsara/agents/code-reviewer.md`, add a review dimension:

```
### Architectural Placement
- Are new files placed in the correct directory per the plan's Key Decisions?
- Does the file ownership match the plan's stated scope (shared vs plugin-specific)?
```

This requires the code-reviewer to receive the plan's Key Decisions as context (currently it only receives the diff and task requirements).

#### Fix 3: Add anti-bias prompt to planning skill

In the File Map section of the planning skill, add:

```
When writing file paths, derive them from Key Decisions — do not default to
existing infrastructure patterns. If Key Decisions says "shared," the file
must not be inside any plugin-specific directory, even if that plugin has
convenient existing infrastructure.
```

### Meta-Observation

This issue is itself the first candidate for the continuous-learning system being built. It is an agent-level judgment error (not a code defect), it is project-specific (samsara's planning process), and it was caught by a human correction. If `.learnings/` existed, this would be recorded as:

```yaml
---
id: 2026-04-17_plan-file-map-contradiction
domain: planning
trigger: "When writing File Map in a plan after Key Decisions include architectural scope decisions"
created: 2026-04-17
last_validated: 2026-04-17
status: active
source_session: manual
---

# Plan File Map contradicted Key Decisions

## What went wrong
Main agent wrote File Map paths inside samsara/ while Key Decisions stated "shared, not samsara-exclusive."

## Root cause
Path-of-least-resistance bias — existing samsara hook infrastructure was the familiar pattern. No cross-check step in the planning template forced verification.

## Correct approach
Derive file paths from Key Decisions. If "shared," place outside plugin directories. Add File Map consistency check step to planning.

## Context
Discovered during continuous-learning implementation. 4 tasks were fully implemented in wrong locations before user caught the error.
```

---

**Note:** ISSUE-002, 003, 004 were originally recorded here but are NOT samsara issues.
They belong to the continuous-learning feature (shared, kaleidoscope-tools root level).
Moved to: `changes/2026-04-15_continuous-learning/issues.md`

**Note:** The Loop Engineering Gap Analysis (originally ISSUE-005 ~ ISSUE-009, recorded 2026-06-10)
was moved to `roadmap.md` (renumbered RM-001 ~ RM-005) — those entries are capability
enhancements identified through analysis, not defects discovered during usage.

---

## ISSUE-002: `samsara-cli validate` has no CI consumer — an alarm clock that never rings

**Discovered:** 2026-07-04
**Context:** workflow-subtraction-optimization feature, task-8 final reconciliation
**Severity:** Medium — a whole guard mechanism silently inert

### What Happened

During the feature's final reconciliation, `uv run samsara-cli validate --platform codex`
reported 36 issues on the feature branch. A HEAD-worktree comparison showed **main was
already at 42 issues** — the validator has been failing continuously, and nothing consumes
its exit code: CI gates on pytest only, no release step runs validate, and no human ritual
checks it. Tests green + validate red is the standing steady state.

### Why It Matters

This is the exact failure shape the same feature removed elsewhere (`expiry_date` — a
re-review promise no mechanism ever read). A validator that always fails and blocks nothing
is worse than no validator: it trains everyone to ignore it, and a real conversion
regression would land invisibly among the 36 pre-existing issues.

### Root Cause (initial read)

The validator scans workflow artifacts (`changes/`, `docs/`) for platform-specific patterns
alongside the live instruction surface — historical artifacts can never be "fixed" (they are
records), so the issue count can never reach zero, so the exit code can never be consumed
as a gate. Scope design makes the tool ungateable.

### Candidate Fixes (for a future feature — not attempted here)

1. Scope validate to the live instruction surface (skills/, agents/, references/, hooks/),
   excluding `changes/` and `docs/` historical artifacts — makes zero reachable, then wire
   the exit code into CI.
2. Or split: `validate --strict` (live surface, CI-gated) vs `validate --all` (informational).
3. Or delete the validator if conversion tests already cover its guarantees — per the axiom,
   a guard nobody consumes should not exist.

**Re-review signal:** next release or next converter change touches validate behavior;
**owner:** repo maintainer.

---

## ISSUE-003: ~~Structure-spec evidence chain has no code-level enforcement~~ — WITHDRAWN (2026-07-07)

**Status: WITHDRAWN.** Two reasons, recorded per the 1.0.0 design direction (`changes/2026-07-06_samsara-1.0.0-codebase-craft/`, §3.6/§7 — user decision 2026-07-06):

1. **The premise was reversed.** The proposed fix — code-enforcing the structure-spec chain via `samsara-cli validate` — would have code-enforced *judgment* (whether a boundary is right, whether drift matters), turning judgment into ritual. Format-vs-judgment reclassification (design note 4): only mechanical shape ever gets script teeth; judgment gets visibility + adversarial review + consumption discipline, never a gate. Additionally, samsara-cli is the cross-service integration layer, not the home of feature-artifact format checks — those belong to per-skill validate scripts.
2. **The mechanism this issue guarded was removed.** The structure-spec gate machinery (spec-path guard, structure_refs, fragment injection with 50% signal, spec-mode drift_items, structural_drift aggregation, 0-dangling audit over structure-spec) was deleted on 2026-07-07 in favor of the 1.0.0 global thinking channel (Real Seams + `seam`/`affects`/`anchors` + dual-face `structural_decisions`). The legitimate format core this issue pointed at now has real deterministic teeth: `skills/planning/scripts/validate_format.py` and `skills/implement/scripts/validate_format.py` (dangling-ref checks run as programs, not prose obedience), re-run terminally by validate-and-ship Step 1.

Original entry preserved below for the record.

**Discovered:** 2026-07-05
**Context:** structural-honesty-mechanisms feature, Level-2 iteration triage
**Severity:** High — single point of dependency for the feature's core guarantee, degradation is by-design invisible

### What Happened

The structural-honesty-mechanisms feature landed a four-link evidence chain (planning
generates `structure-spec.yaml` → implement injects fragments at dispatch → code-quality-reviewer
consumes in spec mode → iteration/validate-and-ship audit). Per KD-2 (zero `samsara_cli`
code in this feature's scope), **every link is enforced only by prose instructions** in
skills/agents markdown. Four scar items across task-1..4 record this under
`systemic_ref: doc-vs-runtime-obedience` and `doc-instruction-no-code-enforcement`.

### Why It Matters

The framework's corruption signature applies to itself: if a future agent model quietly
stops obeying the prose (skips the dispatch check, omits `drift_items`, never runs evidence
resolution), the chain degrades into ceremony **and nothing detects it** — doc-contract
tests only prove the instructions still exist, not that they are followed. This is not a
permanent-risk shape (Accept); it is planned-work shape (Defer): KD-2 was a scope decision
for one feature, not a permanent architecture decision.

### Scope of the fix (next feature)

Wire `samsara-cli validate` (whose live-surface scoping was just fixed in ISSUE-002) to
consume `structure-spec.yaml` mechanically:

1. Schema check — parse every `changes/*/structure-spec.yaml`; unparseable = error
   (today "unreadable → FAIL" is prose-only, dispatch-template.md).
2. Dangling-ref check — `planned_task` refs must resolve against the same feature's
   `index.yaml` task ids; `git_history` refs must point at existing repo paths
   (today this runs only when an agent obeys validate-and-ship's 0-dangling prose).
3. In-scope instances explicitly covered by this issue: the 50% directed-injection signal
   has no code check (task-2 scar), and `drift_items` missing-vs-empty distinction has no
   code check at consumption time (task-3 scar) — both become machine-checkable once the
   validator owns spec parsing.

Evidence anchor per docs/thinking.md ch.4: this issue entry upgrades the four deferred scar
items from imagination-level ("any runtime-enforcement someday") to `planned_task`-level —
the next feature's structure-spec can cite ISSUE-003 as its change reason.

**Re-review signal:** next feature that touches samsara_cli validators, or first ship of a
feature whose structure-spec was never machine-parsed end-to-end;
**owner:** yuyu_liao.
