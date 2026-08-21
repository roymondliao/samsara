# Planning Flow — Canonical Procedure

**Sole owner: executable procedure.** SKILL.md owns entry and the artifact graph;
templates own shapes. Planning translates authority into executable work without
reopening upstream design judgment.

## 1. Input Gate

Read `1-kickoff.md` and `problem-autopsy.md`. Read the complete
`pre-thinking.md`; Step 6 refs are an index, not a substitute for the source.

Resolve every L1 ref from Step 6 back to its original declaration before making
Planning judgments. The handoff must resolve to exactly one `PT-CI` in Step 2
and every cited `PT-S*` in Step 4. Missing, duplicate, or dangling refs are an
incomplete Pre-thinking handoff; STOP and return to `samsara:pre-thinking`.
Never replace a broken ref with copied or re-derived content.

Continue only when all of these are true:

- Step 6 commitment is Proceed or Accept gap.
- Core identity has `PT-CI`.
- Every design decision used by Planning has a unique `PT-D*` ID.
- Every real seam has a unique `PT-S*` ID and semantic name.
- Evaluation Contract has `PT-EVAL`.

Otherwise STOP and return to `samsara:pre-thinking`.

Accepted gaps remain visible as source refs; Planning must not silently resolve
them into a convenient assumption.

### Stable ID contract

Planning adds two fixed ID families: `PL-D*` (Planning Decision) and `AC-*`
(Acceptance Contract Scenario). The upstream `PT-*` meanings remain owned by
Pre-thinking.

Once referenced downstream, an ID and its canonical label are immutable: never
renumber, reuse, or repurpose either one. A semantic replacement, split, or merge
gets a new ID and updated refs. Human-facing Markdown writes every authority ID
(`ID (canonical label)`) so the reader sees both the machine key and its meaning.
Canonical labels are short semantic phrases without parentheses.
YAML reference fields (`planning_refs`, `decision_refs`, `acceptance_refs`,
`source_refs`, and `evaluator_ref`) keep bare IDs only. The validator checks
reference labels against their declarations; it does not judge label quality.

## 2. Planning Judgment and Acceptance

Write `2-plan.md` from `templates/plan.md`.

- Allocate `PL-D*` only for Planning judgments: task boundaries, file allocation,
  ordering, and how acceptance maps to work.
- The text after each `PL-D*` heading is its canonical label.
- Every `PL-D*` cites the `PT-*`, research, or live-code evidence that forces it.
- Do not copy upstream rationale as a new decision and do not allocate `PT-*` IDs.
- Record unresolved Planning assumptions explicitly.

Write `acceptance.yaml` from `templates/acceptance.yaml`:

- Use stable `AC-*` IDs and cite source refs.
- Give each scenario one semantic `label`; it is the ID's canonical human
  resolver and cannot change while the ID remains live.
- Put silent failure and other applicable death paths before happy paths.
- Add degradation or unknown-outcome scenarios only when the system can actually
  enter those states. Otherwise record the type under `not_applicable` with a
  concrete rationale; never invent behavior to fill the template.
- `unknown` is required only at boundaries where the outcome can genuinely be
  indeterminate. Never treat unknown as success or failure.
- Scenarios may support `PT-EVAL`; they cannot replace it.

Reference taxonomy: `death-first-spec.md`.

## 3. File Allocation Consistency — STOP Gate

Record the global file allocation in `2-plan.md`. Compare every placement or
ownership consequence against its cited upstream decision:

- **matches** — all paths honor the decision.
- **contradicts** — at least one path violates it.
- **out of scope** — the decision constrains no path.

**STOP on contradicts.** Revise the allocation or return to Pre-thinking when
the upstream decision itself must change. Do not proceed to task decomposition.

**Anti-bias:** derive paths from the cited placement/ownership decisions before
accepting the proposed file allocation; do not use the allocation to rationalize
those decisions after the fact.

## 4. Task Decomposition and Reference Graph

Create `index.yaml` and task files together.

- A task is dispatch-complete through its work order, Overview projection, Index
  references, and live anchors; do not copy all upstream context into the task.
- `depends_on` owns ordering; `affects` owns reverse structural impact. Neither
  substitutes for the other.
- An `affects` entry that only restates ordering is noise.
- `anchors` are live starting points, never a whitelist or prose interface copy.
- Each task cites its `PL-D*`, `PT-*`, and `AC-*` refs.
- Each task names exactly one semantic seam or `null`.
- Each task names an observable Unit Test Contract source.
- If a needed seam has no `PT-S*` source, STOP and return to
  `samsara:pre-thinking`; do not invent one in Planning.

Planning may add `planned` task IDs to a referenced seam as a planned-change
evidence tier. This strengthens the evidence; it does not create or revise the
seam decision.

Keep projection volume consumption-driven, not line-count-driven:

- **over-projection:** an `affects` entry no implementer cites through scar
  `forced_by` evidence.
- **under-projection:** downstream work tears structure because a real impact was
  missing.
- A large `affects` set is a signal to reconsider task boundaries, not a reason
  to enforce an arbitrary cap.

Task files use `task-format.md`. They specify goal, files, constraints, contract,
death-test requirements, and assumptions to verify. Implement owns test order,
review dispatch, scar generation, commits, and report-back procedure.

## 5. Derived Overview

Generate `overview.md` only after decomposition.

- Materialize the minimum shared context Implement dispatches repeatedly.
- Every projected decision or seam carries its upstream `source_ref`.
- Planning-specific consequences cite `PL-D*`; design consequences cite `PT-*`.
- Do not add decisions, death-case summaries, file maps, or task-local steps.
- Treat Overview as regenerable. When an upstream source changes, regenerate it
  before validation.

## 6. Format Validation

Resolve the validator from Planning's installed skill directory; do not assume
the target repository contains Samsara's source tree. Run it against the
feature directory with `uv`:

```text
uv run python <installed-planning-skill-directory>/scripts/validate_format.py changes/<feature>/
```

Exit `0` is clean, `1` is findings, and `2` is cannot-validate/unknown. Only `0`
may enter the transition gate.

The validator owns machine-decidable checks: IDs, source refs, task files,
acceptance refs, dependency cycles, seam resolution, affects, anchors, and
planned task refs. It never judges whether a decision, seam, or scenario is good.
Judgment remains with the responsible author or reviewer. Missing validator
output is a visible missing, never a silent skip.

## 7. Transition

Use one canonical prompt:

> Planning complete. The authority graph, acceptance contract, task graph, work orders, and derived Overview validate cleanly. Proceed to Implementation?

- If `Execution mode: human-in-the-loop`, ask the user this prompt.
- If `Execution mode: auto`, do not ask the user. Dispatch
  `samsara:auto-gatekeeper` with gate ID `planning.transition` and this exact
  prompt, then wait for its validated decision. The Gatekeeper alone appends
  `auto-decisions.md`.
- Proceed invokes `samsara:implement`; revise updates artifacts and re-runs
  validation; accept-gap first records its ref and consequence in the plan's
  Source Contract, then keeps it visible to Implement.
