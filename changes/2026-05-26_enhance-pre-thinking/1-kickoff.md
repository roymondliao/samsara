# Kickoff: enhance-pre-thinking

## Problem Statement

`samsara:pre-thinking` currently addresses one type of gap: information decisions the LLM would need to make during planning that research has not constrained. Two capabilities are absent: (1) design decision alignment — surfacing architectural/structural choices that affect how tasks are decomposed, so agents do not make undeclared design assumptions during planning; and (2) agent-evaluable evaluation alignment — forcing the user to define the one canonical method an agent can run, inspect, or consistently judge to decide whether the task is actually done. Without these, agents proceed to planning with implicit design choices and no stable feedback source for iteration or bug fixing.

## Evidence

- Current pre-thinking maps exclusively to information gaps: "research didn't specify X." It does not distinguish information gaps from design decision gaps — cases where research establishes constraints but multiple valid architectural choices remain and the choice structurally affects task breakdown.
- Planning produces `acceptance.yaml` written by the LLM. But if the only useful feedback source is a browser flow, artifact inspection, snapshot comparison, CLI behavior, or stable rubric, this intent is never captured. The LLM writes acceptance criteria from research artifacts, not from a user-confirmed agent-evaluable standard.
- TDD and death-path tests confirm code correctness. They do not necessarily define the single feedback source the agent should use when deciding whether to iterate or debug. The gap between "tests pass" and "agent can prove done" is currently invisible until delivery.

## Risk of Inaction

Agents continue to make design choices during planning without user approval. Delivered features pass automated test suites but misalign with user's verification intent. The misalignment is discovered post-delivery, requiring re-iteration that could have been prevented at the pre-thinking stage.

## Scope

### Must-Have (with death conditions)

- **Design decision gap category** — Step A identifies two distinct gap types: (a) information gaps (research didn't establish X), and (b) design decision gaps (research established constraints but multiple valid designs remain; choice structurally affects task decomposition). Agents surface both types for user confirmation. — Death condition: if design decision gaps in practice are indistinguishable from information gaps (no real separation in agent behavior), merge back into a single Step A gap category and remove the distinction.

- **Mandatory agent-evaluable Evaluation Contract** — pre-thinking always asks the user to define the one Primary evaluator the agent should use to judge completion, including how the agent can perform it, pass/fail signal, and feedback loop. Captured even on the quick-pass path. — Death condition: if evaluation responses are consistently identical to "run the automated tests" across ≥5 consecutive feature sessions, the question may be too heavy and should be redesigned, but tests-only must be an explicit user choice.

### Nice-to-Have

- Structured evaluator types (e.g., `command | browser_flow | artifact_inspection | snapshot_comparison | stable_rubric`)
- Quick-pass evaluation shorthand: if the user responds "automated tests only," record tests as the explicit Primary evaluator with no further follow-up

### Explicitly Out of Scope

- Replacing `planning/acceptance.yaml` with pre-thinking's evaluation capture (pre-thinking captures user intent; planning formalizes into BDD acceptance criteria)
- System design that covers implementation details (loop style, naming, internal module structure) — these remain implementer decisions
- Replacing TDD or death-path tests — the Primary evaluator is the canonical feedback source, while engineering tests remain mandatory quality gates

## North Star

```yaml
metric:
  name: "first-delivery acceptance rate"
	  definition: "percentage of delivered features where the user-confirmed Primary evaluator confirms success without requesting re-iteration"
  current: "unknown (no baseline — enhanced pre-thinking not yet in production)"
  target: "measurable improvement over baseline after 5+ features use the enhanced skill"
  invalidation_condition: "if the metric improves but pre-thinking sessions become so heavy that agents or users skip or rush them — optimizing acceptance rate at the cost of process integrity"
	  corruption_signature: "Primary evaluator responses are consistently vague, plural, or not agent-performable; detect by reviewing Evaluation Contract fields in pre-thinking.md across sessions"

sub_metrics:
  - name: "evaluation specificity rate"
    current: "unknown"
	    target: "≥70% of Evaluation Contracts name one agent-performable or agent-inspectable Primary evaluator"
    proxy_confidence: high
    decoupling_detection: "if specificity is high but re-iteration rate is unchanged, captured evaluation intent is not reducing post-delivery misalignment"

  - name: "design decision gap capture rate"
    current: "unknown"
    target: "≥50% of non-trivial pre-thinking sessions surface at least one design decision gap distinct from information gaps"
    proxy_confidence: medium
    decoupling_detection: "if design gaps are captured in pre-thinking.md but planning still makes undeclared design assumptions, the gap-to-plan linkage is broken"
```

## Stakeholders

- **Decision maker:** yuyu_liao (framework author and sole user)
- **Impacted teams:** any agent executing `samsara:pre-thinking` or `samsara:planning`
- **Damage recipients:** agents handling pre-thinking (must now distinguish two gap types and always ask evaluation); planning skill (may need to formally import pre-thinking.md as a prerequisite input if evaluation intent is consumed at planning time)
