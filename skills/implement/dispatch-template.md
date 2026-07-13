# Implementer Dispatch Template

Use this template when dispatching an implementer subagent. **Paste the full task
and complete compact Overview** — never make the subagent discover its global
context by choosing what to read.

## Global Thinking Channel — four layers, three push one pull

The dispatch prompt carries four context layers. The design rule behind them: **structural awareness must be broad, raw content must stay narrow** — awareness is small in volume, so pushing it does not violate subagent context hygiene.

| Layer | Content | Source (copied, never invented) | Push/Pull |
|---|---|---|---|
| **L1 global position** | complete compact Overview: core identity + shared context + all real seams; identify the current task seam | complete `overview.md` + this task's `seam` from `index.yaml` | push |
| **L2 context projection** | this task's `affects` (who builds on my structure, what they need) + `anchors` (read-first files, path + why) | `index.yaml` task entry | push |
| **L3 task body** | task-N.md full text | `tasks/task-N.md` | push |
| **L4 deep reference** | actual file contents | implementer reads them itself, starting from the anchors | pull |

**The dispatcher copies L1/L2 from planning's products; it never composes them.** Hand-curating "what's relevant to this task" at dispatch time is exactly the blind-spot mechanism the channel replaces — if the dispatcher finds itself writing a projection that planning did not produce, that is a violation: stop and send the gap back to planning, do not improvise.

**Three states, resolved per task before composing the prompt:**

- `seam`/`affects`/`anchors` fields present in `index.yaml` → inject L1/L2 as below.
- Fields absent (a plan written before the global thinking channel existed) → write `global_channel: absent` in Additional Context — explicit and visible, never silently skipped. The implementer then falls back to its own read-before-write neighbor judgment.
- Fields present but the referenced seam does not resolve in `overview.md` Real Seams Projection → that is a planning format failure the planning validator should have caught; do not dispatch — return to planning.

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

    [MUST paste the complete compact Overview verbatim: Core Identity, Shared
     Execution Context, and all Real Seams. Preserve every source_ref. This is
     broad structural awareness, not decision authority.]

    ## Global Position (L1)

    [COPY from planning products — never compose at dispatch time:
     - The complete Overview above is the shared L1 projection.
     - Current task seam: copy this task's `seam` from index.yaml and identify
       its matching Real Seams entry without dropping the other seams.
     If the plan predates the global thinking channel, write `global_channel: absent`
     here and omit the L2 section below.]

    ## Context Projection (L2)

    [COPY this task's `affects` and `anchors` entries from index.yaml verbatim:
     - affects: which planned tasks will build on this task's structure, and what
       they need from its boundary — this is the "planned change" evidence tier
       your pattern choices may cite in forced_by
     - anchors: files to read BEFORE writing (path + why). When this task has
       depends_on, the anchors include the upstream tasks' interface files — read
       the LIVE signatures to honor upstream contracts. Anchors are a starting
       set, not a whitelist: keep pulling along the trail (L4).]

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
2. **Copy the complete compact Overview** — Preserve every projection and
   `source_ref`; resolve authoritative decision text from the cited source
   artifact, never from Overview.
3. **Include death cases** — If `problem-autopsy.md` has death cases relevant to this task, paste them in Additional Context.
4. **Include prior scars** — If this task depends on a completed task (per `index.yaml`), include relevant scar report items that might affect implementation.
5. **Absolute paths only** — Working directory must be absolute. The subagent cannot resolve relative paths.
6. **Measure before writing** — any quantitative value written INTO a dispatch prompt (spec line counts, entry counts, test counts) must come from a command you actually ran (`wc -l`, `grep -c`, ...) before writing it, never an estimate — reviewers inherit dispatch numbers into verdicts (precedent: an unmeasured "30 lines" estimate propagated into a durable review-record verdict when the actual count was 25).
7. **Copy L1/L2, never compose** — the Global Position and Context Projection sections are verbatim copies of planning's products (Overview projections, index.yaml `seam`/`affects`/`anchors`). A dispatcher writing its own projection re-creates the hand-curation blind spot the channel exists to remove. A plan without these fields gets an explicit `global_channel: absent`, never a silent omission.

## Anti-Patterns

- **Never** tell the subagent to "read overview.md" or "read task-N.md" — it doesn't know where they are
- **Never** summarize the task file — the subagent needs the full death test requirements and acceptance criteria
- **Never** skip Additional Context for tasks with dependencies — prior scars propagate
- **Never** omit the working directory — the subagent needs to know where to create/edit files

## Review Dispatch

After the implementer reports back (status DONE or DONE_WITH_CONCERNS), dispatch BOTH reviewers in parallel.

**Dispatch both in the same message to enable parallel execution.** Two separate Agent calls in one message run concurrently; dispatching them in separate messages runs them sequentially and doubles wall-clock time.

**Aggregation rule:** Main agent MUST receive BOTH review outputs before proceeding. If only one output arrives, that is a FAIL with "missing reviewer" error — never assume absent reviewer = PASS. Re-dispatch the missing reviewer. If either reviewer returns `UNKNOWN`, that is a blocking review failure, not PASS/PASS_WITH_CONCERNS; fix the missing or unreadable reference/domain condition and re-dispatch both reviewers before proceeding.

### Yin reviewer
```
Agent tool:
  subagent_type: "samsara:code-reviewer"
  description: "Yin review Task N: [task title]"
  prompt: |
    Review the following changes for Task N: [task title]

    ## Feature
    [MUST name the feature directory: changes/<feature>/ — yin uses this to
     locate feature artifacts (scar reports, review-record.md if present) for
     cross-checks]

    ## Task Requirements
    [MUST paste acceptance criteria from task-N.md]

    ## Changed Files
    [List the files the implementer modified]

    ## Diff
    [MUST paste the unstaged diff of the implementer's changes]

    ## Placement Authority
    [Resolve this task's planning_refs and decision_refs from index.yaml. Paste
     the cited placement/ownership entries from 2-plan.md and pre-thinking.md,
     including their IDs. Do not source decisions from overview.md. If no cited
     decision constrains placement/ownership, say so explicitly.]

    ## Task Seam (L1)
    [Paste this task's `seam` value from index.yaml and the matching Real Seams
     Projection entry from overview.md, including source_ref. If the plan has no seam fields (predates the global
     thinking channel), write `global_channel: absent` — absence must be visible,
     not blank.]

    ## Architectural Placement Review (mandatory)
    Using the Placement Authority above, check whether the placement/ownership of
    the changed files matches its cited decisions. Classify each applicable decision
    as matches / contradicts / out-of-scope. A contradiction is a finding. If no
    authority refs were provided, say so — absence is a finding, not a silent pass.
    Seam placement dimension: using the Task Seam above, check whether the changed
    files actually sit on the declared seam (dangling seam ids are the planning
    validator's job — yours is whether the placement is TRUE to the declaration).

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

    ## Feature
    [MUST name the feature directory: changes/<feature>/ — the quality
     reviewer resolves forced_by / seam / affects citations against this
     feature's index.yaml and overview.md]

    ## Task Requirements
    [MUST paste acceptance criteria from task-N.md]

    ## Changed Files
    [List the files the implementer modified]

    ## Diff
    [MUST paste the unstaged diff of the implementer's changes]

    ## Global Position + Projection (L1/L2)
    [COPY from planning products, same as the implementer dispatch: this task's
     seam (Real Seams Projection entry, including source_ref) and its `affects` entries from index.yaml. These
     feed the structural-decision cross-check: whether forced_by citations are
     real, and whether a soft seam is backed by a planned change or speculative.
     If the plan predates the channel, write `global_channel: absent`.]

    ## Structural Decisions (scar)
    [Paste the `structural_decisions` section of this task's scar report
     verbatim — the dual-face entries under review. If the scar report has no
     structural_decisions key, say so — that is a finding, not a blank.]

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

Both reviewers must report back. If either reports `UNKNOWN`, FAIL, or PASS_WITH_CONCERNS with Critical issues, the implementer must fix before proceeding. `UNKNOWN` usually means a required reference could not be resolved or the execution domain is unsupported; treat it as blocking until the reference/domain issue is fixed and both reviewers are re-run.

After both reviews pass → update `index.yaml` → proceed to next task. Commit only after all tasks complete.

## Review Record Durability

After a task's review rounds conclude, the MAIN AGENT excerpts each verdict's key sections VERBATIM (not summarized) into `changes/<feature>/review-record.md`: **the reviewer's reasoning for each structural judgment (the payload is the reasoning, not only the verdict line — why an abstraction was judged speculative, how it was seen)**, any arbitration of a disputed Critical (who arbitrated, the ruling, one-line grounds), and the summary verdict line. Excerpts must be verbatim; if a source number in the verdict is known-wrong, keep the original text and add a transcription annotation next to it (precedent: the "30 lines vs 25" annotation in `changes/2026-07-05_issue-002-validate-live-surface/review-record.md`).

DC-5 discipline: an absent review-record entry for a reviewed task means "never recorded" (a finding at aggregation time), never "nothing to record" — a missing entry is not evidence that nothing happened.

**Honest marker:** this convention is prose-enforced only — no aggregation-time consumer reads `review-record.md` yet to check the DC-5 discipline above actually holds. Judgment records get visibility + adversarial review, not a code gate (format-vs-judgment: only mechanical shape ever gets script teeth).
