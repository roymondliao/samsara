# Kickoff: <feature-name>

## Problem Statement
<!-- What problem are we solving? One paragraph. -->

## Problem Essence (named handoff to pre-thinking)
<!-- One or two lines, REQUIREMENT language: what must be solved, stripped of any
     implementation shape. This is a distinct product from pre-thinking's "core
     identity" (STRUCTURE language: what the code must essentially be to serve
     this) — research owns the essence, pre-thinking distils the identity from it.
     Test: if the essence names a mechanism ("add a cache", "use a hook") instead
     of a need, it is a solution wearing the problem's clothes — rewrite. -->

## Boundary Scope (what the seams may be drawn inside)
<!-- Research frames the RANGE structural thinking happens inside — without this,
     pre-thinking cannot tell this feature's real seams from someone else's
     territory. Three lists, subtraction first: -->
- **真正要解什麼:** <the one thing actually being solved>
- **涉及哪些:** <areas/modules this genuinely touches>
- **哪些現在不做:** <adjacent things explicitly NOT solved now — each with one
  line on why not-now (a cut with no reason silently grows back)>

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

### POC Death Date (optional)
<!-- Only set this if the feature is a genuine throwaway POC exempt from the structure-spec path; planning re-checks this date every pass — an expired date forces the full spec path, it does not extend the exemption. -->
poc_death_date: "<YYYY-MM-DD, optional>"

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
