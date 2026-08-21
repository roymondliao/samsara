# Golden re-expression: task-4-scar.yaml (232 lines) -> golden_task4_slot_form.yaml (75 lines)

Task-5 acceptance artifact (not a scar report — no line budget applies to
this file itself). Source (read-only, never modified):
`changes/2026-07-02_workflow-subtraction-optimization/scar-reports/task-4-scar.yaml`.
Golden fixture: `tests/fixtures/scar_reports/golden_task4_slot_form.yaml`
(validator-clean — see `tests/test_skills/test_format_validators.py::test_golden_task4_re_expression_validates_clean`).

Every distinguishable content point in the source is accounted for below.
"Destination" is one of: a golden fixture item, `review-record.md` (round-by-round
review verdicts — go-elsewhere), the commit message (before/after counts —
go-elsewhere), a fold into an existing item (compressed, not lost, fold
explicitly noted), or an explicit deletion with a one-line reason (the only
case where content is not carried forward anywhere).

**Destination semantics (verifiability boundary):** for go-elsewhere rows
(`review-record.md` / commit message), the destination is **prescriptive** —
where the CURRENT go-elsewhere contract says such content belongs for new
reports — not a descriptive claim that this historical content exists there.
The source feature (shipped 2026-07-04, eb4ae07) predates the
`review-record.md` convention (no such file exists in its directory), and
eb4ae07's commit message carries only feature-aggregate figures, not the
per-task numbers cited below. Nothing was moved; the golden fixture itself
preserves every scar fact, and go-elsewhere rows document only where the
non-scar content WOULD live under the new contract.

| Source (line range) | Content | Destination | Note |
|---|---|---|---|
| 1-2 | `task_id`/`completion_status` header | golden header (unchanged) | direct |
| 4-20 `known_shortcuts[0]` | Auto Mode Gate pointer sections exceed the task's own "<=8 line" cap (per-skill counts) | golden `known_shortcuts[0]` | direct, compressed |
| 20 (sub-clause) "Recorded per the task's explicit request, not because it is unresolved debt..." | self-justifying process defense | **deleted** | reader gains nothing beyond `accepted_because`, which already states why it was accepted; this clause only pre-empts a reviewer's doubt, no future action changes |
| 22-46 `known_shortcuts[1]` | canonical increment (+27) vs skills decrement (-46) ratio, not "far smaller" in a strict sense | golden `known_shortcuts[1]` | direct, compressed |
| 22-46 (inline per-stage numbers: research 22->16, pre-thinking 24->18, ...) | before/after raw-line table (embedded in prose here, and again in `narrative` below — the source duplicates it) | commit message | go-elsewhere: before/after counts |
| 48-70 `known_shortcuts[2]` (Step 0 body vs Auto Gate overlap) | validate-and-ship Step 0 still generally restates unknown/fail meaning, overlapping the Auto Gate override list | golden `known_shortcuts[2]` | direct, compressed |
| 71-80 "FINAL DISPOSITION (quality review verdict, accepted by main agent)... Accepted, not re-deferred." | round-by-round review verdict prose | `review-record.md` | go-elsewhere: review verdict history |
| 78-80 `re_review_signal` + `owner` | concrete recheck condition + accountable party | folded into golden `known_shortcuts[2].accepted_because` ("re-review when either wording changes") | compressed, not lost — owner detail (change's own author) is implicit in "re-review when X changes" and not restated verbatim per write-filter (a name is not more actionable than the trigger condition) |
| 81-83 "Additionally fixed this round (quality Important): ...auto-mode.md ... trimmed ... (no test pinned it)" | a fix was made with no test guarding regression | golden `silent_failure_conditions[4]` (auto-mode.md trim, no test) | direct, new item — this is itself a genuine silent-failure fact, not process narrative |
| 85-92 `silent_failure_conditions:` header + `[0]` | `systemic_ref: doc-vs-runtime-obedience` | golden `silent_failure_conditions[0]` | direct, already systemic_ref form |
| 94-104 `silent_failure_conditions[1]` (first half) | anti-dup test matches VERBATIM substrings only; paraphrase re-embedding undetected | golden `silent_failure_conditions[1]` | direct, compressed — split out of the source's single bundled item (see next row) |
| 105-111 "HONESTY CORRECTION (review round): this was NOT hypothetical — yin review proved..." | round-by-round review verdict narrative | `review-record.md` | go-elsewhere: review verdict history |
| 108-111 (the concrete fact: 5 residue lines existed and were deleted) | a live instance had shipped and was fixed | golden `silent_failure_conditions[2]` (status: resolved) | direct — split into its own item since it is a *resolved* fact, distinct from the *permanent accepted* VERBATIM-only limitation in row above; one item = one death-reason |
| 112-113 (old-form `status`/`resolution` at the bundled item's level) | the fix description | folded into golden `silent_failure_conditions[2].resolution` | direct |
| 115-147 `assumptions_made[0..3]` | 4 verified assumptions with grep/pytest evidence pointers | golden `assumptions_made[0..3]` | direct, near-verbatim (already matches the verified-pointer slot form) |
| 149-156 `debt_registered`/`debt_location` | debt flag + location prose | golden `debt_registered`/`debt_location` | direct, condensed to one line |
| 158-175 `resolved_items[0]` | anti-dup predicate initially matched only 1 of 4 canonical decision values (`revise`), broadened to all 4, verified by injection | golden `silent_failure_conditions[3]` (status: resolved) | direct — old schema's separate `resolved_items` list form replaced by resolved-in-place per the current schema's `resolved-in-place` rule |
| 177-194 `resolved_items[1]` | 3 literal test-required phrases split mid-phrase by a markdown line-wrap; fixed by re-wrapping | golden `known_shortcuts[3]` (status: resolved) | direct — same resolved-in-place migration |
| 196-212 `narrative` before/after raw-line table (6 stages, plus lines 210/212: canonical +27 and net -19) | before/after line counts | commit message（規範性去向，見上方 Destination semantics） | go-elsewhere: before/after counts (duplicate of the row-22-46 occurrence — same destination); the +27/-19 figures themselves are also preserved as scar content in golden `known_shortcuts[1]` |
| 214-223 `narrative` "Design choices not built... second canonical home... only ONE consumer..." | Structural Honesty refusal (no second canonical home for the Required Fields list) | golden `narrative` | direct, condensed — kept as `narrative` prose rather than manufactured into a `structural_decisions` entry: the source predates the `structural_decisions` concept entirely, and fabricating a `forced_by` citation for a historical decision after the fact would violate `forced-by-evidence` (post-hoc rationalization) |
| 225-229 "Baseline: 803 passed... Final: 829 passed (803 + 26 new tests...)" | test count before/after | commit message | go-elsewhere: before/after counts |
| 230-232 "Zero regressions in any pre-existing test... including test_security_gate_fold.py... verified unchanged and still green" | regression claim | **no new destination — already captured** | duplicates the evidence pointer already in golden `assumptions_made[3].note` (`test_security_gate_fold.py -> 21 passed, unchanged`); restating it a second time would be exactly the re-duplication this feature exists to remove |

## Judgment calls closest to the boundary (flagged in the scar report)

1. Splitting the source's single bundled `silent_failure_conditions[1]` item
   (VERBATIM-only limitation + the "5 residue lines" fix, mixed together under
   one `status: resolved`) into two golden items — one permanent/accepted, one
   resolved. This is a judgment call: the source's own status marking treated
   the whole bundle as "resolved," which is imprecise (the VERBATIM-only
   limitation itself was never resolved, only the one live instance was). The
   split is more honest to the current schema's one-item-one-death-reason
   shape, but it is an interpretive act, not a mechanical transcription.
2. Folding `re_review_signal`/`owner` into `accepted_because` prose instead of
   inventing new schema fields for them. The current schema has no dedicated
   slots for these; compressing them into one sentence risks losing the
   "who is accountable" specificity a future reader might want.
3. Whether the "Additionally fixed this round... no test pinned it" sentence
   (source lines 81-83) is a genuine silent-failure condition (this golden's
   classification) or process narrative belonging in review-record.md. It
   describes a state that persists (no test), not a review verdict about a
   past round — classified as a silent-failure condition.
4. Go-elsewhere destinations are prescriptive, not historically verifiable
   for this source (see Destination semantics above) — the review verdicts
   and per-task counts routed to `review-record.md`/commit message have no
   real landing site in the 2026-07-02 feature, which predates those
   conventions. First drafts of this table presented them as if descriptive;
   yin review caught the over-claim.

## Counts (measured, not estimated)

- Golden fixture: 75 physical lines (`wc -l`), validator-clean (0 findings).
- Traceability rows above: 22, covering every distinguishable content block
  in the 232-line source with a destination (zero silent drops).
- Mechanical line-coverage check (re-run after yin review corrected an
  earlier over-claim that missed source lines 210/212): with row ranges as
  cited above, exactly 12 of the source's 232 lines are uncovered —
  lines 3, 21, 47, 84, 93, 114, 148, 157, 176, 195, 213, 224 — every one a
  pure blank separator (script-verified, reproducible). This proves
  structural (line-range) completeness only — semantic correctness of each
  row's classification is judgment, not mechanically checked (see judgment
  calls above).
