# Kickoff: Auto Version Release

## Problem Statement

Samsara needs GitHub Actions release automation where `.claude-plugin/marketplace.json` is the release source of truth. When `metadata.version` changes, CI should prove that `.claude-plugin/plugin.json` and `pyproject.toml` carry the same version, then create exactly one matching Git tag and GitHub Release for that commit. The workflow must be idempotent: an existing `vX.Y.Z` tag/release should not be recreated, and version drift should fail before any tag is pushed.

## Evidence

- Current repo has three version fields and all are `0.9.0`: `.claude-plugin/marketplace.json` `metadata.version`, `.claude-plugin/plugin.json` `version`, and `pyproject.toml` `[project].version`.
- There is no existing `.github/workflows/` release workflow. `.github/` currently contains templates only.
- GitHub Actions workflow syntax supports `push` branch/tag filtering and workflow-level/job-level `permissions`. Source: https://docs.github.com/en/actions/writing-workflows/workflow-syntax-for-github-actions
- GitHub documents that `contents: write` allows repository content operations including release creation. Source: https://docs.github.com/en/actions/writing-workflows/workflow-syntax-for-github-actions
- `GITHUB_TOKEN` is the standard token for workflow authentication, and GitHub recommends granting only required permissions. Source: https://docs.github.com/en/actions/configuring-and-managing-workflows/authenticating-with-the-github_token
- GitHub CLI is preinstalled on GitHub-hosted runners and requires `GH_TOKEN` in workflow steps. Source: https://docs.github.com/actions/using-workflows/using-github-cli-in-workflows
- `gh release create` supports creating a release from a tag, generated notes, target commit selection, and `--verify-tag`. Source: https://cli.github.com/manual/gh_release_create
- `actions/checkout@v6` is current, supports authenticated git commands, and documents `fetch-depth: 0` for all history/tags. Source: https://github.com/actions/checkout
- `astral-sh/setup-uv` is the native action for installing `uv`, with cache support and optional Python version management. Source: https://github.com/astral-sh/setup-uv

## Risk of Inaction

Manual version bumps and manual release tags will drift. The most likely rot pattern is a GitHub release named after one version while the Claude plugin marketplace metadata or Python package metadata advertises another. That breaks install/update expectations, makes debugging user reports harder, and forces maintainers to reconstruct which commit actually shipped.

## Scope

### Must-Have (with death conditions)

- **Marketplace version as source of truth** — Read `.claude-plugin/marketplace.json` `metadata.version` and derive the release tag as `v<version>`. Death condition: if the marketplace schema stops using a stable `metadata.version`, move the source of truth to the registry-required field instead.
- **Version sync validation** — Fail CI when `.claude-plugin/plugin.json` `version` or `pyproject.toml` `[project].version` differs from marketplace `metadata.version`. Death condition: if the project adopts dynamic Python versioning, replace the pyproject equality check with the dynamic version provider check.
- **Local sync command or script** — Provide a deterministic way to update `plugin.json` and `pyproject.toml` from marketplace version before committing. Death condition: if maintainers intentionally want independent package/plugin versions, remove this and split release lanes.
- **Release workflow on trusted refs only** — Run release creation on `push` to `main` and `workflow_dispatch`, never on PRs from forks. Death condition: if release approval must be human-gated, make the workflow manual-only or require a protected environment.
- **Idempotent tag/release creation** — If `v<version>` already exists, the workflow should no-op or fail clearly before creating duplicate release state. Death condition: if tags can be moved after publication, stop automation until tag immutability/protection is decided.
- **Validation before mutation** — Run version sync checks and the repo's normal `uv`/`pytest`/`pre-commit` validation before pushing a tag or creating a release. Death condition: if full validation is too slow for every version bump, keep a fast release gate and move the full suite to required branch protection.
- **Least-privilege token permissions** — Use `contents: write` only in the release job that pushes tags/releases; keep validation jobs read-only. Death condition: if org policy disables `GITHUB_TOKEN` write permissions, switch to a scoped GitHub App token rather than broad PAT usage.

### Nice-to-Have

- Infer prerelease status from semver suffixes like `1.0.0-rc.1`.
- Attach built package artifacts from `uv build` to the GitHub Release.
- Generate release notes from PR labels or a changelog section instead of only GitHub auto-generated notes.
- Add a pre-commit hook that rejects version drift before CI.

### Explicitly Out of Scope

- Publishing to PyPI or any package registry.
- Automatically deciding the next semantic version.
- CI self-committing version bumps back to `main`.
- Rewriting existing issue/PR templates under `.github/`.
- Retagging or deleting already published releases.

## North Star

```yaml
metric:
  name: "version-bump release correctness"
  definition: "Percentage of merged marketplace version bumps on main that produce exactly one matching v<version> Git tag and GitHub Release, with pyproject/plugin metadata equal to marketplace metadata"
  current: 0%
  target: 100%
  invalidation_condition: "If marketplace version is not the artifact consumers actually use for install/update decisions, this metric optimizes the wrong version source"
  corruption_signature: "A release exists for v<version>, but at least one committed metadata file or installed plugin reports a different version"

sub_metrics:
  - name: "version sync gate pass rate"
    current: 0%
    target: 100%
    proxy_confidence: high
    decoupling_detection: "Sync gate passes while manual inspection shows marketplace, plugin, and pyproject versions differ"
  - name: "release idempotency"
    current: 0%
    target: 100%
    proxy_confidence: high
    decoupling_detection: "Re-running the workflow for the same commit creates a second release, moves a tag, or changes release contents unexpectedly"
  - name: "trusted-ref release isolation"
    current: 0%
    target: 100%
    proxy_confidence: high
    decoupling_detection: "A PR or fork-triggered workflow can reach a step with release write credentials"
  - name: "validation-before-release coverage"
    current: 0%
    target: 100%
    proxy_confidence: medium
    decoupling_detection: "Tag/release creation succeeds even when tests, pre-commit, or version sync fail earlier in the same workflow"
```

## Stakeholders

- **Decision maker:** Roymond Liao
- **Impacted teams:** Samsara maintainers and users installing releases from GitHub or Claude plugin marketplace metadata
- **Damage recipients:** Maintainers who must debug release/version drift; users who install a release whose metadata lies; CI maintainers who inherit token permission and idempotency edge cases
