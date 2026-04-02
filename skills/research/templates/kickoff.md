# Kickoff: <feature-name>

## Problem Statement
<!-- What problem are we solving? One paragraph. -->

## Evidence
<!-- Why does this problem exist? What data or observations support it? -->

## Risk of Inaction
<!-- What happens if we do nothing? Be specific. -->

## Scope

### Must-Have (with death conditions)
<!-- Each must-have includes: what it is, and when it should be killed -->
- **<item>** — Death condition: <when this should be removed>

### Nice-to-Have
- <item>

### Explicitly Out of Scope
- <item>

## North Star

```yaml
metric:
  name: "<metric name>"
  definition: "<precise definition>"
  current: <value>
  target: <value>
  invalidation_condition: "<when this goal itself is wrong>"
  corruption_signature: "<how to detect if metric is being gamed>"

sub_metrics:
  - name: "<sub-metric>"
    current: <value>
    target: <value>
    proxy_confidence: high | medium | low
    decoupling_detection: "<how to detect proxy diverging from main>"
```

## Stakeholders
- **Decision maker:** <who>
- **Impacted teams:** <who>
- **Damage recipients:** <who bears cost of the solution>
