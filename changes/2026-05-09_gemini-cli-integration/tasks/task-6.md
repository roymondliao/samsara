# Task 6: Wire CLI commands and detector coverage for gemini-cli

## Context

Read: `changes/2026-05-09_gemini-cli-integration/overview.md`

After conversion, validation, and installer behavior exist, the CLI must expose `gemini-cli` consistently through `list-platforms`, `convert`, `install`, `update`, and `validate`.

## Files

- Modify: `samsara_cli/main.py`
- Modify: `samsara_cli/installer/detect.py`
- Modify: `tests/test_cli/test_main.py`
- Modify: `tests/test_cli/test_main_death.py`
- Modify: `tests/test_installer/test_detect.py`
- Modify: `tests/test_installer/test_detect_death.py`

## Death Test Requirements

- Test: unknown platform error lists `gemini-cli` among available platforms after registration.
- Test: `samsara-cli validate --platform gemini-cli` passes platform context into target validation.
- Test: `samsara-cli install gemini-cli` aborts clearly when Gemini CLI detection returns false.
- Test: `samsara-cli update gemini-cli` uses Gemini installer path and does not fall back to Codex defaults.

## Implementation Steps

- [ ] Step 1: Write CLI/de detector death tests.
- [ ] Step 2: Run death tests with `source .venv/bin/activate` and `uv run pytest <test files>`; verify they fail.
- [ ] Step 3: Write happy-path CLI tests with patched conversion/installer calls.
- [ ] Step 4: Run happy-path tests; verify they fail if wiring is incomplete.
- [ ] Step 5: Update CLI validation call sites and detector messages.
- [ ] Step 6: Run CLI and detector tests; verify they pass.
- [ ] Step 7: Write scar report.
- [ ] Step 8: Commit.

## Expected Scar Report Items

- Potential shortcut: tests patch too much and never verify the platform argument is passed through.
- Potential shortcut: Gemini detection URL omitted, producing poor install errors.
- Assumption to verify: `gemini-cli` is the stable platform config name even though the executable is `gemini`.

## Acceptance Criteria

- Covers: "Degradation - Gemini CLI unavailable during smoke tests"
- Covers: "Success - convert produces Gemini native output"
