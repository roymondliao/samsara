# Kickoff: <feature-name>

## Problem Source
`problem-autopsy.md`
<!-- Canonical source wording, reframe, translation delta, kill conditions,
     damage recipients, and observable done state live there. Do not restate them. -->

## Problem Essence (named handoff to pre-thinking)
<!-- One or two lines, REQUIREMENT language: what must be solved, stripped of any
     implementation shape. This is a distinct product from pre-thinking's "core
     identity" (STRUCTURE language: what the code must essentially be to serve
     this) — research owns the essence, pre-thinking distils the identity from it.
     Test: if the essence names a mechanism ("add a cache", "use a hook") instead
     of a need, it is a solution wearing the problem's clothes — rewrite. -->

## Scope Contract (sole scope authority)
<!-- Research frames the RANGE structural thinking happens inside. Keep all scope
     facts here; do not create a second boundary/out-of-scope list elsewhere. -->
- **What must be solved:** <the one thing actually being solved>
- **Areas involved:** <areas/modules this genuinely touches>

### Must-Have (with death conditions)
- **<item>** — Death condition: <when this should be removed>

### Nice-to-Have
- <item>

### Not solved now
- **<adjacent item>** — Reason: <why not now; an unexplained cut grows back>

## Evidence
<!-- Why does this problem exist? What data or observations support it? -->

## Risk of Inaction
<!-- What happens if we do nothing? Be specific. -->

## North Star

<!-- Product outcome direction owned by Research. This is not `PT-EVAL`;
     Pre-thinking defines the one agent-executable Primary evaluator. -->

```yaml
metric:
  name: "<metric name>"
  definition: "<precise definition>"
  current: <value | unknown>
  current_basis: "<measurement source | missing input>"
  target: <value | unknown>
  target_basis: "<decision rationale | missing input>"
  invalidation_condition: "<when this goal itself is wrong>"
  corruption_signature: "<how to detect if metric is being gamed>"

sub_metrics:
  - name: "<sub-metric>"
    current: <value | unknown>
    current_basis: "<measurement source | missing input>"
    target: <value | unknown>
    target_basis: "<decision rationale | missing input>"
    proxy_confidence: high | medium | low
    decoupling_detection: "<how to detect proxy diverging from main>"
```

## Delivery Stakeholders
- **Decision maker:** <who>
- **Impacted teams:** <who>
