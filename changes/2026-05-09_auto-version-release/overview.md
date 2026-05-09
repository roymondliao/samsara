# Overview: Auto Version Release

## Goal

Automate GitHub tagging and releases from `.claude-plugin/marketplace.json` `metadata.version`, while keeping `.claude-plugin/plugin.json` and `pyproject.toml` synchronized.

## Architecture

Release/version logic lives in `samsara_cli/release/version_metadata.py` and is exposed through `samsara-cli release` commands. GitHub Actions call those commands instead of parsing JSON/TOML directly in shell. CI stays read-only; only the release job gets `contents: write` after validation succeeds.

## Tech Stack

Python 3.14, Typer, pytest, `tomllib`, `tomli-w`, GitHub Actions, GitHub CLI, `uv`, pre-commit.

## Key Decisions

- Marketplace metadata is source of truth: the tag follows `.claude-plugin/marketplace.json` `metadata.version`.
- Tags use `v<version>`: this keeps release refs distinct from raw semver strings.
- Release CI does not self-commit version files: drift fails before mutation; maintainers run sync before commit.
- Version parsing is centralized in Python: workflow YAML should call tested CLI commands.
- `contents: write` is release-job only: PR/push validation does not receive release mutation permissions.

## Death Cases Summary

1. Version drift creates a correct-looking tag but lying package/plugin metadata.
2. Rerunning release moves an existing tag or creates duplicate release state.
3. Workflow YAML exists but silently skips version validation or grants write permissions too early.

## File Map

- `samsara_cli/release/version_metadata.py` — parse, compare, sync, and derive release tag.
- `samsara_cli/main.py` — expose release subcommands.
- `.github/workflows/ci.yml` — read-only validation.
- `.github/workflows/release.yml` — trusted tag/release automation.
- `tests/test_release/` — version metadata tests.
- `tests/test_cli/test_release_commands*.py` — CLI command tests.
- `tests/test_workflows/test_github_actions.py` — static workflow contract tests.
- `README.md` — release process/current version cleanup.
