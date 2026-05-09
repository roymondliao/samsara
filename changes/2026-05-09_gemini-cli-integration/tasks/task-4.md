# Task 4: Make engine and target validator platform-aware

## Context

Read: `changes/2026-05-09_gemini-cli-integration/overview.md`

The current target validator has Codex-native assumptions around `.agents/skills`, `.codex/agents`, and TOML agent validation. Gemini needs `.gemini/skills`, `.gemini/agents/*.md`, and `.gemini/settings.json` validation without weakening Codex checks.

## Files

- Modify: `samsara_cli/converter/engine.py`
- Modify: `samsara_cli/validators/target.py`
- Modify: `samsara_cli/main.py`
- Create: `tests/test_validators/test_target_gemini.py`
- Modify: `tests/test_validators/test_target.py`
- Modify: `tests/test_validators/test_target_death.py`
- Modify: `tests/test_cli/test_main.py`
- Modify: `tests/test_cli/test_main_death.py`

## Death Test Requirements

- Test: Gemini validation fails if skills are under `.agents/skills` instead of `.gemini/skills`.
- Test: Gemini validation fails if agents are TOML or markdown without required frontmatter.
- Test: Gemini validation fails if `.gemini/settings.json` is invalid JSON or lacks `hooks.SessionStart`.
- Test: source patterns `invoke \`samsara:X\`` and `subagent_type:` fail validation before output is committed.
- Test: Codex TOML validation still runs for Codex output.

## Implementation Steps

- [ ] Step 1: Write Gemini target validator death tests.
- [ ] Step 2: Run validator death tests with `source .venv/bin/activate` and `uv run pytest <test files>`; verify they fail.
- [ ] Step 3: Write happy-path validation tests for minimal Gemini output.
- [ ] Step 4: Run happy-path tests; verify they fail.
- [ ] Step 5: Add a platform parameter or platform config to `TargetValidator.validate`.
- [ ] Step 6: Update engine and CLI validation calls to pass platform.
- [ ] Step 7: Keep default behavior backward-compatible for existing tests where practical.
- [ ] Step 8: Run validator, engine, and CLI tests for Codex and Gemini; verify they pass.
- [ ] Step 9: Write scar report.
- [ ] Step 10: Commit.

## Expected Scar Report Items

- Potential shortcut: adding Gemini checks while silently skipping Codex TOML parse checks.
- Potential shortcut: validating only that files exist, not that frontmatter/settings schema are loadable.
- Assumption to verify: all generated Gemini markdown agents can be parsed with a simple delimiter-based frontmatter parser.

## Acceptance Criteria

- Covers: "Silent failure - output uses .agents/skills alias"
- Covers: "Silent failure - Gemini agent output uses wrong format"
- Covers: "Silent failure - unconverted source syntax leaks into Gemini output"
- Covers: "Success - convert produces Gemini native output"
