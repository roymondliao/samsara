# Overview: codex-global-companion-runtime

> Derived implementation projection. Do not add or revise decisions here;
> regenerate this file from the referenced authority artifacts.

## Sources

- Design authority: `pre-thinking.md`
- Planning judgment: `2-plan.md`
- Acceptance contract: `acceptance.yaml`
- Execution graph: `index.yaml`

## Core Identity Projection

- source_ref: PT-CI
  consequence: Treat install success as a proven executable runtime contract, never as file-copy completion.

## Shared Execution Context

- source_ref: PL-D1
  consequence: Runner proof, command materialization, smoke checks, and manifest migration stay under one task owner.
- source_ref: PL-D2
  consequence: No-fallback guidance and companion syntax floor describe the same invocation boundary.
- source_ref: PL-D3
  consequence: Only clean-PATH execution from a foreign cwd satisfies PT-EVAL.

## Real Seams Projection

- seam: runtime-provenance
  source_ref: PT-S1
  source: `pre-thinking.md#seam-runtime-provenance`
  what: Separate an invoking process from a runner eligible to become a persistent installed dependency.
  evidence: already-happened
  planned: task-1
- seam: command-materialization
  source_ref: PT-S2
  source: `pre-thinking.md#seam-command-materialization`
  what: Convert a scope-agnostic runner token into a verified machine-specific absolute command only during installation.
  evidence: already-happened
  planned: task-1, task-2
- seam: installation-evidence
  source_ref: PT-S3
  source: `pre-thinking.md#seam-installation-evidence`
  what: Record executable dependencies beside file ownership so update can audit both.
  evidence: domain-essential
  planned: task-1, task-3
