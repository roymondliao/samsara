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

    ## Project Conventions

    [MUST paste the content of AGENTS.md from the worktree root]

    ## Architecture Context

    [MUST paste RELEVANT SECTIONS of overview.md — curate for this task, don't dump the entire file.
     Include: Goal, Tech Stack, Key Decisions that affect this task, and relevant Death Cases.]

    ## Task

    [MUST paste FULL TEXT of task-N.md — do not summarize, do not truncate]

    ## Scar Report Format

    [MUST paste FULL CONTENT of scar-schema.yaml — the subagent cannot read this file]

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

After the implementer reports back (status DONE or DONE_WITH_CONCERNS), dispatch BOTH reviewers in parallel.

**Dispatch both in the same message to enable parallel execution.** Two separate Agent calls in one message run concurrently; dispatching them in separate messages runs them sequentially and doubles wall-clock time.

**Aggregation rule:** Main agent MUST receive BOTH review outputs before proceeding. If only one output arrives, that is a FAIL with "missing reviewer" error — never assume absent reviewer = PASS. Re-dispatch the missing reviewer.

### Yin reviewer
```
Agent tool:
  subagent_type: "samsara:code-reviewer"
  description: "Yin review Task N: [task title]"
  prompt: |
    Review the following changes for Task N: [task title]

    ## Task Requirements
    [MUST paste acceptance criteria from task-N.md]

    ## Changed Files
    [List the files the implementer modified]

    ## Diff
    [MUST paste the unstaged diff of the implementer's changes]

    ## Test-Quality Review (mandatory)
    Review the TESTS before implementation correctness. For every test in the diff:
    - Flag brittle / over-fit tests (redden on a behavior-preserving refactor —
      pinned to implementation details, not an observable contract).
    - Flag tautological / silent-green tests (can never go red — assert almost
      nothing, stay green when behavior breaks).
    - When a test is bound to the WRONG contract, say "fix the test, not the
      implementation" — do not bend the implementation to a rotten test.
    - Challenge any perfunctory contract label (Clean Scar): a named contract that
      maps to no observable behavior, API/schema, artifact, or death/bug case does
      NOT satisfy the gate.
```

### Code Quality reviewer
```
Agent tool:
  subagent_type: "samsara:code-quality-reviewer"
  description: "Code quality review Task N: [task title]"
  prompt: |
    Review the following changes for Task N: [task title]

    ## Task Requirements
    [MUST paste acceptance criteria from task-N.md]

    ## Changed Files
    [List the files the implementer modified]

    ## Diff
    [MUST paste the unstaged diff of the implementer's changes]

    ## Test-Quality Review (mandatory — structural test coupling)
    Review the TESTS for structural test coupling: tests coupled to the
    implementation STRUCTURE (private internals, call sequence, member layout,
    mock-call order) rather than to an observable contract. Report this as
    structural evidence under the Coupling principle with file:line evidence.
    Structural coupling is evidence for the yin reviewer's brittle-test review;
    refer any brittle / wrong-contract / fix-the-test verdict, plus test
    silent-rot / correctness concerns (tautological tests, wrong-contract tests),
    to the yin code reviewer.
```

Both reviewers must report back. If either reports FAIL or PASS_WITH_CONCERNS with Critical issues, the implementer must fix before proceeding.

After both reviews pass → update `index.yaml` → proceed to next task. Commit only after all tasks complete.
