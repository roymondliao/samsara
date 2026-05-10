# Task 4: Document Release Process and Stale Version Cleanup

## Context

Read: `changes/2026-05-09_auto-version-release/overview.md`

After the CLI and workflows exist, the maintainer path must be visible. `README.md` currently has a stale current version section, so update it to reflect the synchronized metadata and document the release commands without adding a package registry publishing promise.

## Files

- Modify: `README.md`
- Modify: `README.zh-TW.md`
- Modify: `changes/2026-05-09_auto-version-release/overview.md`
- Modify: `changes/2026-05-09_auto-version-release/index.yaml`

## Death Test Requirements

- Test: documentation does not tell maintainers to edit `pyproject.toml` or `.claude-plugin/plugin.json` as source of truth.
- Test: documentation includes `samsara-cli release sync-version` and `samsara-cli release check-version`.
- Test: README current version matches `.claude-plugin/marketplace.json` `metadata.version`.

## Implementation Steps

- [ ] Step 1: Write or extend tests that inspect README release/version text.
- [ ] Step 2: Run `source .venv/bin/activate` and `uv run pytest <new/readme test>`; verify it fails if docs are stale.
- [ ] Step 3: Update English and Traditional Chinese README release instructions.
- [ ] Step 4: Update current version text from stale `0.5.0` to the synchronized metadata version.
- [ ] Step 5: Update planning index status only if implementation has completed.
- [ ] Step 6: Run `source .venv/bin/activate` and `uv run pytest <new/readme test>`; verify it passes.
- [ ] Step 7: Run `source .venv/bin/activate` and `uv run pre-commit run --all-files`.
- [ ] Step 8: Write scar report.
- [ ] Step 9: Commit.

## Expected Scar Report Items

- Potential shortcut: documenting manual edits to three files instead of source-of-truth plus sync.
- Potential shortcut: promising PyPI/package publishing, which is out of scope.
- Potential shortcut: updating only English README and leaving zh-TW stale.
- Assumption to verify: README version text should be a human-facing current version, not an independent source of truth.

## Acceptance Criteria

- Covers: "Success - local sync updates secondary metadata"
