# Pre-thinking: enhance-pre-thinking

## Session: 2026-05-26T00:00:00+08:00

## Step A — Design and Gap Map

### Information Gaps

gaps: none identified — the user clarified the evaluation requirement in-session.

### Design Decision Gaps

#### Gap D1: completion-contract
**Question:** Should pre-thinking completion be represented by a section heading or by a validated decision value?
**Hypothesis:** Use decision value. A heading can exist in templates or partial files and is not a safe completion signal.
**Planning impact:** Planning guard must require `Decision: Proceed` or `Decision: Accept gap`; `Decision: Return to Research` blocks planning.

#### Gap D2: design-alignment-scope
**Question:** Should pre-thinking cover system design choices that shape task decomposition, or only information gaps?
**Hypothesis:** Include design choices only when they affect task boundaries, artifact contracts, ownership, or failure modes.
**Planning impact:** Planning must consume design constraints before writing tasks.

#### Gap D3: evaluation-contract-owner
**Question:** Is evaluation a user acceptance note or an agent-evaluable contract?
**Hypothesis:** It must be an agent-evaluable contract with one Primary evaluator, so iteration/debugging use a stable feedback source.
**Planning impact:** Planning, validation, iteration, and debugging must all preserve the same evaluator.

---

## Step B — Answers

### Group 1: pre-thinking semantics
**Q:** Should proposals 1, 2, 4, and 5 be implemented as described?
**A:** Yes. Completion guard, design alignment, planning consumption, and fixture/test coverage should be implemented.

**Q:** How should evaluation be framed?
**A:** Evaluation must force the user to think from the agent's perspective: how the agent can evaluate completion. There should be one canonical evaluation method, and its feedback should guide iteration or bug fixing.

---

## Evaluation Contract

**Primary evaluator:** Targeted pytest suite covering the new pre-thinking contract and conversion chain.
**Agent can perform it by:** Run `source .venv/bin/activate && uv run pytest tests/test_skills/test_pre_thinking_enhancement.py tests/integration/test_snapshot.py tests/integration/test_pipeline.py tests/test_converter/test_skill.py -q`.
**Pass signal:** All tests pass; no snapshot diff; fixture conversion includes `samsara-pre-thinking`.
**Fail signal:** Any assertion failure, missing snapshot file, stale `research -> planning` route, or pre-thinking template containing predeclared completion sections.
**Feedback loop:** Inspect the failing assertion first, patch the corresponding skill/fixture/snapshot, rerun the same Primary evaluator.
**Out of scope validation:** Full interactive agent behavior across live Codex/Gemini sessions.

---

## Step C — Commitment

**Date:** 2026-05-26T00:00:00+08:00
**Decision:** Proceed
**Accepted gaps:** none
**Unresolved gaps:** none
