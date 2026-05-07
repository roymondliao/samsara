# Task 10: Codex Smoke Test — Local End-to-End Verification

## Context

Read: overview.md

This task creates the Layer 4 smoke test that verifies converted samsara actually works on Codex. This is the only test that touches the real Codex CLI environment.

Marked with `@pytest.mark.integration` — runs only with `pytest -m integration` on a machine with Codex CLI installed. Does NOT run in CI (Codex requires OPENAI_API_KEY which is subscription-based, not available as API key).

Smoke test flow:
1. Run full conversion pipeline on actual samsara source
2. Install converted output to a temp Codex skills directory
3. Verify Codex can discover the installed skills
4. (Optional) Trigger a skill and verify response

Limitations:
- Cannot test full workflow chain (requires interactive Codex session)
- Cannot verify agent dispatch behavior (requires model interaction)
- CAN verify: file structure recognized by Codex, skills appear in skill list, hooks.json is valid

## Files

- Create: `tests/integration/test_smoke_codex.py`
- Test: self

## Death Test Requirements

- Test: Smoke test must skip gracefully if Codex CLI not installed — not fail with confusing error
- Test: Smoke test must NOT modify user's actual Codex config — use isolated temp directory
- Test: Smoke test must clean up temp install directory after completion — not leave artifacts

## Implementation Steps

- [ ] Step 1: Write smoke test setup:
  - Check `codex --version` — skip all tests if not installed
  - Create temp directory for isolated installation
  - Run full convert + install targeting temp directory
- [ ] Step 2: Write structural smoke tests:
  - Verify `.codex-plugin/plugin.json` exists and parses
  - Verify all skill directories exist with valid SKILL.md
  - Verify all agent .toml files exist and parse
  - Verify hooks.json exists and has valid structure
- [ ] Step 3: Write Codex discovery smoke test (if feasible):
  - Check if Codex's skill scanner can find skills in the installed directory
  - This may require `codex exec` or inspecting Codex's skill loading logs
- [ ] Step 4: Write cleanup fixture (teardown that removes temp directory)
- [ ] Step 5: Run smoke test locally — verify it passes
- [ ] Step 6: Write scar report

## Expected Scar Report Items

- Potential shortcut: Codex skill discovery test may not be feasible without an interactive session — Codex may only scan skills at session start. If so, structural validation is the best we can do.
- Assumption to verify: Installing to a custom directory (not `~/.codex/skills/`) is recognized by Codex — may need to use `CODEX_HOME` env var or symlink approach
- Potential shortcut: No model interaction in smoke test means we can't verify that transformed skill instructions actually produce correct behavior. This is an inherent limitation of automated testing.

## Acceptance Criteria

- Covers: "Success - install to Codex" (real environment verification)
- Covers: "Hook injection silent failure - feature flag not documented" (verify hook structure is valid for Codex)
