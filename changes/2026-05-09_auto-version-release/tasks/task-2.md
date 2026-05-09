# Task 2: Expose Release Version CLI Commands

## Context

Read: `changes/2026-05-09_auto-version-release/overview.md`

The version metadata core from `samsara_cli/release/version_metadata.py` must be available through maintainer- and CI-friendly CLI commands. Existing `samsara-cli version` already prints package version, so add a `release` Typer sub-app rather than overloading that command.

## Files

- Modify: `samsara_cli/main.py`
- Create: `tests/test_cli/test_release_commands.py`
- Create: `tests/test_cli/test_release_commands_death.py`

## Death Test Requirements

- Test: `samsara-cli release check-version` exits non-zero and lists all mismatches when versions drift.
- Test: `samsara-cli release print-tag` exits non-zero instead of printing a tag when versions drift or metadata is invalid.
- Test: `samsara-cli release sync-version --check` reports required changes without writing files.
- Test: command errors do not produce Python tracebacks for expected file/parse/version failures.

## Implementation Steps

- [ ] Step 1: Write CLI death tests using `typer.testing.CliRunner` and temp repo fixtures.
- [ ] Step 2: Run `source .venv/bin/activate` and `uv run pytest tests/test_cli/test_release_commands_death.py`; verify they fail.
- [ ] Step 3: Write happy-path CLI tests for `check-version`, `sync-version`, `sync-version --check`, and `print-tag`.
- [ ] Step 4: Run new CLI tests; verify they fail.
- [ ] Step 5: Add `release` Typer sub-app to `samsara_cli/main.py`.
- [ ] Step 6: Implement stable human output and optional `--json` output for `check-version`.
- [ ] Step 7: Ensure `print-tag` writes only the tag to stdout on success.
- [ ] Step 8: Run `source .venv/bin/activate` and `uv run pytest tests/test_cli/test_release_commands.py tests/test_cli/test_release_commands_death.py`; verify all pass.
- [ ] Step 9: Write scar report.
- [ ] Step 10: Commit.

## Expected Scar Report Items

- Potential shortcut: printing Rich formatting or extra text from `print-tag`, making it unsafe for shell capture.
- Potential shortcut: hiding mismatch details behind a generic non-zero exit.
- Potential shortcut: making `sync-version` write during `--check`.
- Assumption to verify: current package `version` command remains unchanged and still reports `samsara-cli 0.9.0` until the metadata version changes.

## Acceptance Criteria

- Covers: "Silent failure - version drift would publish lying metadata"
- Covers: "Success - local sync updates secondary metadata"
