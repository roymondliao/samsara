# Plan: codebase-map-churn-autoregen

## Pre-thinking Commitments Consumed

- **Decision:** Proceed
- **Accepted gaps:** none
- **System design constraints:**
  - Session start = detection + strong signal only (bash hook, git churn). Regeneration is NOT performed by the hook.
  - Regeneration auto-initiates at pre-thinking entry; Phase 4 human review retained in human-in-the-loop mode.
  - Staleness signal = count of changed source files since the map's `last_updated` (exclude `changes/`, `docs/`, `bugfix/`); default threshold ~30; stored as a configurable field in `.samsara/codebase-map.yaml`, replacing the dead `staleness_threshold_days`.
  - Git-uncomputable (no git / shallow / unparseable `last_updated`) → explicit "churn unknown", never "fresh".
  - The rewritten hook is Claude-Code-only; the `samsara_cli` converter renders an honest no-op placeholder for codex/gemini and is **decoupled from the source bash** (it does not read it). Constraint reduces to: converter tests stay green + placeholder never claims fresh.
  - Map schema change is backward compatible: a map missing the new field falls back to the default; a map still carrying the old field is not broken (old field simply unread, as today).
- **Primary evaluator:** pytest behavioral suite over fixture git repositories.
- **Pass signal:** (1) `touch` of the map file does not change the verdict; (2) churn over threshold → stale verdict, under → fresh; (3) git/last_updated uncomputable → explicit "churn unknown", never fresh; (4) forced regen failure → map marked stale + reason, never silent reuse.
- **Fail signal:** mtime touch flips to fresh; over-threshold reports fresh; git-absent reports fresh; regen failure leaves no stale mark / silent reuse.
- **Feedback loop:** on suite failure, re-run the single failing fixture in isolation, inspect actual vs expected verdict before editing detection logic.

## Step 2: Technical Specification

### Components

| Component | Change | Runtime |
|---|---|---|
| `skills/codebase-map/templates/codebase-map.yaml` | Remove dead `staleness_threshold_days`; add `staleness_churn_threshold` (int, changed source files; default 30) | artifact schema |
| `hooks/check-codebase-map` | Replace mtime/7-day logic with: read `last_updated` from map YAML → compute git churn since that date → compare to threshold (field or default) → emit status; honest "churn unknown" on any uncomputable input | bash, Claude Code, SessionStart, 3000ms |
| `skills/pre-thinking/SKILL.md` + `skills/pre-thinking/flow.md` | Atomic Context Boundary: on entry, compute churn; if over threshold, auto-initiate `samsara:codebase-map` regeneration (retaining Phase 4 human review); on regen failure, mark map stale + record reason, never silently reuse | agent behavior |
| `skills/codebase-map/SKILL.md` | Document the auto-initiated trigger + the `staleness_churn_threshold` field; fail-honest contract on regen failure (do NOT bump `last_updated` if regen did not complete) | agent behavior |

### I/O with Unknown Output — the hook's verdict (three states, not two)

The hook's freshness verdict must be exactly one of:
- `fresh` — map exists, churn computable, churn < threshold → **exit 0, no output** (zero token cost)
- `stale` — map missing, OR churn computable and ≥ threshold → emit directive message with the churn count / missing status
- `unknown` — map exists but churn is **not computable** (no git repo, shallow clone, `last_updated` absent/malformed, git command failed/timed out) → emit explicit "churn unknown — cannot verify freshness" message

Treating `unknown` as `fresh` is the central defect this feature exists to prevent.

### Death Cases (not edge cases)

**DC-1 — mtime gaming.** Trigger: map file `touch`ed (mtime = now) but `last_updated` old and churn high. Appears: fresh (today's mechanism). Truth: stale. Detect: verdict derives from `last_updated` + git churn, never file mtime.

**DC-2 — git uncomputable.** Trigger: project is not a git repo / shallow clone / detached with no history. Appears: fresh, or crash under `set -u`. Truth: cannot determine churn. Detect: verdict = `unknown`, exit 0 with explicit message, no crash.

**DC-3 — `last_updated` missing or malformed.** Trigger: map exists but no `last_updated:` line, or value not a git-parseable date. Appears: fresh or crash. Truth: age indeterminate. Detect: verdict = `unknown`, recommend regeneration.

**DC-4 — regen failure silently reusing old map.** Trigger: pre-thinking auto-initiates regen but it fails (explorer error, write failure, user aborts review). Appears: map present and `last_updated` bumped → looks freshly regenerated. Truth: regen did not complete. Detect: on failure the map is marked stale with a reason and `last_updated` is **not** advanced; the corruption signature (timestamp bumped without content change) is explicitly guarded.

**DC-5 — over-threshold reported fresh.** Trigger: churn = 50 files, threshold = 30. Appears: fresh. Truth: stale. Detect: verdict = `stale` with churn count in message.

**DC-6 — converter false-fresh regression.** Trigger: converted codex/gemini hook runs without `CLAUDE_PROJECT_DIR`. Appears: could claim fresh or crash under `set -u`. Truth: cannot check on that platform. Detect: converted hook is an honest no-op (exit 0, no false-fresh claim); existing converter tests stay green.

**DC-7 — churn computation exceeds the 3000ms hook budget.** Trigger: very large history. Appears: hook killed mid-run → no output → session proceeds as if fresh. Truth: not computed. Detect: bound the git invocation; on non-completion, verdict = `unknown`, not silent fresh.

## Step 2.5: Acceptance Criteria

See `acceptance.yaml`. Order: silent-failure (DC-1, DC-4) → unknown-outcome (DC-2, DC-3, DC-7) → degradation (DC-6 converter no-op) → happy path with evidence (fresh exit-0; stale with churn count).

## Step 3: Task Decomposition

- **Task 1 — map schema field swap** (artifact contract; no silent-failure risk by itself, but defines the contract Task 2 consumes). Depends on: none.
- **Task 2 — bash hook churn detection + honest fallback** (the Primary-evaluator centerpiece; owns DC-1, DC-2, DC-3, DC-5, DC-7). Depends on: Task 1 (field name).
- **Task 3 — pre-thinking auto-regen + codebase-map fail-honest** (agent behavior; owns DC-4; converter no-op DC-6 verified here). Depends on: Task 1 (threshold semantics), Task 2 (shared churn definition).

Converter coverage (DC-6) is a verification, not a code task: confirm `tests/test_converter/` stays green and the rendered placeholder makes no fresh claim. Tracked as an acceptance scenario, validated in validate-and-ship.

Updating this repo's own live `.samsara/codebase-map.yaml` (currently 210 files over threshold, still carrying the old field) is **downstream dogfood**, not part of this mechanism work — the new mechanism will itself flag it at next pre-thinking entry.
