# Task 8: Add skip-safe Gemini CLI smoke tests

## Context

Read: `changes/2026-05-09_gemini-cli-integration/overview.md`

Smoke tests should verify as much Gemini runtime behavior as is safely available, but they must not fail on machines without Gemini CLI and must never modify real user Gemini configuration.

## Files

- Create: `tests/integration/test_smoke_gemini_cli.py`
- Modify: `tests/integration/test_smoke_codex.py` only if shared smoke helpers are extracted.
- Modify: `pyproject.toml` only if a new pytest marker is required.

## Death Test Requirements

- Test: smoke detection returns a boolean and skips when `gemini --version` is unavailable.
- Test: smoke conversion output is written under an isolated temp directory.
- Test: project/global install smoke setup uses patched `HOME` or temp CWD, never real `~/.gemini`.
- Test: if Gemini CLI is available, structural runtime checks verify settings JSON, skills path, agents path, and hook script executability.
- Test: any inability to inspect live Gemini skill discovery is reported as skipped/degraded, not success.

## Implementation Steps

- [ ] Step 1: Write smoke skip and isolation death tests.
- [ ] Step 2: Run smoke tests with `source .venv/bin/activate` and `uv run pytest tests/integration/test_smoke_gemini_cli.py`; verify skip behavior is explicit where Gemini is missing.
- [ ] Step 3: Add structural smoke checks on converted Gemini output.
- [ ] Step 4: Add optional live Gemini checks only when a reliable non-interactive command exists.
- [ ] Step 5: Run integration tests for Codex and Gemini smoke files.
- [ ] Step 6: Write scar report.
- [ ] Step 7: Commit.

## Expected Scar Report Items

- Potential shortcut: smoke test claims runtime discovery success based only on file existence.
- Potential shortcut: test touches real `~/.gemini/settings.json` when Gemini is installed locally.
- Assumption to verify: Gemini CLI exposes enough non-interactive commands to inspect skills/agents; if not, document as degraded coverage.

## Acceptance Criteria

- Covers: "Degradation - Gemini CLI unavailable during smoke tests"
- Covers: "Success - global install writes only patched HOME"
- Covers: "Success - Codex regression suite still passes"
