# Task 3: Pre-thinking auto-regen + codebase-map fail-honest contract

## Context
Read: overview.md

This task makes regeneration self-maintaining and honest. It changes **agent-behavior skill docs**, not unit-testable code, so per the Evaluation Contract it is validated by artifact inspection + the DC-4 fail-honest guard, not by the pytest Primary evaluator. The churn definition and threshold are the same as Task 2 (changed source files since `last_updated`, `staleness_churn_threshold` default 30).

Two behavior changes:
1. **Pre-thinking auto-initiates regen.** In the Atomic Context Boundary, when the map is present but churn is over threshold, the agent auto-initiates `samsara:codebase-map` regeneration instead of merely recording an information gap. Phase 4 human review is **retained** in human-in-the-loop mode.
2. **codebase-map fails honestly.** Regeneration must not advance `last_updated` unless new content was actually written and (in HITL) reviewed. A failed/aborted regen marks the map stale with a reason and leaves `last_updated` untouched.

## Files
- Modify: `skills/pre-thinking/SKILL.md` (Atomic Context Boundary section) — add the auto-initiate-on-over-threshold instruction
- Modify: `skills/pre-thinking/flow.md` (section 1, atomic context procedure step for "present but stale") — replace "use only as starting hypothesis / record info gap" with "if churn over threshold, auto-initiate samsara:codebase-map regeneration (retain Phase 4 review in HITL)"
- Modify: `skills/codebase-map/SKILL.md` — document the auto-initiated trigger, the `staleness_churn_threshold` field, and the fail-honest contract (do NOT bump `last_updated` on incomplete regen)

## Death Test Requirements
- Test DC-4 (regen failure silent reuse): this is a doc-contract guard. Provide a deterministic check that the codebase-map SKILL's write step is gated on "regen completed AND (auto ⇒ review passed)". Implement as an inspection test asserting the SKILL.md regeneration/write section contains an explicit "do not advance last_updated on failure/abort" clause AND a reviewable "mark stale + reason" instruction. (This is the strongest agent-behavior guard available without a live multi-agent run; record the residual gap in the scar report.)

## Unit Test Contract
- Contract source: the SKILL/flow **documented-artifact contract** — the presence and content of the prescribed instructions in `skills/pre-thinking/SKILL.md`, `skills/pre-thinking/flow.md`, and `skills/codebase-map/SKILL.md`. A test asserts each file contains the named behavioral clause (auto-initiate over threshold; retain Phase 4 review; no `last_updated` bump on failed regen).
- The test asserts the contractual clause is present and unambiguous, NOT exact prose wording — match on the behavioral tokens (e.g., "auto-initiate", "last_updated" + "not advanced"/"not bumped"), not full sentences.

## Implementation Steps
- [ ] Step 1: Write death test (DC-4 doc-contract guard) + the artifact-contract unit test
- [ ] Step 2: Run — verify they fail (clauses absent today)
- [ ] Step 3: Edit pre-thinking SKILL.md + flow.md to add auto-initiate-on-over-threshold (retain Phase 4 review)
- [ ] Step 4: Edit codebase-map SKILL.md to add the fail-honest contract + threshold field doc
- [ ] Step 5: Run all tests — verify they pass
- [ ] Step 6: Write scar report (MUST record: this guards the documented contract, not a live regen run — the true behavioral verification is deferred to validate-and-ship dogfood)
- [ ] Step 7: Report back (do not commit)

## Expected Scar Report Items
- Known shortcut: a doc-presence test cannot prove the agent actually obeys the instruction at runtime — the real proof is a live pre-thinking session triggering regen. Record as `deferred_to_feature_iteration` / validate-and-ship dogfood.
- Assumption to verify: that auto-initiating regen inside pre-thinking does not create a loop (pre-thinking → regen → which itself may read the map). Verify the regen path does not re-enter pre-thinking.
- Silent failure to watch: "auto-initiate" silently degrading to "warn only" if the agent treats it as optional — the wording must be imperative, not advisory.

## Acceptance Criteria
- Covers: "Silent failure - regen failure reuses old map (DC-4)", "Degradation - converted codex/gemini hook stays an honest no-op (DC-6)" (verification note: confirm tests/test_converter/ stays green — no converter code change)
