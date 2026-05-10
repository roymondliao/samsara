# Problem Autopsy: Auto Version Release

## original_statement

「我要弄一個自動打 tags & release 的 github action CI/CD，而 tags 會跟著 .claude-plugin/marketplace.json 的 version 走，所以連同 pyproject.toml and .claude-plugin/plugin.json 的 version 也要 sync。」

## reframed_statement

Add a GitHub Actions release lane where `.claude-plugin/marketplace.json` `metadata.version` is the authoritative release version. CI should verify or provide tooling to synchronize `.claude-plugin/plugin.json` and `pyproject.toml` to that version, then create the matching `v<version>` Git tag and GitHub Release from the validated commit. The automation should avoid self-mutating release commits unless explicitly requested, because CI-generated version commits can create confusing loops and unaudited release state.

## translation_delta

```yaml
translation_delta:
  - original: "自動打 tags & release"
    reframed: "Create exactly one Git tag and GitHub Release from a validated main-branch commit"
    delta: "Automation must define idempotency and trusted-ref boundaries, not just call git tag and gh release."

  - original: "tags 會跟著 .claude-plugin/marketplace.json 的 version 走"
    reframed: "marketplace metadata.version is the release source of truth and maps to v<version>"
    delta: "The tag prefix and exact JSON path need to be explicit, otherwise v0.9.0 vs 0.9.0 can drift."

  - original: "pyproject.toml and .claude-plugin/plugin.json 的 version 也要 sync"
    reframed: "CI should fail on drift, with a local or workflow-dispatch sync path available before release"
    delta: "Sync can mean auto-editing files or enforcing equality. Auto-editing inside release CI is higher risk because it mutates the commit being released."

  - original: "github action CI/CD"
    reframed: "Separate read-only validation from write-capable release mutation"
    delta: "The workflow needs least-privilege permissions; validation and release are different trust surfaces."
```

## kill_conditions

```yaml
kill_conditions:
  - condition: "No installer, marketplace, or user workflow consumes GitHub tags/releases as the distribution boundary"
    rationale: "Automating releases that nobody consumes adds maintenance and security surface without reducing user pain."

  - condition: "The desired behavior requires CI to silently rewrite version files and release that generated commit"
    rationale: "Self-mutating release workflows can create loops, hide unreviewed changes, and make the released commit differ from the merged commit."

  - condition: "The authoritative version should actually be the Python package version, not marketplace metadata"
    rationale: "If package consumers are the primary release audience, using marketplace metadata as source of truth will optimize the wrong artifact."

  - condition: "Repository or organization policy cannot grant safe release write permissions to GitHub Actions"
    rationale: "Without controlled `contents: write` or an equivalent scoped GitHub App token, release automation either fails or requires over-broad credentials."
```

## damage_recipients

```yaml
damage_recipients:
  - who: "Maintainers"
    cost: "They must maintain version parsing, semver policy, tag idempotency, and recovery behavior for failed releases."

  - who: "Release consumers"
    cost: "If the release tag and embedded metadata disagree, users may install or report bugs against the wrong version."

  - who: "CI security posture"
    cost: "A workflow that can push tags and create releases needs elevated repository content permissions and careful trigger restrictions."

  - who: "Future package publishing work"
    cost: "A GitHub-only release lane can become a constraint if PyPI or another registry later needs different artifact/version rules."
```

## observable_done_state

Changing `.claude-plugin/marketplace.json` `metadata.version` to a new semver and keeping `.claude-plugin/plugin.json` plus `pyproject.toml` synchronized results in a successful main-branch workflow that creates `v<version>` and a GitHub Release for the same commit. If either secondary version differs, CI fails before any tag or release is created. Re-running the workflow for an already released version does not move tags, duplicate releases, or mutate version files.
