# Task 5: Implement Gemini project and global installer merge behavior

## Context

Read: `changes/2026-05-09_gemini-cli-integration/overview.md`

Installer behavior is currently Codex-oriented: project install merges native trees, global install modifies TOML config. Gemini requires JSON settings merge for both project and global scopes, and global install must back up `~/.gemini/settings.json`.

## Files

- Modify: `samsara_cli/installer/install.py`
- Modify: `tests/test_installer/test_install.py`
- Modify: `tests/test_installer/test_install_death.py`
- Create: `tests/test_installer/test_install_gemini.py`

## Death Test Requirements

- Test: project install with existing `.gemini/settings.json` preserves unrelated settings and hooks.
- Test: repeated project install creates exactly one samsara SessionStart hook.
- Test: invalid existing settings JSON aborts install instead of overwriting.
- Test: global install creates `settings.json.bak` before modifying settings.
- Test: global install with patched `HOME` never writes to real `Path.home()/.gemini`.
- Test: partial or failed settings merge does not return "Installation complete" semantics.

## Implementation Steps

- [ ] Step 1: Write Gemini installer death tests.
- [ ] Step 2: Run death tests with `source .venv/bin/activate` and `uv run pytest <test files>`; verify they fail.
- [ ] Step 3: Write happy-path project/global install tests.
- [ ] Step 4: Run happy-path tests; verify they fail.
- [ ] Step 5: Add JSON settings merge helper for `settings.json`.
- [ ] Step 6: Make global config update dispatch by config file suffix or platform config.
- [ ] Step 7: Preserve Codex TOML behavior and existing Codex tests.
- [ ] Step 8: Run installer tests; verify they pass.
- [ ] Step 9: Write scar report.
- [ ] Step 10: Commit.

## Expected Scar Report Items

- Potential shortcut: generic JSON merge that appends duplicate hooks because object equality misses command normalization.
- Potential shortcut: backing up settings after writing rather than before mutation.
- Assumption to verify: replacing `~` with patched `HOME` remains sufficient for global path resolution.

## Acceptance Criteria

- Covers: "Silent failure - existing Gemini settings overwritten during project install"
- Covers: "Silent failure - repeated install duplicates SessionStart hook"
- Covers: "Unknown outcome - partial install copy"
- Covers: "Success - project install is local and idempotent"
- Covers: "Success - global install writes only patched HOME"
