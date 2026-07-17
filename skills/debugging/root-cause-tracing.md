# Root Cause Tracing — Yin-Side Technique Reference

This file supplies diagnostic lenses only. `SKILL.md` owns procedure, artifacts,
and repair routing.

## Core Yin Question

> Why did the system allow this failure to look healthy?

The failure is the symptom. The deeper disease is a detection system that let
wrong state, missing side effects, or degraded behavior remain believable.
Diagnosis must explain both what failed and what pretended to be healthy while
damage spread.

Ask:

- Which component knew first, or should have known?
- Which boundary converted a visible failure into plausible output?
- Who discovered it, and how far had damage spread by then?
- Which signal, invariant, or owner was absent?
- If the failing component disappeared, would the system fail honestly or keep
  lying?

## Evidence Discipline

Keep observation, hypothesis, and confirmed cause separate. Every causal claim
needs a log, diff, reproduction, command result, or `file:line` reference. If
evidence is absent, record `unknown` and name what would resolve it. Never discard
refuting evidence to preserve a preferred explanation.

## Rot Path and Rot Distance

Trace corruption or missing behavior from entry to detection:

```text
entry
  -> transformation or boundary
  -> storage or side effect
  -> fallback/default/retry
  -> detection
```

For each edge record:

- what crossed the boundary;
- which guard should have stopped or exposed it;
- what evidence proves the guard failed;
- how the next layer hid, normalized, or amplified the damage.

The number of crossed layers is the **rot distance**. It is not an automatic
severity score; it shows how much system structure participated before truth
became visible.

## Accomplice Analysis

An accomplice is any component that makes failure appear healthy:

- silent catches returning plausible values;
- defaults erasing missing or corrupt input;
- fallbacks hiding degraded state;
- coercion converting invalid input into valid-looking data;
- retries hiding partial side effects or missing idempotency;
- dashboards or success responses checking the request path but not the promised
  outcome.

An accomplice is not automatically the root cause. State exactly how it delayed
detection, changed the signal, or widened the damage.

## Detection Debt

Reconstruct last-known-good evidence, suspected introduction, first observable
symptom, and discovery. Use `unknown` when a timestamp or commit cannot be
verified; correlation is not cause.

The delay between failure and discovery is detection debt. Identify:

- the earliest evidence the system could have exposed;
- why existing monitoring, validation, or ownership did not consume it;
- whether the Primary evaluator passed while the real outcome failed;
- what kept the system reporting health.

## Differential and Counterfactual Analysis

Compare failing and non-failing cases one variable at a time: input, state,
configuration, dependency, deployment, execution path, and side effects.

Then test the system's honesty:

- Without the fallback/default/catch, would failure become visible sooner?
- If code did not change, was a latent defect merely exposed by new data or load?
- Would the proposed repair remove the cause, or only shorten one visible symptom?
- Under what condition would the same system resume pretending to be healthy?

## Anti-Pattern — Premature Fix

A plausible patch is not a confirmed root cause. Fixing the first broken line can
leave the concealment mechanism intact, allowing the next failure to rot through
the same path. Diagnosis is complete only when it states what failed, why it
remained credible, what is confirmed, what remains unknown, and which repair
workflow owns the next action.
