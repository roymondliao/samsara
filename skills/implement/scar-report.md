# Scar Report — Format Guide

Every completed task leaves a scar report. This is the yin-side output of implementation — it records what the code cannot say about itself.

> 如果 AI 完成任務後宣告「完成」但不附帶 scar report，該完成狀態標記為 `completion_unverified`。

## Format

Scar reports use YAML format at `scar-reports/task-N-scar.yaml`:

```yaml
task_id: task-1
completion_status: done  # done | done_with_concerns | blocked

known_shortcuts:
  # What corners were cut? What would you do differently with more time?
  - "Skipped concurrent session edge case — single-user assumption"
  - "Used string matching instead of proper parser for config values"

silent_failure_conditions:
  # Under what conditions will this implementation silently produce wrong results?
  - "If auth service latency exceeds 3s, fallback to cached token without marking degraded state"
  - "If database connection pool is exhausted, requests queue silently with no timeout"

assumptions_made:
  # What was assumed to be true but not verified?
  - assumption: "Session token TTL is always 24h"
    verified: false
  - assumption: "Database supports row-level locking"
    verified: true

debt_registered: true  # Was technical debt formally recorded?
debt_location: "TODO in auth/middleware.ts:42"  # Where? (null if debt_registered is false)
```

## Rules

1. **No empty scar reports.** If `known_shortcuts`, `silent_failure_conditions`, and `assumptions_made` are all empty, you haven't thought hard enough. Every implementation has at least one assumption.
2. **Honest completion status:**
   - `done` — all tests pass, no unverified assumptions blocking correctness
   - `done_with_concerns` — tests pass, but there are unverified assumptions that could affect correctness
   - `blocked` — cannot complete due to external dependency or unresolvable issue
3. **debt_registered must be true** if any known_shortcuts or silent_failure_conditions exist. If you recorded a shortcut but didn't register the debt, that's hiding a wound.

## Anti-Pattern: The Clean Scar

A scar report that says "no shortcuts, no silent failures, no assumptions" is suspicious. It usually means the author didn't look hard enough, not that the code is perfect. Challenge it.
