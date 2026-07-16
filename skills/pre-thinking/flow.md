# Pre-thinking Flow — Detailed Procedures

**Sole owner: executable procedure.** `SKILL.md` owns entry, routing overview,
output, and transition; templates own shapes. If another source conflicts with
this file's procedure, this file wins.

**Cross-cutting principles (the design's load-bearing spine):**

1. **Anything a "feeling" could fake, replace with "point to checkable evidence."** Confidence, done-ness, derivation, pattern choice, seam reality — all use this move. An LLM can fake confidence; it cannot fake a pointable file:line.
2. **Asymmetric friction.** Thinking less has friction everywhere; thinking more is free. Deep needs no reason, shallow needs a written reason; adding a lens is free, dropping a known lens needs a reason; challenging an assumption is free, self-accepting is banned; recording reversal cost is cheap, building a speculative extension point is expensive.
3. **Facts parallel, judgment sequential.** Gathering facts can fan out (facts don't fight); making decisions must be single-file (decisions are interdependent; parallel forks into contradictions).
4. **Leave convergence traces.** Every decision carries "why not the others" and "what rots first" as signposts for the next person who iterates.
5. **Prefer failures that alarm.** Choose the option that fails loudly over the one that fails silently. A guess isn't dangerous; a silent guess is.

### Stable ID contract

These prefixes have one fixed meaning:

- `PT-CI` (Pre-thinking Core Identity)
- `PT-D*` (Pre-thinking Design Decision)
- `PT-S*` (Pre-thinking Real Seam)
- `PT-EVAL` (Pre-thinking Evaluation Contract)

An ID is an immutable authority key, not a label to rewrite. Once downstream
artifacts cite an ID, never renumber it, never reuse it for another meaning, and
never change its canonical label. A correction that preserves the same decision
identity keeps both. A repurpose, split, merge, or semantic replacement gets a
new ID and all consumers update their refs; retired IDs are not recycled.

The canonical human resolver is the Step 2 `Canonical label` for `PT-CI`, the
Step 4 decision label for `PT-D*`, the Step 4 seam name for `PT-S*`, and the fixed
label `evaluation-contract` for `PT-EVAL`. Human-facing Markdown cites
`ID (canonical label)`. Machine-facing YAML reference fields store the bare ID.
Canonical labels are short semantic phrases without parentheses.
The label beside a reference is a checked projection of its declaration, never a
second place to redefine it.

---

## 1. Step 1 — Locate the work

The agent judges two things from the research conclusions + one look at the codebase, writes them down; both are revisable later.

### (1) Type (may be several at once)

feature / perf optimization / infra / refactor / external-service integration / data-structure change. Can't tell → count them all.
→ Why: different types need different things thought about (Step 4 uses this to pick which dimensions to reason over).

### (2) Depth — one ruler: uncertainty × blast radius

- **uncertainty** = are there design questions still "not thought through, must guess"?
- **blast radius** = if this is built wrong, how far does damage spread? Do you know how far?
  - **Codebase/structural dimension (codebase-craft):** beyond system/data/permission spread, ask *which seam does this change land on? Does it touch a load-bearing boundary?* Landing on a core seam (much existing or planned code sits on it) = large radius → think deep; only adding a leaf node = small. This makes "think deep?" sensitive to codebase structure, not just system consequences (design note 2 §5).

The ruler has exactly one real gate: **deep thinking is the default; fast-track is a narrow path you must *prove* into.**

- **fast-track**: prove *both axes approach zero* (no unresolved design question; wrong = bounded, known damage) → no thinking needed. What lets you skip is not "small change" — "small" is only the surface.
- **deep thinking**: everything else, all through the same flow (Step 2 assume → Step 3 gather → Step 4 converge).
- The rule is one-directional: fast-track needs proof; unsure = deep. Do not assume you can judge "this one needs no depth." Misjudging into deep only costs tokens; misjudging into fast-track drops blind spots — asymmetric cost.
- **No "light thinking" middle tier.** Whether to dispatch searchers, and how
  many, emerges from Step 2's not-confident assumptions and the distinct evidence
  surfaces they require. Zero not-confident assumptions means zero searchers
  (equivalent to the old "light" case), with no separate first-step judgment call.

**Revisable (depth one-way valve + mid-flight upgrade):** if later steps surface new evidence, the main agent upgrades depth on its own (never downgrades). Not a new mechanism — the existing single-directional valve.

---

## 2. Step 2 — Assume, frame, and distil core identity

Collect the research conclusions into a set of **explicitly written assumptions**. This step **converges** (draws a box the later thinking runs inside; stops it sprawling), it does not brainstorm.

An assumption earns writing if the blast-radius axis says so: **"if this is wrong, does the design change?" Yes → write it; no → noise (leave it to implementation).** How many is decided by that filter, no fixed count; when unsure whether to write one, write it (a line is cheap, a missed wrong premise is expensive).

Each assumption, four fields:
```
Assumption: what this run takes to be true
Boundary: when it holds; when it does not
If it breaks: what rots, who notices first
Basis: a checkable piece of evidence to point at (or none)
```

**"Confident / not confident" is judged objectively, not by feeling:**
- **Confident = can point, right now, to a concrete checkable basis** (file:line / an existing test / a research finding / an existing contract). Claim confidence → you must write the basis; none written = not confident automatically.
- Not a basis: "usually it's like this" / "the framework should handle it" / "industry convention." That's feeling, not this case's evidence.
- This matches the axiom: existence is responsibility; what exists leaves evidence; producing evidence is how you carry the responsibility.

Assumptions then split naturally: **confident** → used to frame scope; **not confident** → go to Step 3 for evidence (those that can't be gathered, only the human knows → become Step 5 questions). If assumptions contradict each other and won't reconcile → research framed it wrong, **return to research**.

### Atomic context procedure (before framing is complete)

Framing needs live system facts (module boundaries, entrypoints, config/env sources, external services, data flow, existing tests). Derive them from live codebase artifacts:

1. Check `.samsara/codebase-map.yaml`.
2. If present and fresh, read it as derived context for module boundaries, entrypoints, config sources, external services, data flow, hidden coupling, and assumptions.
3. If present but stale and churn (changed source files since `last_updated`, excluding paths under `changes/`, `docs/`, `bugfix/`) exceeds `staleness_churn_threshold` (canonical definition: codebase-map SKILL.md Triggers): **auto-initiate** `samsara:codebase-map` regeneration before continuing. Codebase Map's project-scoped evidence review owns map verification; do not add a feature execution-mode gate. Do not proceed past this step until regeneration completes. **If auto-initiated regeneration fails or aborts, do NOT treat it as completed and do NOT block indefinitely: proceed with the map explicitly marked stale, record an information gap noting the failed regeneration, and continue planning on that basis.** If present but stale and churn is at or below `staleness_churn_threshold`: use it only as a starting hypothesis. Verify any fact needed for planning against live codebase artifacts; record stale or unverifiable facts as information gaps.
4. If missing, do not invent a map from memory. For a small, localized task, run targeted local inspection of the affected files and their immediate entrypoints/config/external interactions. For broad or unclear scope, record an information gap recommending `samsara:codebase-map`.
5. If the map and live codebase disagree, live codebase artifacts win. Surface the drift as an information gap or update requirement; do not silently trust the map.

### Codebase-craft — distil the domain core identity

While framing, produce one more named output: the **domain core identity**.

- **What it is:** what this system (within feature scope) essentially *is*, one or two lines — the thing structural decisions must serve.
- **Where it comes from:** the research problem-essence + this step's hypothesis-framing. As you condense research into an explicit hypothesis, force out the "this thing's core identity is X" judgment that frames scope.
- **Operability test (guards against empty slogans):** the identity must be able to **adjudicate a concrete structural decision**. Test: if two opposite structural choices both "serve" your written identity, it is too vague — rewrite it. (Same "replace anything foolable with checkable" principle.)

Core identity is a **design decision** and rides the Step 6 handoff channel (planning Key Decisions single source). It is feature-level, produced once here (design note 2 §4.1).
Assign it the stable ID `PT-CI` so downstream artifacts cite it instead of
copying it as a new decision.

---

## 3. Step 3 — Multi-lens evidence

Go find evidence for the not-confident assumptions. **Why multi-lens and not the main agent alone:** the main agent only searches where it already thought to look — its blind spots decide what it can find. Independent searchers at **different lenses** hit what it didn't think to look for. This is the only reason multi-lens exists: cover blind spots.

Derive the dynamic evidence strategy from decision-relevant, not-confident
assumptions and the distinct evidence surfaces they require. This is not a
one-to-one mapping. One lens may cover multiple assumptions when they depend on
the same evidence surface; one assumption may require multiple lenses when its
evidence or blind spots span different surfaces. Before dispatch, record each
lens's assumptions, evidence surface, and independent blind-spot rationale in
`pre-thinking.md`.

- **No cap on lens count** — dispatch as many as this run needs, decided by "which kinds of places the evidence is scattered across." No cap is possible because **searchers bring back only facts, and facts don't fight — they only complement** (let them judge, and many of them return contradictory advice built on different premises — so they don't judge).
- **Each searcher returns:** facts found (with sources), things found along the way that weren't on the list (this is the real blind-spot value), things not found. **No "recommendation" field.** (Return shape: `templates/lens-report.md`.)
- **How to dispatch:** the lens (question to answer) + thinking scope (Step 2's box) + starting points (a few entry files, but a *start* not "only search these," else you smuggle the main agent's blind spot into the searcher) + return format.
- A lens that fails or comes back blank → record it as an "unverified gap," do not carry on as if nothing happened.
- **Searcher count comes from Step 2, not Step 1:** derive the uncapped lens set
  from the many-to-many mapping above. Zero not-confident assumptions means zero
  searchers and the main agent looks itself. This follows from deleting the
  "light thinking" tier; it is not a separate depth rule.
- A **default lens list** (skill-local `references/lenses.md`) serves as a reminder (not a cap): after deriving lenses, check it for known-important ones you missed; deliberately skipping one needs a written reason.
- **codebase-map as a start, not truth:** when `.samsara/codebase-map.yaml` exists and is fresh enough, searchers take it as a starting hypothesis (saves re-digging), but **live codebase wins** — where map and reality disagree, trust reality and surface the drift. Map missing or stale → don't invent from memory; search.
- **Sole writer:** searchers only *return results* to the main agent; they write no file. `pre-thinking.md` is written by the main agent alone (avoids many searchers writing one file at once).

### Codebase-craft — which lenses gather seam facts

Among the default lenses, **structure / evolution / boundary** are the ones that feed the real-seam decision in Step 4:
- **structure / boundary** gather *facts*: existing module/abstraction boundaries, coupling, existing patterns in the area.
- **evolution** gathers the **already-happened** evidence tier: how this area has historically changed (git history) — used to judge whether a seam is stable/real.

These are still facts, not judgment. The judgment (is this a real seam? what tier?) happens in Step 4. Keep the separation (design note 2 §4.2).

---

## 4. Step 4 — Converge to design decisions

The main agent, **alone and in order** (can't parallelize — decisions depend on each other: "where to put it" needs "what's the core" first). This is the most dangerous step — passing judgment is exactly where an LLM snaps back to "looks fine, ship it."

### First decide which decisions to make (where dimensions come from)

Not a fixed list — dimensions **grow naturally + a type checklist as safety net** (same management as Step 3 lenses):
1. From Step 2's **not-confident assumptions** — each "wrong → design changes" assumption is a decision to make.
2. From Step 3's **evidence and candidate gaps** — what searchers hit becomes a dimension to decide.
3. Against the **type checklist** below — fill a missed known-important one; to truly skip, write one line of reason (adding a dimension is free, dropping a known one needs a reason).

Type checklist (reminder, not a cap; Step 1's type decides which rows to read):

| Type | Common decision dimensions |
|---|---|
| feature | where + why / reuse existing or build new / consistent with existing style or deviate (write the cost of deviating) / which upstream contracts to inherit |
| perf | current baseline + target / how to measure (→ becomes Step 6 evaluator) / how to prevent regression |
| infra | format contracts (data/secret/config) / blast radius (incl. permissions) / placeholder-value lifecycle (who fills, when swapped, warning if wrong) / rollback / which validations the agent does vs the operator |
| refactor | how to prove behavior wasn't broken / safe cut order (stepwise, stoppable anytime) |
| external integration | build or use existing / exit cost / their interface contract |
| data-structure change | compatibility / old-new coexistence window / rollback point |

(This dimension table and Step 3's lens table are **different layers but corresponding**: lenses gather facts, dimensions consume those facts to decide. E.g. structure-lens facts → feed the "where / reuse / pattern" dimension.)

### Each dimension lands in one of three boxes

Core mechanism, one sentence: **every decision must land in one of three boxes — there is no fourth box called "I feel."**
Assign each decision a unique stable ID (`PT-D1`, `PT-D2`, ...). Preserve the ID
when revising the decision; Planning cites the ID and never allocates a `PT-*` ID.

1. **Evidence-decided** — Step 3's facts forced a single answer; cite the source.
2. **Self-derived** — evidence didn't force it, but you derive it from a **nameable root** and **write the chain out**. Root = **Samsara axiom + the problem's hard requirements + existing convention/contract (if found and confirmed not rotten)**. You don't need to first classify this change's "novelty/maturity" to decide what to check: go look for a convention/contract; not found → fall back to axiom + hard requirements. The act of looking gives the situated answer; classify-then-check and check-directly are equivalent.
   - Why write the chain, not just "I used first principles": the latter can label any conclusion, trivially faked; a written chain exposes fakes (they don't reconnect to the root).
   - **Mature-repo trap:** some existing code is rotten. "Consistent with existing" may perpetuate rot — before citing an existing convention, confirm it isn't rotten; if it is, deviate and record the deviation as a decision.
3. **Needs an external call** — can't derive it, several answers stand, the choice needs a preference/priority the agent has no authority to invent. Answerer: **human, or the gatekeeper in auto mode.**
   - Sub-split: (a) derivable from project principle/convention → gatekeeper judges legitimately; (b) only human/org knows (naming convention, business priority) → gatekeeper can only guess, and **must mark "unconfirmed guess" and record it**, making it a visible risk rather than a silent wrong assumption.

**Reversibility folds into the three boxes:** on each decision, ask "how painful to change later" —
- easy to change, or both options equally easy → pick the flexible one yourself ("self-derived"), record reversal cost in passing.
- keeping flexibility costs extra now → a trade-off with no standard answer, "needs external call."
- actually building the extension point → only when a present-day, real force exists; otherwise record reversal cost, don't build.
- specially flag the pseudo-reversible ("looks easy to change, but semantics are locked") — it gives false safety and rots first.

### Codebase-craft — real seams as a named decision category

The domain's essential boundaries the feature **sits on or creates** (module/abstraction boundaries) are a **named decision category** in Step 4 — run through the same three boxes, **not a separate structural pass**.
Assign each seam decision a unique stable ID (`PT-S1`, `PT-S2`, ...); the
semantic seam name remains the human-facing resolver key.

- **Where produced:** Step 3's structure/boundary/evolution lenses gathered the facts → converge here into named seam decisions.
- **Evidence-tier marker (key) + accrues along the pipeline:** the full tier order is
  **already-happened (git history) > planned change (plan's future tasks) > domain-essential boundary > imagination**.
  But evidence accrues along the *pipeline stage*: pre-thinking can only mark **already-happened / domain-essential** (or "needs external call"); the **planned-change** tier is added later by planning, once it decomposes tasks (see design note 2 §7). So pre-thinking marks each seam already-happened/domain-essential; planning may later *strengthen* the same seam to planned-change. **Imagination is not evidence** — a seam that at pre-thinking time cannot be marked with any checkable tier is not a real seam (death case DC-1 below).
- **Feature-scope limited:** recognize only seams the feature sits on/creates, do **not** redraw the whole project's architecture (guards seam astronomy).
- **Granularity floor:** seams go down to **function / module / abstraction boundary**, no lower (design direction §3.2). Note the floor is about *what yin review can see*; the *threshold for leaving a trace* is narrower — only a structural bet (pattern choice / boundary-seam creation or deviation / explicit refusal) leaves a trace, ordinary function splitting does not (design notes 5 §9, 6 §2.3).

### Death cases (silent failure + detection)

| Death | Silent-failure shape | Detection / defense |
|---|---|---|
| **Seam astronomy** | pre-thinking tries to draw the whole project's architecture; seams explode, most imaginary | feature-scope limit + evidence-tier marker (imagination tier rejected) + downstream consumption discipline (a seam no code sits on = noise, design note 1) |
| **Empty core identity** | identity written as a slogan that adjudicates no decision | operability test: two opposite structural choices both "serve" it → too vague, rewrite |
| **Seam with no evidence tier** | looks like structural thinking, actually drawing lines by feeling (DC-1) | three-box discipline: a seam also lands in one box (evidence-decided / self-derived+chain / needs external call); no markable tier = not a real seam |
| **Mature repo perpetuates a rotten seam** | "consistent with existing" reuses an already-rotten boundary | before citing an existing convention, confirm it isn't rotten; if rotten, deviate and record as a decision |

### Closing check

You may declare "no gaps" only when **every dimension that grew (including checklist ones skipped with a written reason) has landed in one of the three boxes.** Do not wave it off with "nothing to ask."

---

## 5. Step 5 — Ask what must be asked

Step 4 recognized and marked which decisions "need an external call"; this step actually asks and records the answers. The most dangerous thing: **how you ask decides whether you get a real decision or a rubber stamp.** So two rules:

- **Every question is a real multiple-choice:** ≥2 options + each option's trade-off. Never ask "shall we do it the way I recommend?" (that yes/no is exactly the samsara "shall we do all of it?" disease).
- Give every question a stable slug and dispatch it as
  `pre-thinking.step5.<group-slug>.<question-slug>`. A rewrite keeps the same ID;
  a different question gets a new ID.
- **Answers recorded as traces**, not just the conclusion: which was chosen / why not the others / what this decision assumes / what rots first when that assumption breaks. So the next person can pick it up and change it without re-litigating the whole thing.

Ask a small batch at a time, split rounds if many. If an answer overturns a Step
4 derivation, propagate the fix downstream because decisions are interdependent.

### Grouping and overflow

- Group questions by **topic domain** (same subsystem/concern together) and **answer-interdependency** (answering Q1 may change Q2's right answer → same group). Order groups by **resolution dependency** (unblocking groups first).
- **Hard limit: never more than 3 questions in one AskUserQuestion call** (§8 header constraint applies too). When a group has N > 3: split into rounds of ≤3, all rounds sharing the same group number + theme (`### Group X: <theme> (round 1)`, `(round 2)`, …) — sub-rounds of one group, never relabelled as separate groups.

### File-edit detection (before EACH Step 5 append)

1. **Read** the current `pre-thinking.md` from disk.
2. **Compare** to the content the LLM last wrote (the expected state tracked internally).
3. **If it differs:** print exactly `I see you've edited pre-thinking.md. Incorporating your changes.`; treat the user-edited version as authoritative for differing sections; use it as the base for the append.
4. **Append** the new group's answers below the (possibly user-edited) content.

This runs before every append, not only the first. **If expected state is unavailable** (K3b resume or context compression): reconstruct the baseline by reading the current file's earlier sections and all visible Step 5 groups; treat that as expected state and compare. Do NOT overwrite user edits, do NOT halt on detecting edits, do NOT skip the read-before-append.

---

## 6. Step 6 — Honest handoff

Hand three things to planning; be honest about your own state.

### (1) L1 handoff — core identity + real seams (codebase-craft)

The feature-level **core identity** (Step 2) and **real seams** (Step 4) are design decisions. They travel through the **existing "planning Key Decisions single source" channel** (the same channel Step 4's other design decisions use) — planning cites them, does **not** re-derive them and does **not** add new placement decisions. This is the **L1 contract** the implementer's global-thinking channel later consumes (design notes 1 §10, 2 §7). No new file, no new mechanism: L1 = the shared (identity + seams) + planning's per-task (position) added at decomposition.
The L1 handoff lists the corresponding `PT-CI` and `PT-S*` IDs.
Each ref includes its canonical label so a human can resolve its meaning without
copying the decision content.

Do not build the seam's future abstraction now — structural-honesty rules still govern: write the concrete first, abstract when the second real force appears. L1 says *where the joint should be soft*, it does not authorize growing the joint pre-emptively (design note 1 §6).

### (2) Evaluation Contract (single standard, existing format)

Evaluation is never optional, including fast-track.

Define one agent-evaluable Primary evaluator — something that, when it holds,
means done; the agent can actually run or inspect it, not "feels done." This is
the existing Evaluation Contract. Write it in this exact structure:

```
## Evaluation Contract

**Contract ID:** PT-EVAL
**Canonical label:** evaluation-contract
**Primary evaluator:** <one canonical method>
**Agent can perform it by:** <command, browser flow, artifact inspection, snapshot comparison, log check, or stable rubric>
**Pass signal:** <observable condition>
**Fail signal:** <observable condition>
**Feedback loop:** <what the agent should do first if it fails>
**Out of scope validation:** <things the user may care about but the agent cannot reliably evaluate, or "none">
```

Rules:
- `Primary evaluator` must be singular. Supporting evidence is allowed, but there is only one canonical feedback source. Iterating up (10%→90%), swapping the ruler each increment confuses progress with drift.
- TDD and death-path tests remain mandatory engineering gates. They are not the Primary evaluator unless the user (or recorded gatekeeper decision) explicitly chooses "tests only" as the unique standard.
- If multiple evaluators are given, ask one follow-up to pick the canonical one.
- Planning, iteration, debugging, and validate-and-ship must reuse this same Primary evaluator, never invent a new success standard.
- Defined here because this is the last moment design intent is fully in view and no code is written yet — most accurate.

### (3) Commitment (one of three) + residual list

**Proceed / Accept gap / Return to Research** — forces an explicit stance so no one slips into planning while pretending everything's solved. Residual list = things unsolvable here, handed to planning or later (e.g. "this step needs an operator to fill a value manually"). Auto: commitment made by the gatekeeper too; "Return to Research" is allowed (a flow redirect, not a fallback to a human).

Only Proceed or Accept gap may invoke `samsara:planning`.

---

## Execution Mode Routing

Apply this routing to every Step 5 choice, Evaluation Contract selection, and
Step 6 commitment:

- If `Execution mode: human-in-the-loop`, ask the user using the active prompt.
- If `Execution mode: auto`, do not ask the user. Dispatch
  `samsara:auto-gatekeeper` with the active stable gate ID, wait for its validated
  decision, and write the answer to `pre-thinking.md`. The Gatekeeper alone
  appends `auto-decisions.md`.

- Step 5: preserve the choice trace and mark human-only answers as unconfirmed
  guesses.
- Evaluation Contract: record exactly one Primary evaluator.
- Evaluation Contract uses `pre-thinking.evaluator`.
- Commitment uses `pre-thinking.commitment`; invoke planning only for Proceed or
  Accept gap.

---

## 7. Return to Research write format

**When commitment = Return to Research (from mid-Step-5 OR Step 6):**

1. Write `## Step 6 — Commitment` section immediately.
2. Use this exact format:

```
## Step 6 — Commitment

**Date:** <ISO timestamp>
**Decision:** Return to Research
**Accepted gaps:** none
**Unresolved gaps:**
- Gap <n> (<label>): <specific question that needs research to answer>
[list ALL unresolved gaps by their exact labels]
```

3. `unresolved_gaps` must be non-empty. Each entry references a specific gap/assumption label (e.g. `Gap 1 (interface-ownership)`) — never generic labels like "unclear requirements."
4. After writing, output: `"Pre-thinking suspended. The following gaps require clarification before planning: [gap list]. Please re-invoke samsara:research."`
5. **Do NOT invoke `samsara:planning`.** Stop.

**If triggered mid-Step-5** (user signals uncertainty during a group): write Step 6 immediately with all not-confident assumptions/decisions unresolved so far. Mark partially-answered groups unresolved if answers were insufficient.

---

## 8. AskUserQuestion Header Constraint

All `AskUserQuestion` calls in this skill must use a `header` field of **≤ 12 characters** for broadest client compatibility (Codex CLI, Gemini CLI v0.29.0+).

Compliant headers: `"Pre-thinking"` (12), `"Lens review"` (11), `"Commitment"` (10), `"Resume?"` (7).

---

## 9. K3b Recovery and Completion Procedure

**On session start, before Step 1:**

1. Check if `pre-thinking.md` exists in `changes/<feature>/`.
2. **If absent:** proceed normally to Step 1.
3. **If present AND complete:** read the `Decision:` field and Evaluation Contract.
   - `Decision: Proceed` or `Decision: Accept gap` + complete Evaluation Contract
     + L1 refs present = planning-ready only when the refs contain `PT-CI` and
     every cited `PT-S*`, and each ref resolves to exactly one Step 2/4
     declaration. A heading or copied L1 prose is not completion.
   - `Decision: Return to Research` = complete but NOT planning-ready. Stop and ask the user to re-invoke `samsara:research` with the unresolved gaps.
   - A Step 6 heading without one of these decisions is incomplete.
   - Any Step 6 without Evaluation Contract, without L1 refs, or with an
     unresolved/duplicate `PT-CI` or `PT-S*` ref is incomplete.
4. **If present AND incomplete:** session was interrupted (K3b state).
   - Identify the last completed step (which of Steps 1–6 are written? which Step 5 groups are present?).
     - A Step 5 group is **complete** if its `### Group N:` header is followed by at least one `**A:**` answer line before the next `### Group` header or end of file.
     - A group with header but no `**A:**` line is **partial** — treat it as the NEXT INCOMPLETE group and resume from it.
   - Inform the user: `"Pre-thinking was interrupted before commitment was reached. [Last completed step: Step N]"`
   - Offer via AskUserQuestion (header ≤ 12 chars):
     - **Resume** — continue from the next incomplete step; do NOT re-run earlier completed steps.
     - **Restart** — overwrite the file, run from Step 1 fresh.
   - Wait for user selection. Do NOT proceed without it.
   - For Resume: reconstruct the expected-state baseline via the §5 file-edit fallback (read all written steps + visible Step 5 groups as baseline), then continue.
   - For Restart: overwrite `pre-thinking.md`, run Step 1 fresh.

**Failure to detect K3b = planning may be invoked with zero commitment.** This check is mandatory at session start, not optional. Never use heading presence alone as a completion signal.
