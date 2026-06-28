# Overview: codebase-map-churn-autoregen

## Goal
Make codebase-map freshness honest (churn-based, not mtime) and self-maintaining (auto-regenerate at pre-thinking entry), failing loudly when freshness cannot be verified.

## Architecture
Split the mechanism into two honest layers by runtime: a **detection layer** (cheap, scriptable) that the bash SessionStart hook and the pre-thinking agent each compute independently as code churn since the map's `last_updated`; and a **regeneration layer** (the agent-only `samsara:codebase-map` 3-explorer workflow) that only the agent can run. The hook signals; pre-thinking regenerates. Every uncomputable input collapses to an explicit `unknown` verdict, never to `fresh`.

## Tech Stack
Bash (SessionStart hook, git CLI for churn), YAML (map schema), Samsara skill markdown (pre-thinking, codebase-map), pytest over fixture git repos (Primary evaluator).

## Key Decisions
- **KD1: Session start detects only; pre-thinking regenerates.** A 3000ms bash hook cannot run the 3-agent regen workflow; detection is scriptable, regeneration is agent-only.
- **KD2: Auto-initiate, keep human review.** Regen fires without the user remembering to trigger it, but Phase 4 human review is retained in human-in-the-loop mode.
- **KD3: Churn replaces wall-clock.** Staleness = changed source files since `last_updated` (exclude `changes/`, `docs/`, `bugfix/`); default 30; configurable via `staleness_churn_threshold` in the map, replacing the dead `staleness_threshold_days`.
- **KD4: Uncomputable → unknown, never fresh.** No git / shallow / malformed `last_updated` / over-budget all yield an explicit unknown verdict (research kill condition #1 floor).
- **KD5: Converter decoupled.** The converter renders an honest no-op placeholder for codex/gemini from a template and does not read the source bash; the hook rewrite is Claude-Code-only.
- **KD6: Backward-compatible schema.** A map without the new field falls back to the default; a map still carrying the old field is not broken.

## Death Cases Summary
1. **mtime gaming (DC-1):** map `touch`ed looks fresh while churn is high — verdict must come from `last_updated` + churn, never mtime.
2. **regen failure silent reuse (DC-4):** failed regeneration leaves old map presented as fresh / `last_updated` bumped — must mark stale + reason, never advance the timestamp.
3. **uncomputable reported fresh (DC-2/DC-3):** no git or malformed `last_updated` defaults to fresh — must be an explicit `unknown`.

## File Map
<!-- File Map Consistency Check (self-applied, per ISSUE-001): every path traces to a Key Decision above. -->
- `skills/codebase-map/templates/codebase-map.yaml` — remove `staleness_threshold_days`, add `staleness_churn_threshold` (KD3, KD6) [Task 1]
- `hooks/check-codebase-map` — churn-based detection layer, honest `unknown` fallback, no mtime (KD1, KD3, KD4) [Task 2]
- `tests/test_hooks/test_check_codebase_map.py` (new) — Primary evaluator: pytest fixture-repo behavioral suite (KD1, KD3, KD4) [Task 2]
- `skills/pre-thinking/SKILL.md` + `skills/pre-thinking/flow.md` — auto-initiate regen at Atomic Context Boundary when over threshold (KD1, KD2) [Task 3]
- `skills/codebase-map/SKILL.md` — document auto-initiated trigger + `staleness_churn_threshold` + fail-honest contract (KD2, KD4) [Task 3]

Consistency note: no path lives under a Claude-only assumption that contradicts KD5 — the converter (`samsara_cli/converter/hook.py`) is intentionally **not** modified; codex/gemini behavior is covered by the existing converter suite as a no-regression check, not by a new file here.
