# Implementer Dispatch Template

Use this template when dispatching an implementer subagent. **Paste full text** of task and overview — never make the subagent read files.

## Model & Effort Selection

The agent definition (`agents/implementer.md`) sets defaults: `model: sonnet`, `effort: high`. Override per-dispatch when needed:

| Task complexity | model | effort | When |
|----------------|-------|--------|------|
| Isolated, clear spec, 1-2 files | `sonnet` | `medium` | Most tasks with well-specified plans |
| Multi-file coordination, integration | `sonnet` | `high` | Tasks with cross-file dependencies |
| Architecture decisions, broad codebase impact | `opus` | `high` | Tasks requiring design judgment |

**Default to the agent definition's defaults.** Only override `model`/`effort` when the task clearly demands more capability.

## Template

Before composing the dispatch prompt, read `templates/scar-schema.yaml` from the implement skill directory. Paste its full content into the **Scar Report Format** section below.

```
Agent tool:
  subagent_type: "samsara:implementer"
  model: sonnet                # optional — omit to use agent default (sonnet)
  effort: medium               # optional — omit to use agent default (medium)
  description: "Implement Task N: [task title from index.yaml]"
  prompt: |
    You are implementing Task N: [task title]

    ## Architecture Context

    [Paste RELEVANT SECTIONS of overview.md — curate for this task, don't dump the entire file.
     Include: Goal, Tech Stack, Key Decisions that affect this task, and relevant Death Cases.]

    ## Task

    [Paste FULL TEXT of task-N.md — do not summarize, do not truncate]

    ## Scar Report Format

    [Paste FULL CONTENT of scar-schema.yaml — the subagent cannot read this file]

    ## Working Directory

    [Absolute path to the project root or worktree]

    ## Additional Context

    [Optional: relevant scar reports from prior tasks that affect this one,
     specific death cases from problem-autopsy.md, or dependency notes from index.yaml]
```

## Rules

1. **Always paste full text** — `task-N.md` must be pasted in its entirety. The subagent has no context about file locations.
2. **Curate overview.md** — Don't paste the entire overview for every task. Select sections relevant to this specific task's scope.
3. **Include death cases** — If `problem-autopsy.md` has death cases relevant to this task, paste them in Additional Context.
4. **Include prior scars** — If this task depends on a completed task (per `index.yaml`), include relevant scar report items that might affect implementation.
5. **Absolute paths only** — Working directory must be absolute. The subagent cannot resolve relative paths.

## Anti-Patterns

- **Never** tell the subagent to "read overview.md" or "read task-N.md" — it doesn't know where they are
- **Never** summarize the task file — the subagent needs the full death test requirements and acceptance criteria
- **Never** skip Additional Context for tasks with dependencies — prior scars propagate
- **Never** omit the working directory — the subagent needs to know where to create/edit files

## Review Dispatch

After the implementer reports back (status DONE or DONE_WITH_CONCERNS), dispatch yin-side code review:

```
Agent tool:
  subagent_type: "samsara:code-reviewer"
  description: "Review Task N: [task title]"
  prompt: |
    Review the following changes for Task N: [task title]

    ## Task Requirements
    [Paste acceptance criteria from task-N.md]

    ## Changed Files
    [List the files the implementer modified]

    ## Diff
    [Paste the unstaged diff of the implementer's changes]
```

If the code-reviewer reports FAIL or PASS_WITH_CONCERNS with Critical issues, the implementer must fix before proceeding.

After review passes → update `index.yaml` → proceed to next task. Commit only after all tasks complete.
