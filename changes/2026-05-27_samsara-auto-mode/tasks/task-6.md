# Task 6: Bump release version to 0.11.0

## Context

Read: `changes/2026-05-27_samsara-auto-mode/overview.md`

After auto mode implementation, documentation, and validation are complete, prepare the release metadata for `0.11.0`. The marketplace metadata is the version source of truth; secondary version files must be synchronized through the existing release tooling.

## Files

- Modify: `.claude-plugin/marketplace.json`
- Modify: `.claude-plugin/plugin.json`
- Modify: `pyproject.toml`
- Modify: `uv.lock`
- Test: `tests/test_cli/test_release_commands.py`
- Test: `tests/test_release/test_version_metadata.py`
- Test: `tests/test_release/test_version_metadata_death.py`

## Death Test Requirements

- Test: release metadata must fail if marketplace, plugin, pyproject, or lockfile versions drift.
- Test: release tag output must be `v0.11.0`, not `v0.10.0`.
- Test: CLI version output must report `samsara-cli 0.11.0` after the package metadata is synchronized.

## Implementation Steps

- [ ] Step 1: Confirm current synchronized version is `0.10.0` with `source .venv/bin/activate` and `uv run samsara-cli release check-version`.
- [ ] Step 2: Update `.claude-plugin/marketplace.json` `metadata.version` to `0.11.0`.
- [ ] Step 3: Run `source .venv/bin/activate` and `uv run samsara-cli release sync-version` to synchronize `.claude-plugin/plugin.json`, `pyproject.toml`, and `uv.lock`.
- [ ] Step 4: Run `source .venv/bin/activate` and `uv run samsara-cli release check-version`.
- [ ] Step 5: Run `source .venv/bin/activate` and `uv run samsara-cli release print-tag` and verify it prints `v0.11.0`.
- [ ] Step 6: Run targeted release tests with `source .venv/bin/activate` and `uv run pytest tests/test_cli/test_release_commands.py tests/test_release/test_version_metadata.py tests/test_release/test_version_metadata_death.py`.
- [ ] Step 7: Run final validation from task 5 again if the version bump changes lockfile or package metadata in a way that affects install/conversion tests.
- [ ] Step 8: Write scar report at `changes/2026-05-27_samsara-auto-mode/scar-reports/task-6-scar.yaml`.
- [ ] Step 9: Do not commit from the subagent; report back to the main agent.

## Expected Scar Report Items

- Potential shortcut: manually editing secondary version files instead of using `release sync-version`.
- Potential shortcut: bumping `pyproject.toml` while leaving marketplace metadata at `0.10.0`.
- Assumption to verify: `uv.lock` reflects the package version after release synchronization.

## Acceptance Criteria

- Covers: "Success - release metadata bumped to 0.11.0"
