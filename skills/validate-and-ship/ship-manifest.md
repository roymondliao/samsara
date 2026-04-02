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
    expires: "YYYY-MM-DD"  # When this risk acceptance should be re-evaluated

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
2. **accepted_risks must have expiry dates.** Risk acceptance is not permanent. Every accepted risk has a date by which it must be re-evaluated.
3. **kill_switch is mandatory.** If you can't describe how to disable the feature, you can't ship it safely.
4. **silent_failure_surface** is computed from scar reports. Count the unique `silent_failure_conditions` across all task scar reports.
