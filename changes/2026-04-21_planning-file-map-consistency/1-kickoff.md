# Kickoff: Research ↔ Planning Bidirectional Completeness Gate

## Problem Statement

Samsara's "禁止靜默補全" axiom says: when input is incomplete, stop and mark what is missing. This rule governs all phases — but it is not applied when Planning reads Research. Planning currently proceeds even when Research is incomplete, silently deriving missing constraints from environmental bias rather than rejecting back to Research. The result: architectural decisions made in Research (with human confirmation) are violated during Planning by an agent filling gaps with path-of-least-resistance assumptions.

The symptom (ISSUE-001: File Map contradicting Key Decisions) is a consequence of this gap, not the root cause.

## Evidence

From `changes/2026-04-15_continuous-learning/`:
- Research Key Decision: "Shared, not samsara-exclusive" (human-confirmed)
- Research did NOT derive: "shared → files must not be inside any plugin directory → use scripts/ or project root"
- Planning encountered this gap, silently filled it with samsara/hooks/ (familiar infrastructure = path of least resistance)
- Error propagated through task specs, subagent implementations, code review — caught post-implementation by user

The gap was not a Planning failure. It was Research delivering an incomplete PRD (principle without constraint derivation), and Planning having no mechanism to reject it.

## Risk of Inaction

Every planning session where Research Key Decisions contain architectural scope without constraint derivation carries silent risk. The agent filling the gap introduces bias. The error only surfaces post-implementation (caught by human) or at runtime. Cost: full re-implementation of N tasks in wrong locations.

## Scope

### Must-Have (with death conditions)

- **Research kickoff template: Key Decisions must include architectural constraint derivation** — each decision must be pushed to "directly constrains file structure or module boundary" granularity before human gate confirmation. Death condition: remove if Key Decisions are eliminated as a concept from Research, or if planning is schema-driven from decisions automatically.

- **Planning skill: Research completeness validation step** — before writing Tech Spec or File Map, Planning explicitly checks whether each Key Decision with architectural scope has a derived constraint. If not, Planning stops and returns a gap report to Research rather than self-deriving. Death condition: remove if Research template structurally guarantees completeness (i.e., the validation becomes vacuous).

- **Research ↔ Planning bidirectional gate** — the handoff is not one-way. Planning can reject back to Research with a specific gap list. Research fills gaps (human for judgment calls, agent proposals with human confirmation for derivable constraints). Death condition: remove if all Research completeness is enforced structurally at template level.

### Nice-to-Have

- Architectural compliance check in code-reviewer (secondary — addresses late detection, not root cause)
- Anti-bias prompt in Planning's File Map section (secondary — addresses symptom, not mechanism)

### Explicitly Out of Scope

- Changing the research phase problem definition process
- Adding a new "System Design" skill between Research and Planning
- Modifying task decomposition format or scar report schema

## North Star

```yaml
metric:
  name: "Planning silent gap-fill rate"
  definition: "Number of planning sessions where agent self-derives a constraint that was not present in Research, without rejecting back"
  current: 1 known (continuous-learning), likely more
  target: 0
  invalidation_condition: "If Research becomes so granular that no constraint derivation is ever needed — Planning becomes pure execution with zero design space"
  corruption_signature: "Planning rejects back to Research trivially (for noise, not real gaps) to appear compliant. Detect via: rejection rate rising while architectural errors persist."

sub_metrics:
  - name: "Research completeness gate pass rate"
    current: unknown (gate doesn't exist)
    target: all sessions with architectural scope decisions have complete constraint derivation before Planning proceeds
    proxy_confidence: medium
    decoupling_detection: "Gate exists but never rejects — may mean Research is genuinely complete, or gate is not checking correctly"
  - name: "Post-implementation architectural corrections"
    current: 1 known
    target: 0
    proxy_confidence: high
    decoupling_detection: "Metric is 0 but user catches errors and doesn't record them — verify via session observation"
```

## Stakeholders

- **Decision maker:** yuyu_liao (project owner)
- **Impacted teams:** All samsara planning sessions across any project
- **Damage recipients:** Research agents bear extra responsibility (must push Key Decisions to constraint level); Planning agents bear a gate step (must validate before proceeding); human bears extra confirmation at Research stage
