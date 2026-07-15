# Auto Mode Reference

Auto mode is a workflow execution policy. It preserves every Samsara gate and
routes the judgment that a human would make to `samsara:auto-gatekeeper`.

The human and auto-gatekeeper are **symmetric workflow arbiters**: they receive
the same question, evidence, options, and workflow consequences.
This symmetry does not grant the gatekeeper external execution authority or
human consent. It does not authorize merge, push, PR creation, history rewrite,
or discard; those remain separately authorized actions.

## Authority

- Research owns workflow-run mode selection and persists it in
  `1-kickoff.md`. Later stages consume that value; Bootstrap does not select it.
- The stage owns its prompt, stable gate ID, allowed decisions, and the effect of
  each answer.
- The auto-gatekeeper owns the judgment and is the sole writer of
  `changes/<feature>/auto-decisions.md`.
- The calling workflow dispatches, waits, then applies the validated decision. It
  must not compose, rewrite, or append the decision itself.
- The auto-gatekeeper companion owns mechanical decision-log validation and the
  atomic append. No workflow skill owns or duplicates that writer mechanism.
- This reference owns the decision schema and shared semantics. Stage-specific
  Auto Mode Gate sections are projections; this reference wins if they drift.
- Format validators judge shape and references. They never judge whether the
  engineering recommendation is good.

## Stage Gate Protocol

The calling workflow reads `Execution mode:` from Research's `1-kickoff.md`; it
never infers mode from another feature or an unscoped session value. When
`Execution mode: auto`, the calling workflow dispatches the Agent tool with
`subagent_type: "samsara:auto-gatekeeper"`, supplies the context below, and
waits. The Gatekeeper validates and atomically appends the decision to
`changes/<feature>/auto-decisions.md` before returning. This log is append-only.
The caller applies the validated `proceed`, `revise`, `reject`, or `accept_gap`
result; it never writes the decision itself. Stage sections may narrow the
allowed values but may not redefine them.

The append target and compact fields live in the Decision Log Contract and Entry
Shape below:

- `proceed` continues with the concrete answer.
- `revise` revises the owning artifact or evidence, then the same gate re-runs.
- `reject` stops the current auto path.
- `accept_gap` continues only when the named gap remains visible in a downstream
  artifact.

Every dispatch supplies:

- `feature_dir`
- `stage`
- stable `gate_id`
- exact `workflow_prompt`
- concrete `options`, when the prompt offers choices
- `allowed_decisions`
- `authority_refs` and `evidence_refs`
- `mandatory_constraints`
- Codebase Map ref and state: `fresh | stale | missing`
- prior decision ref when the same gate is re-run

The Codebase Map provides broad structural awareness. Feature artifacts provide
current change authority. Targeted live code, validator output, and committed
evidence provide current truth. When the map conflicts with live code, live code
wins and the drift stays visible. Do not crawl the repository without a decision
need; verify the supplied refs and anchors first.

## Decision Log Contract

`auto-decisions.md` is an append-only event log, not a report or a second copy of
stage artifacts. Every entry uses a stable Markdown heading followed by exactly
one YAML block. Existing entries must not edit prior records. A correction or
re-run appends a new entry whose `supersedes` names the superseded decision.

Before append, write the candidate entry under `/tmp`. Invoke the Gatekeeper's
companion validator once with `--append-candidate`; it locks the feature log,
rechecks current history plus the candidate, and replaces the log atomically
only when clean. Do not validate and append as separate commands. Do not write
the log directly.

A generic approval is invalid. `answer` must be question-specific and preserve
the original workflow prompt. `reason` contains only facts that changed the
decision. Put supporting detail in durable evidence and cite it instead of
restating it.

## Entry Shape

````md
## decision-001 — research.problem-source

```yaml
schema_version: 1
decision_id: decision-001
timestamp: "<ISO-8601 timestamp>"
decided_by: auto-gatekeeper  # auto-gatekeeper | human
stage: research
gate_id: research.problem-source
workflow_prompt: "<exact original prompt>"
answer: "<concise, question-specific answer>"
decision: proceed  # proceed | revise | reject | accept_gap
reason:
  - "<one decision-changing fact>"
evidence_refs:
  - "<durable evidence pointer>"
uncertainty:
  level: low  # low | medium | high
  notes: none
next_action:
  type: continue  # continue | revise_and_rerun | stop
  target: "<stage, artifact, skill, or prepared delivery action>"
gap: null
supersedes: null
```
````

`reason` contains one to three bullets. Architecture or principle reasoning goes
there only when it changes the ruling; never create filler to make a decision
look Staff-level. `evidence_refs` remains non-empty.

For `accept_gap`, replace `gap: null` with:

```yaml
gap:
  summary: "<named unresolved fact>"
  durable_ref: "<owning stage artifact ref>"
  owner: "<who resolves or observes it>"
  recheck_when: "<observable trigger>"
```

## Decision Semantics

- `proceed` → `next_action.type: continue` and apply the concrete answer.
- `revise` → `next_action.type: revise_and_rerun`; the owning stage changes its
  artifact or evidence, then re-runs the same gate with a new decision that
  supersedes this one.
- `reject` → `next_action.type: stop`; no later gate treats it as proceed.
- `accept_gap` → `next_action.type: continue`; the gap is named both here and in
  the stage-owned durable artifact consumed downstream.

An explicit human override during an auto run is appended by the gatekeeper with
`decided_by: human` and the exact human answer. The gatekeeper records rather
than reinterprets it.

## Stable Gate IDs

Definitions are fixed; do not rename or reuse them for a different question.
Instance suffixes identify the existing group, task, scar, round, or validation
condition rather than inventing a new semantic family.

- Research: `research.problem-source`, `research.do-not-solve`,
  `research.damage-recipient`, `research.done-state`, `research.transition`.
- Codebase Map: `codebase-map.update-strategy`, `codebase-map.review`.
- Pre-thinking: `pre-thinking.step5.<group>.<question>`,
  `pre-thinking.evaluator`, `pre-thinking.commitment`.
- Planning: `planning.transition`.
- Implementation: `implementation.strategy`,
  `implementation.review-arbitration.<task>.<round>`.
- Iteration: `iteration.entry-unknown`,
  `iteration.disposition.<scar-id>`, `iteration.blocked-fix.<scar-id>`,
  `iteration.round.<n>`.
- Validation: `validation.empty-diff`, `validation.base-branch`,
  `validation.security-capability`, `validation.security-result`,
  `validation.security-risk`, `validation.delivery`.

## Allowed Decisions

- Research questions and the Research, Pre-thinking, and Planning transitions:
  all four decisions. Their accepted gaps must resolve to Research autopsy,
  Pre-thinking commitment, or Planning Source Contract refs respectively.
- Pre-thinking Step 5 questions and evaluator selection: all four decisions;
  accepted gaps live in `pre-thinking.md`.
- Implementation review arbitration: all four decisions; an accepted concern
  lives in the Scar or review record.
- Implementation strategy: `proceed | revise | reject`.
- Iteration unknown: `revise | reject`.
- Iteration disposition and blocked-fix handling:
  `proceed | revise | reject`; the concrete answer selects the Scar disposition.
- Iteration round continuation: `proceed | reject`.
- Validation gates: `proceed | revise | reject`. `accept_gap` cannot override
  security, Primary evaluator, format, open or blocked Scar, review evidence, or
  final delivery selection.

## Validation

Run the validator shipped with the installed auto-gatekeeper companion:

```text
uv run python <installed-auto-gatekeeper-companion-directory>/scripts/validate_auto_decisions.py changes/<feature>/ --repo-root <repo-root>
```

Exit `0` is clean, `1` is format findings, and `2` is cannot validate. Only a
clean appended decision has workflow authority. When the Gatekeeper cannot
determine whether the gate can pass from available evidence, the result is
unknown and must not transition as if the gate passed.

`<installed-auto-gatekeeper-companion-directory>` is a platform integration
path. `samsara-cli` must install and resolve it with the agent; callers must not
substitute a Research, Bootstrap, or Validate & Ship skill directory.

## Security And Privacy Unknowns

Auto mode cannot accept a security/privacy unknown or risk. Validate & Ship Step
0 owns the exact decision procedure; the gatekeeper records `revise` when a
fixable result returns through Iteration and `reject` when evidence cannot make
the gate safe.
