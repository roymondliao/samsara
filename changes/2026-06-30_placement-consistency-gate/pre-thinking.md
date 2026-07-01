# Pre-thinking: placement-consistency-gate (A4 / ISSUE-001)

## Session: 2026-06-30

## Step A — Design and Gap Map

### Atomic Context Boundary (live facts derived)

- **Reviewer dispatch payload** (`skills/implement/dispatch-template.md`): both reviewers are dispatched per-task with `Task Requirements` (acceptance criteria from task-N.md), `Changed Files`, `Diff`. **Key Decisions / overview.md are NOT passed.** Same in `skills/iteration/SKILL.md` Step 3 fix dispatch.
- **Two reviewers** (`skills/implement/SKILL.md`): `samsara:code-reviewer` (yin — described as "spec compliance, deletion, naming, silent rot, correctness") and `samsara:code-quality-reviewer` (structural S/O/L/I/D + Cohesion/Coupling/DRY/Pattern).
- **code-reviewer.md** review order = 6 steps (Deletion, Naming, Silent Rot, Test Quality, Scar Integrity, Correctness). **No architectural-placement step.** Domain-driven (loads `references/<domain>-review.md`); placement-vs-decision is not a code-domain pattern.
- **Planning** (`skills/planning/SKILL.md`): produces `overview.md` with independent `## Key Decisions` (template line 12) and `## File Map` (line 22). No consistency step between them; the transition goes straight from output to implement.
- **Fast-track** does inline self-review (yin + C5-C8), no subagent — a separate review path.
- **Existing pattern to reuse:** the codebase-map Task 3 / implementer-rules work guarded doc rules with `tests/test_skills/` and `tests/test_agents/` doc-contract tests (presence + ordering). Same shape applies here.

### Information Gaps
`gaps: none identified` — the live dispatch flow, reviewer structure, and template structure are all verified above. No missing facts block planning.

### Design Decision Gaps

#### Gap D1: which reviewer owns architectural placement
**Question:** Should the placement/ownership check live in `samsara:code-reviewer` (yin) or `samsara:code-quality-reviewer` (structural)?
**Hypothesis:** Yin `code-reviewer` — placement = "does the implementation match the plan's architectural DECISION" = spec/plan compliance, which the implement skill already nominally assigns to the yin reviewer; and Mother Rule 2 (boundaries must label assumptions) fits "a file placed against its stated ownership is an unlabeled contradiction." Quality reviewer's Coupling is about code structure, not plan-decision compliance.
**Planning impact:** Determines which agent file gets the new review dimension and which reviewer's dispatch must carry Key Decisions.

#### Gap D2: how a placement/ownership Key Decision is identified
**Question:** Does the planning self-check and the reviewer identify "placement decisions" by pure judgment, or does the overview template gain a light convention to mark them?
**Hypothesis:** Pure judgment (user chose option b — independence, not a structured field). The reviewer/self-check reads Key Decisions and judges which are placement/ownership-related. Optionally the planning skill *encourages* phrasing placement decisions explicitly (a prose convention, not a parseable field) — but no machine-checkable `ownership:` field, and the overview template's two sections stay as-is.
**Planning impact:** Whether `templates/overview.md` changes (a field/convention) or stays; the precision of the self-check.

#### Gap D3: data-flow scope — which dispatch paths carry Key Decisions
**Question:** Key Decisions must reach the reviewer in implement and iteration; does fast-track's inline review also get a placement check?
**Hypothesis:** Implement + iteration dispatch templates carry Key Decisions (the two subagent-review paths). Fast-track is OUT — it's for small (<100-line) changes where feature-level placement contradictions are not the failure mode; adding it there is friction without payload. Planning impact: 2 dispatch templates change (implement, iteration), not 3.

#### Gap D4: planning self-check is a STOP gate, not advisory (resolved by hypothesis)
**Question:** Is the planning consistency check a hard STOP or an advisory note?
**Hypothesis:** Hard STOP before task decomposition on a genuine contradiction (issue.md fix #1, research kill-condition: a soft/advisory check is exhortation #2). Proceeding on this unless D1/D2 move it.

---

### Group 1: design decisions (round 1)

**Q1 (D1 — which reviewer):** Where does the architectural-placement dimension live?
**A:** The yin `samsara:code-reviewer`. Placement = "does the implementation match the plan's architectural decision" = spec/plan compliance (already nominally the yin reviewer's scope), and Mother Rule 2 fits "a file placed against its stated ownership is an unlabeled contradiction." The `code-quality-reviewer` is NOT changed.

**Q2 (D2 — how identified):** Judgment vs structured field vs overview template change?
**A:** Pure judgment, no template change. The planning self-check and the reviewer read Key Decisions and judge which are placement/ownership-related; no machine-checkable `ownership:` field, `templates/overview.md` two sections stay as-is. Independence (the fresh reviewer) is the anti-bias mechanism, not a field.

**Q3 (D3 — data-flow scope):** Which dispatch paths carry Key Decisions?
**A:** Implement + iteration reviewer dispatch templates carry Key Decisions. Fast-track is OUT (small <100-line changes; feature-level placement contradiction is not its failure mode — would be friction without payload).

### Resolved by hypothesis (no question needed)
- **D4 (STOP vs advisory):** Hard STOP before task decomposition on a genuine contradiction. A soft/advisory check is exhortation #2 (research kill-condition).

---

## Evaluation Contract

**Primary evaluator:** A pytest doc-contract test suite over the changed framework files.
**Agent can perform it by:** `uv run pytest <test-path>` (AGENTS.md: activate `.venv`, `uv run pytest`). The suite asserts: (1) `skills/planning/SKILL.md` contains a File-Map↔Key-Decisions consistency-check step that STOPs on contradiction before task decomposition; (2) `agents/code-reviewer.md` contains an architectural-placement review dimension scoped to placement/ownership Key Decisions; (3) **the data flow** — both the `skills/implement` reviewer-dispatch template AND `skills/iteration` reviewer dispatch include the plan's Key Decisions in the reviewer payload.
**Pass signal:** All three assertions green, especially (3) — Key Decisions provably reach BOTH reviewer dispatch paths.
**Fail signal:** Any of: planning has no STOP consistency step; code-reviewer has no placement dimension; OR the placement dimension exists but a dispatch template does not carry Key Decisions (the corruption signature — a gate that checks against nothing).
**Feedback loop:** If (3) fails while (2) passes, fix the dispatch template (the data flow) first — a placement dimension with no Key Decisions is worse than none (false assurance). Do not mark validation complete on (1)+(2) while (3) is red.
**Out of scope validation:** Runtime obedience — whether the planning agent actually STOPs, and whether the reviewer actually catches a real placement contradiction — is agent-behavior, validated by dogfood (a deliberately contradictory plan), not by this suite. Same limitation as the codebase-map Task 3 doc contracts.

## Step C — Commitment

**Date:** 2026-06-30
**Decision:** Proceed
**Accepted gaps:** none
**System design constraints carried to planning:**
- Scope = placement/ownership Key Decisions vs File Map paths only (not all decisions).
- Two independent gates: planning lightweight self-check (#1, judgment, hard STOP) + yin `code-reviewer` architectural-placement dimension (#2, the reliable backstop) + anti-bias prompt in planning (#3).
- Independence of the fresh reviewer is the anti-bias mechanism; NO structured ownership field; `templates/overview.md` unchanged.
- Data flow: Key Decisions reach the reviewer in implement + iteration dispatch; fast-track excluded.
- `code-quality-reviewer` is NOT changed.
- Every landed rule guarded by a doc-contract test; the data-flow test (3) is the corruption-signature guard and is the floor.
- Acceptance bar = defense-in-depth: a contradicting plan is stopped by at least one of the two gates.
