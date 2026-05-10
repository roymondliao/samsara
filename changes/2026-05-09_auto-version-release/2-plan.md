# Technical Plan: Auto Version Release

## Planning Pre-thinking: Information Assumptions

To write this plan, I am assuming:
- Research established `.claude-plugin/marketplace.json` `metadata.version` as the source of truth for releases.
- Research established release tags use the `v<version>` format, for example `0.9.0` maps to `v0.9.0`.
- Research established `.claude-plugin/plugin.json` `version` and `pyproject.toml` `[project].version` must equal marketplace `metadata.version`.
- Research established release automation must fail before mutation when versions drift.
- Research established CI must not silently self-commit version updates during release.
- The repo already uses Typer for `samsara-cli`, pytest for tests, `uv` for dependency execution, and GitHub Actions-compatible `.github/` structure.

Gaps I cannot resolve from Research:
- None.

Uncertainties (I cannot determine if more information is needed):
- None. Release note format and artifact upload depth are implementation choices already marked nice-to-have or out of scope.

## Technical Specification

### Architecture

Add a small release metadata subsystem under `samsara_cli/release/`. It owns all parsing, comparison, sync, and tag derivation logic for the three version files:

```text
.claude-plugin/marketplace.json     metadata.version  source of truth
.claude-plugin/plugin.json          version           must match
pyproject.toml                      project.version   must match
```

GitHub Actions must call the same CLI commands a maintainer can run locally:

```bash
samsara-cli release check-version
samsara-cli release sync-version
samsara-cli release print-tag
```

The release workflow creates tags/releases only after version sync, tests, and pre-commit pass. The workflow must use `contents: write` only for the release job. Read-only CI should validate PRs and pushes without release credentials.

### Interfaces

#### `VersionMetadata.load(repo_root: Path)`

Inputs:
- `repo_root`: project root containing `.claude-plugin/marketplace.json`, `.claude-plugin/plugin.json`, and `pyproject.toml`.

Outputs:
- `success`: returns marketplace, plugin, and pyproject versions plus derived tag.
- `failure`: missing file, malformed JSON/TOML, missing version field, invalid semver, or version drift.
- `unknown`: file read/parsing result cannot be determined. Unknown must be represented as an error state and must never fall through to success.

#### `samsara-cli release check-version`

Inputs:
- `--root PATH`, default current working directory.
- `--json`, optional machine-readable output.

Outputs:
- `success`: exits `0`, prints the synchronized version and tag.
- `failure`: exits non-zero with all mismatched fields listed.
- `unknown`: exits non-zero when any source file cannot be read or parsed.

#### `samsara-cli release sync-version`

Inputs:
- `--root PATH`, default current working directory.
- `--check`, optional dry-run mode that reports required changes without writing.

Outputs:
- `success`: updates plugin and pyproject versions to marketplace version, preserving valid JSON/TOML structure.
- `failure`: exits non-zero if marketplace version is absent/invalid or writes cannot be completed.
- `unknown`: if one file is updated but another write fails, the command must exit non-zero and report partial-write risk.

#### `samsara-cli release print-tag`

Inputs:
- `--root PATH`, default current working directory.

Outputs:
- `success`: prints exactly `v<metadata.version>` to stdout for GitHub Actions.
- `failure`: exits non-zero if versions are invalid or drifted.
- `unknown`: exits non-zero if version state cannot be determined.

### GitHub Actions Design

Create two workflows:

```text
.github/workflows/ci.yml
.github/workflows/release.yml
```

`ci.yml`:
- triggers on pull requests and pushes to `main`
- uses read-only permissions
- checks out code
- installs `uv`
- runs `uv sync --frozen`
- runs `source .venv/bin/activate` before Python-related commands
- runs `uv run pytest`
- runs `uv run pre-commit run --all-files`
- runs `uv run samsara-cli release check-version`

`release.yml`:
- triggers on push to `main` and `workflow_dispatch`
- uses a read-only validation job first
- release job depends on validation and has `permissions.contents: write`
- checks whether `v<version>` already exists remotely
- if tag exists and GitHub Release exists, no-ops with clear output
- if tag exists but release is missing, creates only the release from the existing tag
- if tag does not exist, creates an annotated tag at `github.sha`, pushes it, then creates the GitHub Release
- uses `gh release create <tag> --verify-tag --target "$GITHUB_SHA" --generate-notes`

### I/O States

Every release operation must report one of three states:

| Operation | Success | Failure | Unknown |
| --- | --- | --- | --- |
| Version load | all versions parsed and valid | known mismatch or malformed file | unreadable file or indeterminate parse/write state |
| Version sync | secondary files updated or already equal | invalid source version or write failure | partial write occurred |
| Tag lookup | remote tag known present/absent | git command returns hard error | network/auth timeout or ambiguous ref |
| Release create | release exists or was created for tag | `gh` reports known failure | API result cannot confirm release state |

Unknown is release-blocking.

### Death Cases

| Death case | Trigger | Lie | Truth | Detection |
| --- | --- | --- | --- | --- |
| Version drift release | Marketplace says `0.10.0`, pyproject says `0.9.0` | Release tag looks correct | installed/package metadata lies | `check-version` lists every mismatched path and exits non-zero |
| Wrong tag prefix | Workflow emits `0.10.0` instead of `v0.10.0` | Release exists | consumer/tooling expects `v` tags | `print-tag` unit test and workflow test assert exact tag |
| Partial sync | plugin.json updated, pyproject write fails | command reports sync complete | repo is now inconsistent | sync command detects partial-write risk and exits non-zero |
| Duplicate release | Workflow rerun for already released version | second run succeeds | duplicate release state or tag move happened | remote tag/release checks no-op without pushing |
| Tag moved | Existing `v0.10.0` points to another commit | release job proceeds | published version no longer maps to immutable commit | workflow compares tag SHA to current SHA and fails unless release already exists |
| PR write credential exposure | Pull request from fork reaches release token | CI appears normal | untrusted code can write tags/releases | separate release workflow, trusted triggers only, job-level `contents: write` |
| Silent workflow parser drift | YAML typo disables intended command | workflow exists | version check never runs | static workflow tests parse YAML and assert required commands/permissions |

## File Map

- `samsara_cli/release/__init__.py` — release helper package exports.
- `samsara_cli/release/version_metadata.py` — version parsing, comparison, sync, and tag derivation.
- `samsara_cli/main.py` — add `release` Typer sub-app with `check-version`, `sync-version`, and `print-tag`.
- `tests/test_release/test_version_metadata.py` — happy-path version parsing/sync tests.
- `tests/test_release/test_version_metadata_death.py` — drift, missing field, invalid semver, partial write death tests.
- `tests/test_cli/test_release_commands.py` — release CLI command tests.
- `tests/test_cli/test_release_commands_death.py` — release CLI death tests.
- `.github/workflows/ci.yml` — read-only validation workflow.
- `.github/workflows/release.yml` — trusted release/tag workflow.
- `tests/test_workflows/test_github_actions.py` — static workflow contract tests.
- `README.md` — update current version and release process notes if still stale.

## Validation Plan

All commands must follow project rules:

```bash
source .venv/bin/activate
uv run pytest tests/test_release tests/test_cli tests/test_workflows
uv run pytest
uv run pre-commit run --all-files
```

Workflow behavior that depends on GitHub remote state should be covered by static contract tests and guarded shell logic in the workflow itself. Local tests must not push tags or create releases.
