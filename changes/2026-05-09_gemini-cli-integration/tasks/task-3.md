# Task 3: Add Gemini hook settings conversion

## Context

Read: `changes/2026-05-09_gemini-cli-integration/overview.md`

Gemini hooks are configured in `.gemini/settings.json`, and hook scripts communicate through JSON stdin/stdout. The SessionStart hook must inject bootstrap text through `hookSpecificOutput.additionalContext`.

## Files

- Modify: `samsara_cli/converter/hook.py`
- Modify: `samsara_cli/converter/engine.py`
- Modify: `samsara_cli/config/templates/gemini-cli/hook.sh.j2`
- Modify: `samsara_cli/config/templates/gemini-cli/settings.json.j2`
- Create: `tests/test_converter/test_hook_gemini.py`
- Modify: `tests/test_converter/test_hook_death.py`
- Modify: `tests/test_converter/test_engine.py`
- Modify: `tests/test_converter/test_engine_death.py`

## Death Test Requirements

- Test: rendered Gemini hook script outputs parseable JSON for a minimal SessionStart stdin payload.
- Test: rendered hook stdout contains no plain-text logs outside JSON.
- Test: output JSON contains `hookSpecificOutput.additionalContext`; `systemMessage` alone is not enough.
- Test: missing bootstrap file produces degraded valid JSON, not shell error text on stdout.
- Test: generated `.gemini/settings.json` contains `hooks.SessionStart` with the expected command.

## Implementation Steps

- [ ] Step 1: Write hook JSON protocol death tests.
- [ ] Step 2: Run death tests with `source .venv/bin/activate` and `uv run pytest <test files>`; verify they fail.
- [ ] Step 3: Write happy-path settings rendering tests.
- [ ] Step 4: Run happy-path tests; verify they fail.
- [ ] Step 5: Extend HookConverter or add Gemini-specific helpers for settings JSON and hook script rendering.
- [ ] Step 6: Update engine hook output path for Gemini to `.gemini/settings.json` and `.gemini/hooks/samsara-session-start.sh`.
- [ ] Step 7: Run Codex hook tests plus Gemini hook tests; verify both pass.
- [ ] Step 8: Write scar report.
- [ ] Step 9: Commit.

## Expected Scar Report Items

- Potential shortcut: emitting Codex `systemMessage` only and forgetting Gemini `hookSpecificOutput.additionalContext`.
- Potential shortcut: using `echo` debugging in shell templates, corrupting JSON stdout.
- Assumption to verify: hook command path should use `$GEMINI_PROJECT_DIR` or a relative project path in project installs.

## Acceptance Criteria

- Covers: "Silent failure - hook stdout is not valid JSON"
- Covers: "Silent failure - bootstrap context is displayed but not injected"
- Covers: "Degradation - bootstrap skill file cannot be read by hook"
