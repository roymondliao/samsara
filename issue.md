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
