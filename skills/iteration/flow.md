# Iteration Flow — Executable Authority

This file is the sole procedural authority for Iteration. Scar reports are the item-level SSOT; read and update them in place. A wound is a scar item whose status is not `resolved`. Do not create a normalized scar inventory.

## Step 0: Restore Durable State

Read, in order:

1. `index.yaml`, including `iteration_entry` and every task's refs, seam, affects, and anchors.
2. `pre-thinking.md` for `PT-EVAL` (Primary evaluator, pass/fail signals, and Feedback loop).
3. Every file in `scar-reports/`.
4. `changes/<feature>/review-record.md` for each reviewer verdict, its reasoning, and any arbitration result.
5. When auto mode was used, `changes/<feature>/auto-decisions.md` for prior gate decisions.
6. Git history and working-tree status.

Resume from these artifacts, never from conversation memory. The review record is read-only evidence for feature-level triage; it does not own scar lifecycle state. Auto decisions retain gate authority, and Git history retains round chronology. Write item dispositions only to the original scar items.

Run the Planning and Implement format validators before triage. A finding blocks the clean path. `CANNOT VALIDATE`, missing input, or unreadable evidence is `unknown`, never pass.

## Entry Triage

Iteration is the sole owner of this decision. Every completed implementation enters this cheap triage-only pass; entry does not start fix rounds.

1. Read the direct scar set using Step 1. Do not persist a normalized copy.
2. Run, inspect, or apply `PT-EVAL` exactly as written.
3. Classify Scar items whose current status is `open` with full feature context:
   - `task-local`: one task owns the repair; no shared boundary changes.
   - `feature-level`: the repair requires shared feature authority.
   - `cross-task/system-level`: the same underlying cause crosses tasks, touches a shared boundary, or one task harms another. Equivalent causes remain cross-task when wording differs.
   - `evaluator-failure`: the canonical pass signal does not hold.

`signal_lost` is the count of unresolved scar items. It describes remaining exposure, prioritizes work, compares rounds, and detects stagnation. It is not risk severity and never decides whether an item deserves repair.

Choose one route:

- `skip_rounds`: formats and refs are clean, the Primary evaluator (`PT-EVAL`) passes, and no actionable item remains. Accepted items require rationale, `re_review_signal`, owner, and evidence refs; deferred items require target, `resume_when`, owner, and evidence refs.
- `fix_rounds`: at least one item needs a disposition or repair, or `PT-EVAL` fails.
- `unknown`: a report/ref cannot be parsed or `PT-EVAL` cannot run. List the exact missing evidence; never skip.

In `index.yaml`, replace `iteration_entry: null` with this mapping before branching:

```yaml
iteration_entry:
  status: in_progress
  route: <skip_rounds | fix_rounds | unknown>
  round: 0
  evaluator: <pass | fail | unknown>
  signal_lost: <non-negative integer>
  stagnation_count: 0
  reason: "<one-line evidence-backed result>"
  last_commit: null
  reversible: true
```

For `unknown`, `Execution mode: human-in-the-loop` asks the user to repair the input or record the visible gap. With `Execution mode: auto`, do not ask the user; dispatch `samsara:auto-gatekeeper` and append its decision. Recording a gap does not turn unknown format/evaluator evidence into pass; the transition remains blocked until its gate is satisfied.

## Step 1: Aggregate Remaining Scars

Read scar items directly; do not generate another artifact.

- Current lifecycle: `resolved` is excluded. `open`, `accepted`, `deferred`, and `blocked` remain visible. `iteration: null` alone never means resolved.
- Gen 1 plain string, Gen 2 description dict, and Gen 3 what/bites_when slot items remain readable by shape; no `schema_version` exists.
- Plain string format backward compatibility: do not reject or silently skip plain string format items. Missing deferred flag = false; missing resolved_items = no self-iteration.
- The legacy `resolved_items` list and in-place `status: resolved` (`resolved-in-place`) both exclude the matched item. The legacy-generation reading guarantees continue to apply unchanged: current lifecycle fields are additive, not a replacement for reports already on disk (`legacy-invalid`).
- An unrecognized shape is a parse failure. Name the report; never silently skip it.

Resolve every `systemic_ref` (`systemic-ref`) through `.samsara/systemic-scars.yaml`:

- Registry exists and the ID is present: use the registry description as triage context.
- Registry exists but ID is dangling: parse failure; name report and ID. Never silently skip it.
- Registry is missing or unreadable: mark the item `unknown`, count it, and pass it through the gate. It is not dropped or silently disappeared.

All three generations count toward `signal_lost` identically. Count non-resolved known shortcuts, silent failure conditions, and unverified assumptions. A `systemic_ref` keeps the category in which it appears. Current lifecycle items follow the same rules. The number is an observation, not an entry threshold.

**Parse failure handling:** Non-YAML reports, unrecognized shapes, and dangling refs are parse failures. This is not the old plain-string format: `legacy-invalid` requires counting that format normally and never treating it as a parse failure.

If `PT-EVAL` fails, append an `evaluator-failure` wound to the affected task's scar report with the next unused file-scoped `SC-*` ID. If no task owns the failing surface, record `unknown`; do not invent a feature-level scar file.

## Step 2: Triage (Execution-Mode Gate)

For every `open` current item or unresolved legacy item, choose one disposition:

- `fix`: actionable code/test change. Keep `status: open`; set `iteration` to round, `action: fix`, and evidence refs.
- `accept`: known exposure with no current repair. Set `status: accepted`; require rationale, `re_review_signal`, owner, and evidence refs.
- `defer`: intentionally outside this delivery. Set `status: deferred`; require target, `resume_when`, owner, and evidence refs.
- `blocked`: use only after a selected fix cannot proceed. Require blocker, owner, and evidence refs.

With `Execution mode: human-in-the-loop`, present concise bullets and let the user decide. With `Execution mode: auto`, do not ask the user; dispatch `samsara:auto-gatekeeper`, append the decision, then apply it.

Write each disposition immediately to the original item. Preserve `scar_id` and every original wound field; they are immutable. If an original fact is wrong, append a new item that cites the old one. Do not attach lifecycle state to `structural_decisions`; create a wound that references the decision instead.

When first touching a legacy item, assign the next unused file-scoped `SC-*` ID and add the current lifecycle fields. Never renumber or reuse an ID. Cite items as `scar-reports/<file>#SC-N`.

## Step 3: Fix (Per-Fix Commit)

Iteration selects the wound; Implement owns implementation and review orchestration. Invoke `samsara:implement` with an iteration work order containing:

- `scar_ref` and affected task IDs.
- The complete compact `overview.md` for broad structural awareness.
- The affected tasks' PT/PL/AC refs plus seam, affects, and anchors from `index.yaml`.
- `PT-EVAL` failure evidence and Feedback loop when applicable.
- Expected behavior change, current round, signal_lost, and stagnation count.

Do not curate code excerpts or paste a second scar inventory. Implement pulls live code from anchors and the worktree, applies its normal death-test, test-contract, reviewer, review-record, and arbitration authority, then returns evidence refs before the main-agent commit.

After both Implement reviewers pass, update the original wound to `status: resolved`, add one-line `resolution`, and set iteration action to `fixed` with round and evidence refs. Run the scar validator, then commit code, tests, scar state, and checkpoint together. The commit message cites the full scar ref.

If the fix returns `BLOCKED` or `NEEDS_CONTEXT`, do not retry silently. Record `status: blocked`. With `Execution mode: human-in-the-loop`, ask whether to supply context or defer. With `Execution mode: auto`, do not ask the user; dispatch `samsara:auto-gatekeeper` and record the decision. A fix that reveals another wound appends it to the affected task scar with a new ID, `status: open`, and `iteration: null`.

## Step 4: Round Check + Safety Valve

After a round, reread scars and recompute signal_lost. Record the new count and round in `iteration_entry`.

Show these observations before the continuation decision:

- Round 3 or later.
- Two consecutive rounds without lower signal_lost.
- More new wounds than resolved wounds in the round.

These are advisory safety signals, not deterministic stop rules. After showing them, run the execution-mode gate. With `Execution mode: human-in-the-loop`, ask continue/stop. With `Execution mode: auto`, do not ask the user; dispatch `samsara:auto-gatekeeper` and record the decision. Never gate repair eligibility on a signal_lost threshold.

Stopping cannot hide an item selected for fix. Resolve it or reclassify it as accepted, deferred, or blocked through the active gate.

## Validation Re-entry

Validate & Ship never changes code, tests, or Scar lifecycle. When it returns a
validation finding, Iteration owns the re-entry. Read the item from
`validation.findings` in the committed manifest and resolve its candidate from
`snapshot.candidate_commit`. The manifest template is the shape authority;
`ship-manifest.md` defines field meaning. Run Validate's format validator and
reject an unresolved finding ref rather than maintaining another field list.

Map a code, test, or Scar finding to the affected task through its path,
location, `index.yaml` file allocation, and refs. Preserve the upstream Feedback
loop when `PT-EVAL` produced the finding. If no task owns the surface, set the
`status` field under `iteration_entry` in `index.yaml` to `blocked`, record the
missing ownership evidence, and do not invent a feature-level Scar file.

For an owned finding:

1. Append a new stable `SC-*` wound to that task's Scar report, citing the full
   `ship-manifest.yaml#VF-N` finding ref. Reuse an existing open wound when it
   already names the same fact; never duplicate it for a second observation.
2. In the existing `iteration_entry` mapping, set `status` to `in_progress`,
   route to `fix_rounds`, and run the normal Triage contract.
3. Invoke `samsara:implement` through Step 3. Implement's SKILL is canonical for
   code, test, review, and review-record execution. This flow owns only the
   validation work order and re-entry boundary.
4. Resolve or classify the wound through the normal lifecycle. Run all format
   validators, commit the new candidate, and complete Step 5.

After the new `ready_for_validation` checkpoint is committed, return to
Validate & Ship. Validation discards results for the old candidate and reruns
Security Step 0 against the full base-to-candidate diff.

## Step 5: Commit and Transition

Before `samsara:validate-and-ship`:

1. Run Planning and Implement format validators; findings block transition and unknown is not pass.
2. Commit every remaining scar disposition and `iteration_entry` change.
3. In the existing `iteration_entry` mapping in `index.yaml`, preserve every other field, set `status` to `ready_for_validation`, and set `last_commit` to the verified content/disposition commit. Commit this checkpoint.
4. Verify the working tree is clean and the branch contains committed changes.

If any condition fails, set the `status` field under `iteration_entry` in `index.yaml` to `blocked`, record the exact reason in a committed checkpoint, and do not transition. On success, invoke `samsara:validate-and-ship`.

Report results in concise bullets: route, rounds, signal_lost before/after, resolved refs, accepted refs, deferred refs, blocked refs, evaluator result, and final commit.
