# Problem Autopsy: enhance-pre-thinking

## original_statement

「我認為 pre-thinking 除了是協助 agent 與 user 補齊對於 tasks 更細節部分的討論外，還有涉及對於 tasks 的 system design，我認為有好的 system design 會協助 agent 更好的 planning，並且 task 完成度可以對齊 user 的需求。此外，在 pre-thinking 的階段，必定要包含一個問題，就是要問 user 關於這個 task 要如何來 evaluation ? 因為 TDD 開發在 implement 會做，但是 TDD 跟 death path 的測試都不一定是 user 最終的驗證方式，所以 evaluation 需要對齊。」

## reframed_statement

The `samsara:pre-thinking` skill fills information gaps between research and planning. Two capabilities are absent:

1. **Design decision alignment**: Beyond pure information gaps, pre-thinking should surface design decisions that affect how tasks will be structured. Research may establish constraints but still leave multiple valid architectural choices — the choice structurally shapes how tasks are decomposed. If not surfaced in pre-thinking, agents default-fill these choices during planning without user approval.

2. **Agent-evaluable evaluation alignment**: Pre-thinking must always force the user to define the one Primary evaluator the agent should use to judge completion. TDD and death-path tests confirm code correctness, but they are not necessarily the canonical feedback source for iteration or bug fixing. The evaluator must be something the agent can run, inspect, or apply consistently — command, browser flow, artifact inspection, snapshot comparison, log check, or stable rubric.

## translation_delta

```yaml
translation_delta:
  - original: "還有涉及對於 tasks 的 system design"
    reframed: "design decisions that affect how tasks are decomposed and structured"
    delta: >
      "System design for tasks" is broad — could include architecture, naming, data model, API contracts,
      or internal module structure. Reframed narrows to: design decisions whose choice structurally affects
      task decomposition. Implementation details (loop style, variable names, internal module structure) remain
      implementer decisions and are explicitly out of scope. The line is: does this choice change what tasks
      exist, not just how a task is implemented?

  - original: "有好的 system design 會協助 agent 更好的 planning"
    reframed: "user-confirmed design constraints prevent agents from making undeclared design assumptions during planning"
    delta: >
      Original frames design discussion as quality improvement ("better planning"). Reframed frames it as a
      constraint mechanism — the value is preventing unconfirmed assumptions from silently entering the plan,
      not optimizing design quality. This framing makes the death case visible: if design gaps are surfaced
      but agents still make undeclared assumptions during planning, the enhancement failed.

  - original: "task 完成度可以對齊 user 的需求"
    reframed: "delivered features satisfy the user's stated verification method on first delivery"
    delta: >
      Original is unmeasurable ("task completion aligns with user needs"). Reframed makes it observable:
      does the user need to re-iterate after delivery? This is a binary event per feature, measurable across
      sessions.

  - original: "必定要包含一個問題，就是要問 user 關於這個 task 要如何來 evaluation"
    reframed: "a mandatory agent-evaluable Evaluation Contract is always captured in pre-thinking, regardless of whether other gaps exist"
    delta: >
      "Must include a question" implies always-on, but the later clarification makes the question stricter:
      the user is not merely describing personal acceptance; they must choose one standard that an agent can
      execute, inspect, or judge consistently. The output is a contract with Primary evaluator, pass/fail
      signals, and feedback loop. Quick-pass may still skip gap questions, but it cannot skip this contract.
```

## kill_conditions

```yaml
kill_conditions:
  - condition: >
      Design decision gaps in practice are indistinguishable from information gaps — agents cannot
      reliably categorize gaps into "information" vs "design decision" without ambiguity
    rationale: >
      If the two gap types collapse into one in agent behavior, the separate category adds cognitive
      overhead without behavioral change; merge back into a single Step A gap type

  - condition: >
      Evaluation Contracts are consistently vague, plural, or not agent-evaluable across ≥5 consecutive
      feature sessions
    rationale: >
      The mandatory Evaluation Contract exists to produce one stable feedback source for iteration and
      debugging. If users cannot define one agent-evaluable standard, the contract shape is wrong.

  - condition: >
      Quick-pass path ceases to function for simple features because the evaluation question adds
      an AskUserQuestion call that did not previously exist, making all features heavyweight
    rationale: >
      The quick-pass path serves low-complexity changes. If it is destroyed, the framework's fast
      track is eliminated. If this condition is reached, redesign evaluation to integrate into
      the existing Step C call rather than add a new call.
```

## damage_recipients

```yaml
damage_recipients:
  - who: "Agents executing samsara:pre-thinking"
    cost: >
      Must now identify and present two distinct gap types during Step A (information gaps vs design
      decision gaps), and always capture one Primary evaluator — including on the quick-pass path.

  - who: "Users doing quick iterations on simple features"
    cost: >
      Pre-thinking sessions that previously used the quick-pass path (gap questions skipped) now always
      include at least the Evaluation Contract. Overhead depends on whether the evaluator question is
      folded into the same AskUserQuestion call as commitment.

  - who: "samsara:planning skill"
    cost: >
      If planning is expected to consume evaluation intent captured in pre-thinking.md, planning
      must add pre-thinking.md as a formal prerequisite input — not just 1-kickoff.md and
      problem-autopsy.md. This is a dependency chain change that requires a planning skill update.
```

## observable_done_state

An agent completing enhanced pre-thinking produces a `pre-thinking.md` containing: (a) explicitly categorized gaps — information gaps and design decision gaps — each confirmed or accepted by the user, and (b) one agent-evaluable Evaluation Contract with Primary evaluator, pass/fail signal, and Feedback loop. When the feature is delivered, validate-and-ship applies that evaluator. If it fails, iteration/debugging use the same feedback loop instead of inventing a new standard.
