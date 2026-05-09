# Task 7: Add Gemini fixture snapshots and pipeline tests

## Context

Read: `changes/2026-05-09_gemini-cli-integration/overview.md`

The existing integration suite proves Codex conversion against committed fixtures and snapshots. Gemini needs the same structural pipeline coverage so converter regressions are visible before runtime smoke tests.

## Files

- Create: `tests/fixtures/expected/gemini-cli/`
- Modify: `tests/integration/test_pipeline.py`
- Modify: `tests/integration/test_snapshot.py`
- Modify: `tests/integration/test_format_validation.py`
- Modify: `tests/fixtures/source/` only if the fixture lacks a source pattern needed to exercise Gemini conversion rules.

## Death Test Requirements

- Test: Gemini pipeline fails if `.gemini/agents/*.md` is missing.
- Test: Gemini pipeline fails if `.gemini/skills` has fewer skill dirs than source.
- Test: Gemini pipeline fails if `.gemini/settings.json` is missing or invalid JSON.
- Test: snapshot comparison fails on missing, extra, or changed Gemini files.
- Test: snapshot update writes actual Gemini output and does not leave stale files.

## Implementation Steps

- [ ] Step 1: Write Gemini pipeline death tests.
- [ ] Step 2: Run death tests with `source .venv/bin/activate` and `uv run pytest <test files>`; verify they fail.
- [ ] Step 3: Extend snapshot helpers to handle platform-specific expected directories.
- [ ] Step 4: Generate Gemini expected output from the fixture.
- [ ] Step 5: Commit `tests/fixtures/expected/gemini-cli/` snapshots.
- [ ] Step 6: Run Codex and Gemini integration pipeline/snapshot tests; verify both pass.
- [ ] Step 7: Write scar report.
- [ ] Step 8: Commit.

## Expected Scar Report Items

- Potential shortcut: reusing Codex expected path by accident, so Gemini snapshots compare against wrong files.
- Potential shortcut: snapshots normalize too much and hide real Gemini path regressions.
- Assumption to verify: fixture source contains enough skills/agents/hooks to exercise Gemini-specific conversion.

## Acceptance Criteria

- Covers: "Success - convert produces Gemini native output"
- Covers: "Success - Codex regression suite still passes"
