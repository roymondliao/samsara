# Task 2: Bash hook churn detection + honest unknown fallback

## Context
Read: overview.md

This is the Primary-evaluator centerpiece. Rewrite `hooks/check-codebase-map` so freshness is computed from **code churn since the map's `last_updated`**, never from file mtime. The hook runs on `SessionStart` (Claude Code only, `CLAUDE_PROJECT_DIR` set), `set -euo pipefail`, timeout 3000ms. It must emit the same JSON output contract as today when stale/unknown, and exit 0 silently when fresh.

Current behavior to replace (`hooks/check-codebase-map`): reads file mtime via `stat`, compares to hardcoded `-gt 7` days, never reads `last_updated`, never uses git.

Threshold field (from Task 1): `staleness_churn_threshold` in `.samsara/codebase-map.yaml`; default 30 when the field is absent.

Churn definition: number of distinct changed source files in commits since `last_updated`, excluding paths under `changes/`, `docs/`, `bugfix/`. The exact git invocation is the implementer's choice, but it must be bounded so it cannot hang past the hook budget.

## Files
- Modify: `hooks/check-codebase-map` (full rewrite of the staleness logic; keep the JSON `escape_for_json` + `hookSpecificOutput` output contract)
- Create: `tests/test_hooks/test_check_codebase_map.py` (pytest, drives the bash hook via subprocess against fixture git repos)

## Death Test Requirements
- Test DC-1 (mtime gaming): fixture repo, map `last_updated` 90 days ago, ≥ threshold changed files since, map file `touch`ed to now → verdict MUST be stale, not fresh.
- Test DC-2 (not a git repo): fixture dir with a map but no `.git` → verdict MUST be `unknown`; hook exits 0; no crash under `set -u`; output states freshness unverifiable.
- Test DC-3 (last_updated missing/malformed): map present without `last_updated:`, and map with `last_updated: "not-a-date"` → both verdict `unknown`, recommend regen.
- Test DC-5 (over-threshold): churn 50, threshold 30 → verdict stale; message includes the count.
- Test DC-7 (bounded computation): assert the git invocation is bounded (e.g., a fixture that would be expensive does not leave the hook with no output → on non-completion, `unknown`, never silent fresh). At minimum assert the failure-path maps to `unknown`.

## Unit Test Contract
- Contract source: the hook's **emitted output contract** (a stable boundary/CLI contract) — given a fixture `CLAUDE_PROJECT_DIR`, the hook's (exit code, stdout JSON `hookSpecificOutput.additionalContext`) pair. Fresh = exit 0 + empty stdout; stale/unknown/missing = exit 0 + JSON whose `additionalContext` names the status.
- A unit test must assert this (exit code, parsed-JSON additionalContext status) contract, NOT internal variable names, the exact git command string, or message wording beyond the status token and (for stale) the presence of the churn count.

## Implementation Steps
- [ ] Step 1: Write death tests (DC-1, DC-2, DC-3, DC-5, DC-7) driving the hook via subprocess against tmp_path git fixtures
- [ ] Step 2: Run death tests — verify they fail against the current mtime-based hook
- [ ] Step 3: Write unit tests asserting the (exit code, JSON additionalContext status) contract for fresh / stale / unknown / missing
- [ ] Step 4: Run unit tests — verify they fail
- [ ] Step 5: Rewrite the hook: read `last_updated` from map YAML (grep a simple scalar; malformed → unknown), compute bounded git churn excluding changes/ docs/ bugfix/, read `staleness_churn_threshold` (default 30), map every uncomputable input to `unknown`, keep the JSON output contract
- [ ] Step 6: Run all tests — verify they pass
- [ ] Step 7: Write scar report
- [ ] Step 8: Report back (do not commit)

## Expected Scar Report Items
- Potential shortcut: grep-parsing YAML `last_updated` in bash is fragile — record the exact accepted format and that anything else is treated as `unknown` (this is correct, not a bug, but must be explicit).
- Assumption to verify: the git churn command completes within the 3000ms hook budget on a large repo — verify, and on doubt prefer `unknown` over a slow fresh.
- Silent failure to watch: a git command that errors (not just "no git") must also map to `unknown`, not be swallowed into fresh by `set -e`/`|| true` misuse.

## Acceptance Criteria
- Covers: "Silent failure - mtime gamed (DC-1)", "Unknown - not a git repo (DC-2)", "Unknown - last_updated missing or malformed (DC-3)", "Unknown - churn exceeds budget (DC-7)", "Success - fresh map exits silently", "Success - over-threshold flagged with churn evidence (DC-5)", "Success - threshold read from map, default when absent"
