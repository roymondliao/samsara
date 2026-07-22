# Overview: user-facing-communication-contract

> Derived implementation projection. Do not add or revise decisions here;
> regenerate this file from the referenced authority artifacts.

## Sources

- Design authority: `pre-thinking.md`
- Planning judgment: `2-plan.md`
- Acceptance contract: `acceptance.yaml`
- Execution graph: `index.yaml`

## Core Identity Projection

- source_ref: PT-CI
  consequence: Make the decision easy without hiding the evidence required to verify it.

## Shared Execution Context

- source_ref: PL-D1
  consequence: Bootstrap is the only user-facing presentation authority; stage skills retain payload ownership.
- source_ref: PL-D2
  consequence: Guard semantic behavior and Codex conversion, not exact prose formatting.

## Real Seams Projection

- seam: artifact-to-response
  source_ref: PT-S1
  source: `pre-thinking.md#seam-artifact-to-response`
  what: Project complete artifact evidence into a concise response without creating a second authority.
  evidence: domain-essential
  planned: task-1, task-2
- seam: result-to-detail
  source_ref: PT-S2
  source: `pre-thinking.md#seam-result-to-detail`
  what: Let result-oriented readers stop after the opening while detail-oriented readers continue into evidence.
  evidence: already-happened
  planned: task-1, task-2
