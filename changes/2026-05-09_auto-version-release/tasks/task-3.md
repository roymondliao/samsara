# Task 3: Add GitHub CI and Release Workflows

## Context

Read: `changes/2026-05-09_auto-version-release/overview.md`

The repo currently has `.github/` templates but no workflows. Add a read-only CI workflow and a trusted release workflow. The workflows must use `uv`, activate `.venv` before Python-related commands, and call the release CLI commands from Task 2.

## Files

- Create: `.github/workflows/ci.yml`
- Create: `.github/workflows/release.yml`
- Create: `tests/test_workflows/__init__.py`
- Create: `tests/test_workflows/test_github_actions.py`

## Death Test Requirements

- Test: CI workflow has read-only permissions and contains `samsara-cli release check-version`.
- Test: release workflow validation job runs before any job with `contents: write`.
- Test: release workflow does not trigger on pull requests.
- Test: release workflow checks existing remote tag/release state before creating or pushing tags.
- Test: release workflow compares an existing tag's commit SHA to `github.sha` and fails on mismatch.
- Test: both workflows include `source .venv/bin/activate` before `uv run pytest` / `uv run pre-commit`.

## Implementation Steps

- [ ] Step 1: Write static workflow contract tests using `yaml.safe_load`.
- [ ] Step 2: Run `source .venv/bin/activate` and `uv run pytest tests/test_workflows`; verify they fail.
- [ ] Step 3: Create `.github/workflows/ci.yml` with checkout, setup-uv, `uv sync --frozen`, pytest, pre-commit, and version check.
- [ ] Step 4: Create `.github/workflows/release.yml` with validation, tag derivation, remote tag/release checks, tag push, and `gh release create`.
- [ ] Step 5: Keep `contents: write` scoped only to the release job.
- [ ] Step 6: Ensure `GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}` is set for `gh` commands.
- [ ] Step 7: Run `source .venv/bin/activate` and `uv run pytest tests/test_workflows`; verify all pass.
- [ ] Step 8: Run release CLI tests to verify workflow command names are real.
- [ ] Step 9: Write scar report.
- [ ] Step 10: Commit.

## Expected Scar Report Items

- Potential shortcut: giving workflow-level `contents: write` to every job.
- Potential shortcut: relying on `gh release create` to auto-create tags instead of explicitly controlling the tag.
- Potential shortcut: skipping existing-tag SHA comparison.
- Potential shortcut: using raw Python or `python -m pytest` in workflows, violating project command rules.
- Assumption to verify: GitHub-hosted runners have `gh` available and `astral-sh/setup-uv` can install `uv`.

## Acceptance Criteria

- Covers: "Silent failure - workflow omits version gate"
- Covers: "Silent failure - existing tag points at different commit"
- Covers: "Degradation - release already exists"
- Covers: "Degradation - tag exists but release is missing"
- Covers: "Success - main branch release creates tag and release"
