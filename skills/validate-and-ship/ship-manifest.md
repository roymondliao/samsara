# Ship Manifest — Format Guide

The ship manifest is delivered alongside the feature. It documents what was built and how it can die.

> 交付物除了功能本身，必須附帶它的傷疤。

## Format

```yaml
delivered_capability: "<what was delivered — one sentence>"

known_failure_modes:
  - mode: "<failure description>"
    severity: crash | degradation | silent_corruption
    detection: "<how it's detected — monitoring hook, log pattern, etc.>"

accepted_risks:
  - risk: "<risk description>"
    accepted_by: "<who accepted this risk — typically 'human'>"
    re_review_signal: "<observable condition that should trigger re-review — not a calendar date>"
    owner: "<who is responsible for noticing the signal and re-reviewing>"

silent_failure_surface: low | medium | high
# low: <3 known silent failure paths
# medium: 3-7 known silent failure paths
# high: >7 known silent failure paths or any unverified critical assumptions

monitoring_hooks:
  - "<what monitoring/alerting is in place for when this rots>"

kill_switch: "<how to disable this feature immediately if it starts rotting>"
```

## Rules

1. **No empty failure modes.** Every feature can fail. If `known_failure_modes` is empty, the analysis was insufficient.
2. **accepted_risks must have a re-review signal and an owner, not an expiry date.** Risk acceptance is not permanent — but no mechanism anywhere in this repo (hooks, CLI, tests, skills) has ever read or acted on an `expires` date; a time-driven re-review promise is an alarm clock that never rings. Every accepted risk must instead name `re_review_signal` (the observable condition — a metric, an error pattern, a new dependency, a specific event — that should trigger re-review) and `owner` (who is responsible for noticing that signal and acting on it). Do not reintroduce `expires`/`expiry`; if the only real trigger available is a calendar date, write it INTO the `re_review_signal` text (e.g. "re-review at next quarterly audit"), but the field stays signal-shaped, not date-shaped.
3. **kill_switch is mandatory.** If you can't describe how to disable the feature, you can't ship it safely.
4. **silent_failure_surface** is computed from final scar state. Count unique,
   non-resolved `silent_failure_conditions`; keep accepted, deferred, open, and
   blocked items visible. `iteration: null` alone never removes an item.
