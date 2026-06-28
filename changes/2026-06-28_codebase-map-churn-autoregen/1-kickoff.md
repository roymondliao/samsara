# Kickoff: codebase-map-churn-autoregen

## Problem Statement

Samsara's codebase-map is a navigation/preview aid (live codebase is the source of truth; on conflict live wins). The map decays as the codebase changes, but the current freshness mechanism is both **dishonest** and **ineffective**: `hooks/check-codebase-map` judges staleness by file mtime against a 7-day wall-clock threshold, so a `touch` or `git checkout` falsely refreshes it, and wall-clock days is the wrong proxy (an idle repo looks stale, a heavily-churned repo can look fresh). Worse, even when staleness is detected, the only action is a session-start reminder that nobody acts on — the map here has not been regenerated for 65 days across 77 commits / 210 changed source files. The real pain is not "detection is imprecise"; it is "manual regeneration never happens." The fix is to retire the wall-clock proxy, anchor staleness to **code churn since the map's `last_updated`**, and make regeneration **automatic** at the moments a fresh map matters — with honest failure when auto-regeneration cannot complete.

## Evidence

- `hooks/check-codebase-map:14` computes staleness from `stat` mtime, not the map's own `last_updated` field — `touch`/checkout silently refresh it.
- `.samsara/codebase-map.yaml:2-3`: `last_updated: "2026-04-23"`, `staleness_threshold_days: 7`. Today is 2026-06-28.
- Churn since `last_updated` (measured): **77 commits, 210 changed source/config files** (excluding `changes/`, `docs/`, `bugfix/`). The map is deeply stale by churn, not just by calendar.
- The map has been flagged stale at session start for ~65 days with no regeneration — direct evidence that the warning-only mechanism does not drive action.
- `skills/pre-thinking/SKILL.md` Atomic Context Boundary already treats the map as derived context and live as truth ("if the map and live artifacts disagree, live artifacts win and the drift must be surfaced") — but nothing executes this; a stale map silently feeds misleading derived context.

## Risk of Inaction

The map keeps decaying and keeps being presented as a usable preview while diverging further from reality. Because live wins, this does not cause silent *correctness* failures — it causes silent *navigation* failures: agents and humans use a map that points at a codebase that no longer looks like that, wasting orientation time and eroding trust in the map until it is ignored entirely (at which point the mechanism's existence is pure cost with no benefit). The dishonest mtime signal also means any future "is the map fresh?" check built on the current hook inherits a proxy that can be gamed by an unrelated `touch`.

## Scope

### Must-Have (with death conditions)

- **Churn-based staleness signal (replace wall-clock days)** — staleness is computed from code churn (changed source files and/or commit count) since the map's `last_updated`. Death condition: if churn computation proves unreliable in common environments (shallow clones, missing git history, detached states) more often than it helps, downgrade to a simpler explicit-age signal rather than keep a misleading churn number.
- **Hook reads `last_updated`, not mtime** — `hooks/check-codebase-map` derives age/churn from the map's `last_updated` field and git, never from file mtime; `touch`/checkout must not affect freshness. Death condition: if the codebase-map skill ever stops writing `last_updated`, this signal breaks — must be tied to the map schema as a required field.
- **Auto-regeneration at session start AND pre-thinking entry when churn over threshold** — both trigger points detect churn and regenerate when over threshold; cost is gated by "only when over threshold," not every session. Death condition: if auto-regen cost/noise at these trigger points outweighs the navigation benefit (e.g., users routinely disable it), downgrade to warn-only at that trigger point.
- **Fail-honest regeneration** — when auto-regeneration cannot complete (skill unavailable, no git, churn uncomputable), the mechanism must mark the map explicitly stale and record why it failed; it must NOT silently reuse the old map as if fresh. Death condition: none — this is the floor that justifies the whole change.

### Nice-to-Have
- Throttle/debounce so the same over-threshold state does not retrigger regeneration repeatedly within one working window.
- Configurable churn threshold (with a sane default) rather than a hardcoded constant.

### Explicitly Out of Scope
- Making the map authoritative — it stays a preview aid; live codebase remains the source of truth.
- Per-file-type churn classification (deciding which file changes "really" invalidate the map) — pursue only "coarse but honest," not precise.
- Introducing new runtime dependencies.
- Breaking changes to the existing map schema that would invalidate maps already in the field (the `last_updated` field already exists and is reused).

## North Star

```yaml
metric:
  name: "map churn-at-use"
  definition: "Code churn (changed source files since the map's last_updated, excluding changes/ docs/ bugfix/) measured at the moment a workflow stage consumes the map (session start or pre-thinking Atomic Context Boundary)"
  current: 210            # changed source files since 2026-04-23
  target: "below the configured churn threshold at point of use (e.g. < 30 changed files)"
  invalidation_condition: "If the 'live codebase wins' safety net makes map accuracy irrelevant to actual outcomes, then churn-at-use is a vanity metric and the effort should stop — the map would be pure navigation sugar not worth automating"
  corruption_signature: "last_updated gets bumped (map looks freshly regenerated) but the map content did not actually change to reflect the churn, or a regeneration failed yet the timestamp advanced — freshness gamed without real refresh"

sub_metrics:
  - name: "manual-regen dependency"
    current: "100% (only human-triggered regen exists today)"
    target: "auto-triggered regen becomes the dominant path; human no longer required for routine freshness"
    proxy_confidence: high
    decoupling_detection: "Count regen events by trigger source (auto vs human); if auto count stays 0 while churn-at-use stays high, automation is not actually firing"
  - name: "regen-failure honesty"
    current: "n/a (no auto-regen yet)"
    target: "100% of failed auto-regens are marked stale + reason recorded, 0% silently reuse old map"
    proxy_confidence: high
    decoupling_detection: "A regen failure that leaves the map presented as fresh (no stale mark, no recorded reason) is a decoupling — detect via a death test that forces regen failure and asserts the stale mark + reason exist"
```

## Stakeholders
- **Decision maker:** roymond (user) — confirmed map stays, mechanism is important
- **Impacted teams:** all Samsara users (the hook runs at session start in every project that installs it)
- **Damage recipients:** the session/user at the auto-regen trigger point (pays token+time cost of regeneration when over threshold); CI/automation environments if the hook triggers regen unattended; future maintainers of the now-more-complex (auto vs manual) freshness logic
