# Kickoff: samsara-auto-mode

## Problem Statement

Samsara needs an execution mode choice between `human-in-the-loop` and `auto mode`. Auto mode must not bypass the existing workflow; it must preserve the `research -> pre-thinking -> planning -> implementation -> iteration -> validation` chain while replacing each human gate with a principle-level subagent that can answer workflow questions, confirm transitions, request revision, reject unsafe continuation, or accept explicitly recorded gaps. The target quality bar is pre-production readiness, not PoC-level code generation.

## Evidence

1. Current Samsara workflow depends on human gates for quality control. That gives strong alignment, but it also prevents autonomous execution even when the objective is clear, verifiable, and feedback-rich enough for an agentic loop.
2. Current coding-agent `/goal`-style automation is too shallow for Samsara's standard. It can produce PoC-level work, but it does not preserve multi-stage design discipline, explicit gate decisions, or auditability across research, pre-thinking, planning, implementation, iteration, and validation.
3. The desired behavior is not "skip the workflow"; it is "run the same workflow with an agentic design authority standing in for human gate decisions." That means auto mode must make gate decisions visible, principled, reviewable, and reversible.

## Risk of Inaction

- Samsara remains dependent on synchronous human confirmation even when the work has clear goals, measurable acceptance, and enough feedback loops for autonomous execution.
- Users who want autonomous high-quality work will keep reaching for shallow `/goal`-like paths, creating a quality gap between Samsara's intended workflow and practical execution pressure.
- Human gates stay overloaded with decisions that could be delegated to a project-aware gatekeeper subagent, while genuinely ambiguous or high-risk decisions are not distinguished from routine confirmations.

## Scope

### Must-Have (with death conditions)

- **A configurable execution mode: `human-in-the-loop` or `auto`**
  Death condition: If mode selection is not visible in project config or session-level ask, and users cannot tell which gate policy is active before execution begins, this must be removed or redesigned.

- **Auto mode preserves the existing Samsara workflow**
  Death condition: If auto mode skips `research`, `pre-thinking`, `planning`, implementation discipline, iteration, or validation to gain speed, it is not Samsara auto mode and should be killed.

- **Every former human question or confirmation has an explicit agentic gate decision**
  Death condition: If a gate silently passes without a recorded decision, rationale, uncertainty level, and evidence checked, the auto gate is corrupt and must fail closed.

- **A principle-level gatekeeper subagent replaces human gate answers in auto mode**
  Death condition: If the substitute agent behaves like a narrow reviewer that only checks local output, rather than reasoning from project principles and workflow intent, it should not be trusted as the core auto-mode component.

- **The gatekeeper subagent uses first-principles reasoning when uncertain**
  Death condition: If uncertainty leads to arbitrary continuation, hallucinated requirements, or ungrounded approval instead of returning to first principles or falling back to human, auto mode should be disabled for that run.

- **Auto mode can degrade to human-in-the-loop**
  Death condition: If the system cannot stop and request human input when the objective, risk, or evidence is insufficient, auto mode transfers too much debugging cost to the user and should be blocked.

- **Decision trace is auditable after the run**
  Death condition: If the user or maintainer cannot reconstruct why each gate passed, what alternatives were rejected, and what verification backed the decision, the mode fails the pre-production quality bar.

### Nice-to-Have

- Per-stage confidence scoring that helps summarize which parts of an auto run are strongest or weakest.
- Configurable strictness profiles, such as conservative auto mode for production-impacting code and faster auto mode for isolated internal changes.
- Reusable project-principles artifact that the gatekeeper subagent can update over time, with explicit review rules.

### Explicitly Out of Scope

- Replacing the existing human-in-the-loop workflow.
- Skipping Samsara stages for speed.
- Treating auto mode as a generic `/goal` wrapper that only asks the coding agent to continue until something compiles.
- Guaranteeing that auto mode never needs human intervention; responsible fallback is part of the design.
- Implementing the runtime mechanics in research phase. This document defines the problem shape and evaluation criteria only.

## North Star

```yaml
metric:
  name: "auto_mode_gate_alignment_rate"
  definition: "Percentage of auto-mode gate decisions that a later human audit accepts without requiring material rework of the decision, rationale, or downstream artifact."
  current: "not measured; auto mode does not exist yet"
  target: ">= 90% accepted gate decisions across representative pre-production feature runs"
  invalidation_condition: "If human audit is unavailable, too superficial, or only checks final code instead of gate decisions, this metric cannot validate auto mode."
  corruption_signature: "Alignment rate rises while post-run user debugging or implementation rework also rises; this means audits are rubber-stamping decisions instead of detecting misalignment."

sub_metrics:
  - name: "workflow_stage_preservation_rate"
    definition: "Percentage of auto-mode runs that produce the expected artifacts and gate decisions for every required Samsara stage."
    current: "not measured"
    target: "100% for all non-aborted auto-mode runs"
    proxy_confidence: high
    decoupling_detection: "If artifacts exist but contain shallow or templated gate decisions, the proxy has decoupled from real workflow preservation."

  - name: "human_fallback_precision"
    definition: "Percentage of fallbacks to human that are judged necessary because the gatekeeper lacked enough objective, evidence, or risk clarity."
    current: "not measured"
    target: "High enough to catch true ambiguity without routing routine decisions back to the user; initial target 70-90% necessary fallbacks."
    proxy_confidence: medium
    decoupling_detection: "Fallbacks near 0% with rising misalignment indicates overconfident auto mode; fallbacks near 100% indicates auto mode is not making meaningful decisions."

  - name: "post_run_user_debug_burden"
    definition: "Count of user-reported issues where the user must manually debug requirement mismatch after an auto-mode run."
    current: "not measured"
    target: "Trending down across auto-mode iterations; severe mismatch should be rare before pre-production claim."
    proxy_confidence: medium
    decoupling_detection: "If users stop reporting mismatch but abandon auto mode or redo work outside Samsara, the metric falsely improves."

  - name: "decision_trace_completeness"
    definition: "Percentage of gate decisions with recorded rationale, evidence checked, uncertainty, rejected alternatives, and next-step consequence."
    current: "not measured"
    target: "100% for required gates"
    proxy_confidence: high
    decoupling_detection: "If traces are complete in fields but generic in content, completeness no longer indicates auditability."
```

## Stakeholders

- **Decision maker:** yuyu_liao
- **Impacted teams:** Samsara users, future Samsara skill authors, maintainers of the workflow chain, agents/subagents that execute gates
- **Damage recipients:**
  - User / project owner: bears second-pass debugging cost when auto output does not match the real expectation.
  - Maintainer / reviewer: bears audit and understanding cost if decision traces are unclear.
  - Gatekeeper subagent design: becomes a critical control point and must carry project-principle reasoning rather than local checklist review.
