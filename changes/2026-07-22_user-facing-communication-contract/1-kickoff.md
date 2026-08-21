# Kickoff: user-facing-communication-contract

## Execution Mode

Execution mode: human-in-the-loop

## Problem Source

`problem-autopsy.md`

## Problem Essence (named handoff to pre-thinking)

User-facing answers need a result-first reading path without hiding the evidence
that lets a careful user verify the result.

## Scope Contract (sole scope authority)

- **What must be solved:** Bootstrap lacks a canonical response-shaping contract, so response length and ordering can drift with model reasoning effort.
- **Areas involved:** Bootstrap instructions, semantic guard tests, Codex conversion, and before/after evaluation evidence.

### Must-Have (with death conditions)

- **Standalone opening** — Death condition: remove only if the host platform guarantees the same request-shaped opening.
- **Evidence-preserving detail** — Death condition: never while users must verify changed files, tests, blockers, or unresolved risk.
- **Human-readable identifiers** — Death condition: remove only if machine identifiers disappear from user-visible workflow artifacts.
- **Single presentation authority** — Death condition: remove only if Bootstrap no longer governs the session-wide communication contract.

### Nice-to-Have

- Empirical scoring across multiple host models after the contract ships.

### Not solved now

- **Rewriting stage artifacts for brevity** — Reason: artifacts retain their own authority and lifecycle contracts.
- **A user verbosity preference system** — Reason: progressive disclosure serves both reading styles without new state.
- **Fixed word, paragraph, or bullet limits** — Reason: content risk determines necessary detail.

## Evidence

- The referenced communication-style repository prioritizes answer-first, low-preamble responses.
- User review showed that its terse form loses useful file and validation context.
- Existing Samsara rules require evidence visibility, explicit uncertainty, and semantic labels beside stable IDs.

## Risk of Inaction

High-reasoning responses can bury the result in process history, while aggressive
shortening can remove the evidence a careful user needs to decide whether to
accept the work.

## Accepted Research Gaps

- No cross-model benchmark exists yet; the evaluation therefore checks observable response properties rather than model-specific token counts.

## North Star

```yaml
metric:
  name: "Decision-ready response"
  definition: "A response whose opening stands alone and whose remaining detail preserves every applicable decision-changing fact without repetition."
  current: 0
  current_basis: "No canonical presentation contract or semantic guard exists"
  target: 1
  target_basis: "Bootstrap contract plus conversion and behavior-shape guards"
  invalidation_condition: "Host platform owns an equivalent enforced contract"
  corruption_signature: "Short output omits evidence, or detailed output repeats artifact history before stating the result"
```

## Delivery Stakeholders

- **Decision maker:** Samsara maintainer
- **Impacted users:** Result-oriented users, detail-oriented users, and agents producing user-facing workflow responses
