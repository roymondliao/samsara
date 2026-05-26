---
name: pre-thinking
description: Use when research output (1-kickoff.md + problem-autopsy.md) is complete and you need to surface user-LLM assumption gaps before planning — always runs between research and planning in the samsara chain
---

# Pre-thinking — Surface Gaps Before Planning

Surface the gap between what research established and what planning would need to assume. Make that gap visible to the human before any plan is written.

## Prerequisites

Read from `changes/<feature>/`:
- `1-kickoff.md` — scope, north star, stakeholders
- `problem-autopsy.md` — translation delta, kill conditions

## Process

```dot
digraph pre_thinking {
    node [shape=box];
    start [label="讀取 1-kickoff.md\n+ problem-autopsy.md" shape=doublecircle];
    k3b [label="pre-thinking.md 存在？\n缺 Step C？" shape=diamond];
    resume [label="K3b detected:\nAskUserQuestion\nResume / Restart" shape=doublecircle];
    step_a [label="Step A\n一次寫 pre-thinking.md\n識別所有 gaps"];
    has_gaps [label="gaps?" shape=diamond];
    quick [label="quick-pass\ngaps: none identified\n→ Step C"];
    step_b [label="Step B\n分組問答\n≤3 題/call\nAskUserQuestion\nappend answers"];
    uncertain [label="user 顯示不確定？" shape=diamond];
    rtr_mid [label="RTR: gap list\n→ stop" shape=doublecircle];
    step_c [label="Step C\nAskUserQuestion\nProceed / Accept gap\n/ Return to Research"];
    planning [label="invoke samsara:planning" shape=doublecircle];
    rtr_end [label="RTR: gap list\n→ stop" shape=doublecircle];

    start -> k3b;
    k3b -> resume [label="yes, incomplete"];
    k3b -> step_a [label="no file"];
    k3b -> planning [label="complete\n(Step C present)"];
    resume -> step_a [label="Restart"];
    resume -> step_b [label="Resume"];
    step_a -> has_gaps;
    has_gaps -> quick [label="no gaps"];
    has_gaps -> step_b [label="gaps exist"];
    quick -> step_c;
    step_b -> uncertain [label="group done"];
    uncertain -> step_b [label="Continue\n(next group)"];
    uncertain -> rtr_mid [label="Return to\nResearch"];
    step_b -> step_c [label="all groups done"];
    step_c -> planning [label="Proceed /\nAccept gap"];
    step_c -> rtr_end [label="Return to\nResearch"];
}
```

## Step A — Gap Identification

Read both research artifacts. Identify every decision planning would need to make that research has not constrained. Write all gaps to `pre-thinking.md` in one shot — do NOT start AskUserQuestion before Step A write is complete. If no gaps exist, write `gaps: none identified` and skip Step B entirely. See `support/flow.md` for gap identification criteria.

## Step B — Question Groups

Group gaps by topic domain and answer-interdependency (≤3 questions per AskUserQuestion call). After each call, append answers to `pre-thinking.md` below all existing content — never rewrite or truncate. Read the file before each append; if the file differs from the last-written state, incorporate user edits before appending. See `support/flow.md` §2 for group formation rules, §3 for group overflow procedure, §4 for file-edit detection, §7 for AskUserQuestion header constraint (≤12 chars).

## Step C — Commitment

Collect the final commitment via AskUserQuestion with options: Proceed / Accept gap / Return to Research.

**Step C commitment must be collected via AskUserQuestion — never inferred from conversation context.**

When commitment = Return to Research: write `## Step C — Commitment` section with `Decision: Return to Research` and a non-empty `unresolved_gaps` list referencing specific Step A gap labels. Do NOT invoke `samsara:planning`. See `support/flow.md` for exact write format.

When commitment = Proceed or Accept gap: invoke `samsara:planning`.

## Yin Constraints

- **LLM is the sole writer to pre-thinking.md. User responds via AskUserQuestion only.**
- **Presence of `## Step C — Commitment` signals session complete. Absence = K3b interrupted state — on session start, check for this section before proceeding.**
- **Step A is written in one shot. Do NOT start AskUserQuestion before Step A write is complete.**

## Output

`changes/<feature>/pre-thinking.md` — single file, LLM sole writer. Presence of `## Step C — Commitment` = session complete.
