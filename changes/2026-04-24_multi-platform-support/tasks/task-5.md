# Task 5: Hook Converter — Script Output + hooks.json Adaptation

## Context

Read: overview.md

The hook converter handles 2 hook scripts + 1 hooks.json config. This is the most platform-specific conversion — hook output format and discovery paths differ significantly.

Source (Claude Code):
- `hooks/session-start` — bash script that outputs `hookSpecificOutput.additionalContext`
- `hooks/check-codebase-map` — bash script for codebase map check
- `hooks/hooks.json` — hook config with `SessionStart` matcher `startup|clear|compact`

Target (Codex):
- Hook script outputs `systemMessage` instead of `hookSpecificOutput.additionalContext`
- hooks.json at `.codex-plugin/hooks.json` or `~/.codex/hooks.json`
- SessionStart matchers: `startup`, `resume` (not `clear|compact`)
- Codex requires `codex_hooks = true` feature flag in config.toml

Key differences:
1. JSON output format: `{"hookSpecificOutput":{"additionalContext":"..."}}` → `{"systemMessage":"..."}`
2. Matcher values: `startup|clear|compact` → `startup|resume`
3. Hook script path references: `${CLAUDE_PLUGIN_ROOT}` → platform equivalent
4. Discovery location: plugin-internal → platform-specific path

## Files

- Create: `samsara_cli/converter/hook.py`
- Test: `tests/test_converter/test_hook.py`

## Death Test Requirements

- Test: Converted hook script must output `systemMessage` JSON — output with `hookSpecificOutput` is a silent failure (Codex ignores it)
- Test: hooks.json with incorrect matcher (`clear|compact`) for Codex must be converted — Codex doesn't recognize these values
- Test: Hook script referencing `${CLAUDE_PLUGIN_ROOT}` must be adapted — this env var doesn't exist in Codex
- Test: Hook script with special characters in bootstrap content (quotes, newlines, backslashes) must produce valid JSON after conversion

## Implementation Steps

- [ ] Step 1: Write death tests for wrong output format, wrong matchers, broken env vars
- [ ] Step 2: Run death tests — verify they fail
- [ ] Step 3: Write unit tests for JSON output transformation, matcher conversion, env var adaptation
- [ ] Step 4: Run unit tests — verify they fail
- [ ] Step 5: Implement HookConverter class:
  - `convert_script(source_script: Path, platform_config: PlatformConfig, template: Template) -> str`
  - `convert_hooks_json(source_json: Path, platform_config: PlatformConfig, template: Template) -> dict`
  - For scripts: render via hook.sh.j2, adapting output format and env vars
  - For hooks.json: render via hooks.json.j2, adapting matchers and paths
- [ ] Step 6: Run all tests — verify they pass
- [ ] Step 7: Write scar report

## Expected Scar Report Items

- Potential shortcut: `check-codebase-map` hook may reference Claude Code-specific file paths — need to verify and adapt
- Assumption to verify: Codex `systemMessage` field is rendered to the model in the same way Claude Code's `additionalContext` is (as system-level context, not user message)
- Potential shortcut: Hook script uses `bash "${CLAUDE_PLUGIN_ROOT}/hooks/session-start"` — Codex plugins may use a different env var for plugin root, or none at all

## Acceptance Criteria

- Covers: "Hook injection silent failure - feature flag not documented"
- Covers: "Success - full convert pipeline" (hook portion)
