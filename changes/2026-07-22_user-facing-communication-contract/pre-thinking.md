# Pre-thinking: user-facing-communication-contract

## Session: 2026-07-22T00:00:00+08:00

## Step 1 — Locate the work

**Type(s):** workflow-contract / communication / test
**Depth:** focused thinking
- Uncertainty: A shorter response can improve scan speed while degrading evidence visibility.
- Blast radius: Bootstrap instructions affect every user-facing workflow response and every converted Codex installation.

## Step 2 — Assumptions, scope frame, and core identity

### Assumptions

#### A1: ordering-before-deletion
**Assumption:** Most response overload comes from poor ordering and repeated facts, not from the presence of changed-file and validation evidence.
**Boundary:** Applies to user-facing summaries; owning artifacts retain their full contract.
**If it breaks:** Progressive disclosure remains too long and a future evidence-backed refinement is needed.
**Basis:** User preferred the detailed response's evidence but rejected its weak organization.
**Confidence:** confident

#### A2: request-shape-matters
**Assumption:** Command, explanation, completion, and blocked requests require different opening information.
**Boundary:** The later evidence rules remain shared across shapes.
**If it breaks:** A single opening template will add filler or hide the requested answer.
**Basis:** The reviewed communication reference and the user's comparison of result-only and detail-oriented readers.
**Confidence:** confident

### Domain core identity (communication)
**Decision ID:** PT-CI
**Canonical label:** decision-ready-communication
**Core identity:** A Samsara response makes the user's decision easy without making the evidence disappear.
**Operability check:** The first paragraph answers the request; a careful reader can still locate changed files, verification, blockers, and unresolved risk.

## Step 3 — Multi-lens evidence

### Lens: human-attention
**Assumptions covered:** A1, A2
**Evidence surface:** Opening order, headings, repeated facts, and detail discoverability.
**Why this lens:** Both too much process history and unexplained terse codes increase the effort required to decide.
**Facts found:** The user wants the result earlier but still prefers concrete changed-file and validation details.
**Side-path discoveries:** Bare IDs shorten text while increasing lookup cost.
**Not found / gaps:** Cross-model response measurements are not yet available.

### Lens: authority
**Assumptions covered:** A1
**Evidence surface:** Bootstrap, stage artifacts, reviewer output, and converted skill instructions.
**Why this lens:** Repeating the presentation rule across stages would create drift rather than clarity.
**Facts found:** Bootstrap is the session-wide instruction owner; stage artifacts already own their domain payloads.
**Side-path discoveries:** A semantic guard can assert the owner and preserve the contract in Codex conversion.
**Not found / gaps:** none

## Step 4 — Design decisions

### Decision: progressive disclosure
**Decision ID:** PT-D1
**Box:** user-decided
**Decision:** Use a standalone result-first opening followed by applicable evidence sections; remove repetition, not decision-changing detail.
**Basis / derivation chain:** User comparison of terse and detailed responses → both have useful properties → combine them through ordering.
**Reversal cost:** Low; section order can evolve without changing artifact authority.

### Decision: request-shaped opening
**Decision ID:** PT-D2
**Box:** self-derived
**Decision:** Command/status, explanation/review, completed change, and blocked/unknown requests each name their required opening payload.
**Basis / derivation chain:** A fixed completion template cannot answer all request types directly.
**Reversal cost:** Low; new request shapes can be added to the canonical list.

### Decision: evidence-conditioned detail
**Decision ID:** PT-D3
**Box:** user-decided
**Decision:** Preserve applicable changed files, verification, blockers, uncertainty, and unresolved risks; impose no fixed word or list cap.
**Basis / derivation chain:** Detail-oriented users need verification evidence, while filler and duplicated history cause the attention loss.
**Reversal cost:** Low, but weakening this rule can recreate optimistic completion.

### Decision: dual-reader identifiers
**Decision ID:** PT-D4
**Box:** evidence-decided
**Decision:** Put a human-facing semantic label before every user-visible machine ID; a bare ID is never the explanation.
**Basis / derivation chain:** Stable IDs carry the authority graph, but the user should not need to open an artifact to learn what an ID means.
**Reversal cost:** Low; machine artifacts keep bare canonical IDs.

### Real seams (communication)

#### Seam: artifact-to-response
**Decision ID:** PT-S1
**Box:** evidence-decided
**What it is:** Boundary between the complete owning artifact and its user-facing semantic projection.
**Evidence tier:** domain-essential
**Basis:** The response must summarize an authority without becoming another authority.

#### Seam: result-to-detail
**Decision ID:** PT-S2
**Box:** user-decided
**What it is:** Boundary where a standalone opening hands off to evidence retained for continued reading.
**Evidence tier:** already-happened (user feedback)
**Basis:** Terse and detailed readers need different stopping points in the same response.

## Step 5 — External-call answers

The external communication repository is a design reference only. Samsara keeps
its evidence, uncertainty, and destructive-action safeguards instead of copying
hard brevity limits or mandatory time estimates.

## Step 6 — Honest handoff

### L1 (handoff to planning — Key Decisions single source)
**Decision refs:**
- PT-CI (decision-ready-communication)
- PT-S1 (artifact-to-response)
- PT-S2 (result-to-detail)

### Evaluation Contract

**Contract ID:** PT-EVAL
**Canonical label:** evaluation-contract
**Primary evaluator:** Semantic response-shape tests plus before/after scenario review
**Agent can perform it by:** Run the Bootstrap communication guards and compare representative command, review, completion, blocked, and destructive-action responses.
**Pass signal:** Every opening stands alone; applicable evidence remains; no bare ID, repeated history, arbitrary cap, or unsupported estimate appears.
**Fail signal:** A result is buried, a careful reader loses decision-changing evidence, or another file creates a competing presentation authority.
**Feedback loop:** Fix the Bootstrap contract or its semantic guard rather than copying rules into stage skills.
**Out of scope validation:** Subjective preference across every model and reasoning setting.

### Commitment

**Date:** 2026-07-22T00:00:00+08:00
**Decision:** Proceed
**Accepted gaps:** Cross-model scoring remains future evidence.
**Residual list:** none
