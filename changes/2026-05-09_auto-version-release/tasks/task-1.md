# Task 1: Add Release Version Metadata Core

## Context

Read: `changes/2026-05-09_auto-version-release/overview.md`

The release source of truth is `.claude-plugin/marketplace.json` `metadata.version`. `.claude-plugin/plugin.json` `version` and `pyproject.toml` `[project].version` must match it. This task creates the tested Python core only; CLI and GitHub Actions are separate tasks.

## Files

- Create: `samsara_cli/release/__init__.py`
- Create: `samsara_cli/release/version_metadata.py`
- Create: `tests/test_release/__init__.py`
- Create: `tests/test_release/test_version_metadata.py`
- Create: `tests/test_release/test_version_metadata_death.py`

## Death Test Requirements

- Test: marketplace version differs from plugin and pyproject versions; `check` reports every mismatched file/field and returns failure.
- Test: missing `metadata.version`, missing `version`, or missing `[project].version` is a failure, not `None` or `"unknown"` success.
- Test: invalid version strings such as `latest`, `v1.2.3`, or empty string fail before tag derivation.
- Test: simulated write failure during sync reports partial-write risk and does not claim success.
- Test: malformed JSON/TOML exits through a typed failure path with file path context.

## Implementation Steps

- [ ] Step 1: Write death tests for drift, missing fields, invalid semver, malformed files, and partial writes.
- [ ] Step 2: Run death tests with `source .venv/bin/activate` and `uv run pytest tests/test_release`; verify they fail.
- [ ] Step 3: Write happy-path tests for load, equality check, tag derivation, dry-run sync, and real sync in a temp repo.
- [ ] Step 4: Run new tests; verify they fail.
- [ ] Step 5: Implement `VersionMetadata`, version validation, comparison result objects, tag derivation, and sync writing.
- [ ] Step 6: Use `tomllib` for reading TOML and `tomli_w` for writing TOML.
- [ ] Step 7: Run `source .venv/bin/activate` and `uv run pytest tests/test_release`; verify all pass.
- [ ] Step 8: Write scar report.
- [ ] Step 9: Commit.

## Expected Scar Report Items

- Potential shortcut: parsing TOML or JSON with ad hoc string replacement instead of structured parsers.
- Potential shortcut: stopping at the first mismatch instead of reporting all drift in one run.
- Potential shortcut: accepting `v1.2.3` inside metadata and producing `vv1.2.3`.
- Assumption to verify: semver support should allow prerelease suffixes like `1.0.0-rc.1` but reject a leading `v`.

## Acceptance Criteria

- Covers: "Silent failure - version drift would publish lying metadata"
- Covers: "Unknown outcome - partial version sync write"
- Covers: "Success - local sync updates secondary metadata"
