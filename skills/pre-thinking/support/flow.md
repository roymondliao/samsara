# Pre-thinking Flow — Detailed Procedures

This file expands the SKILL.md step descriptions into agent-executable instructions. Read this alongside SKILL.md; do not treat it as a standalone script.

---

## 1. Gap Identification

A **gap** is a decision the LLM would need to make during planning that research has not constrained.

Gap examples:
- Interface ownership is unclear ("Should this live in module A or B?")
- Success definition is undefined ("How many is 'enough' for the north star metric?")
- Location is ambiguous ("Does this new file go in `lib/` or `core/`?")

**Not a gap:**
- Implementation detail choices that don't change observable behavior (e.g., which loop style to use)
- Decisions that research explicitly delegated to the implementer
- Choices where any option is valid without user input (the LLM can proceed without bias)

A gap test: "If I make this decision without asking, am I smuggling an assumption into planning that the user didn't approve?" If yes — it is a gap.

Write each gap as a specific, non-leading question. Non-leading means: the question does not embed a recommended answer. Bad: "Should we use PostgreSQL (recommended for reliability)?" Good: "Which database engine should this feature use, and why?"

Include a hypothesis for each gap: the LLM's current best assumption. The hypothesis is shown to the user for challenge, not framed as the answer.

---

## 2. Group Formation

Group questions by:
- **Topic domain** — questions about the same subsystem or concern belong together
- **Answer-interdependency** — questions whose answers depend on each other belong in the same group (answering Q1 may change the right answer to Q2)

Order groups by **resolution dependency**: groups whose answers unblock other groups come first.

Within a group, order questions so earlier questions narrow the context for later ones.

---

## 3. Group Overflow Procedure

**When a group has N > 3 questions:**

1. Split into rounds: Round 1 takes the first 3 questions; Round 2 takes the next 3 (or fewer if N ≤ 6); add Round 3 if N > 6.
2. Issue Round 1 via AskUserQuestion (exactly 3 questions, no more).
3. Append Round 1 answers to `pre-thinking.md` under heading `### Group X: <theme> (round 1)`.
4. Issue Round 2 via AskUserQuestion (remaining questions, ≤ 3).
5. Append Round 2 answers under `### Group X: <theme> (round 2)`.
6. Continue until all questions in the group are answered.

**Label invariant:** All rounds share the same group number and theme. `Group X (round 1)` and `Group X (round 2)` are sub-rounds of the same group — do NOT label them as separate groups (Group X and Group X+1). Group identity must be preserved across rounds.

**Hard limit:** NEVER put more than 3 questions in a single AskUserQuestion call. (This round-splitting arithmetic depends on the limit defined in §7. If §7's limit changes, the round-split sizes above must change in lockstep.)

**Example (5-question cluster on database schema):**
- Round 1: Questions 1, 2, 3 → AskUserQuestion → append under `### Group 2: database-schema (round 1)`
- Round 2: Questions 4, 5 → AskUserQuestion → append under `### Group 2: database-schema (round 2)`

---

## 4. File-Edit Detection Procedure

Before EACH Step B append (every group, every round):

1. **Read** the current `pre-thinking.md` from disk.
2. **Compare** to the content the LLM last wrote (the expected state tracked internally).
3. **If the file differs from expected:**
   - Print exactly: `I see you've edited pre-thinking.md. Incorporating your changes.`
   - Treat the user-edited version as authoritative for all differing sections.
   - Use the user-edited content as the base for the upcoming append.
4. **Append** the new group's answers below the (possibly user-edited) content.

**This procedure runs before every append — not only the first one.** Users may edit between any two Step B groups.

**If the expected state is unavailable** (e.g., K3b Resume from a prior session, or context compression): reconstruct the baseline by reading the current file's Step A section and all visible Step B groups. Treat that reconstructed content as the expected state and compare the full current file against it. Proceed with the comparison normally.

**Do NOT:**
- Overwrite the user's edits with the original LLM-written Step A content.
- Halt with an error when user edits are detected — detect, acknowledge, incorporate, continue.
- Skip the read-before-append step even if you are confident nothing changed.

---

## 5. K3b Recovery Procedure

**On session start, before Step A:**

1. Check if `pre-thinking.md` exists in `changes/<feature>/`.
2. **If absent:** proceed normally to Step A.
3. **If present AND `## Step C — Commitment` section exists:** session is already complete — proceed to planning. Do not re-run Step A or Step B. (The presence check is reliable only because `## Step C — Commitment` is never written before the AskUserQuestion commitment response is received — see §8 Quick-Pass and Step C in `templates/pre-thinking.md`.)
4. **If present AND `## Step C — Commitment` section is ABSENT:** session was interrupted (K3b state).
   - Identify the last completed section (Step A written? Which Step B groups are present?).
     - A group is **complete** if its `### Group N:` header is followed by at least one `**A:**` answer line (anywhere before the next `### Group` header or end of file).
     - A group is **partial** (header present, no `**A:**` lines) — treat it as the NEXT INCOMPLETE group and resume from it.
   - Inform the user: `"Pre-thinking was interrupted before commitment was reached. [Last completed section: Step A / Step B Group N]"`
   - Offer via AskUserQuestion (header ≤ 12 chars):
     - **Resume** — continue from the next incomplete group in Step B; do NOT re-run Step A
     - **Restart** — overwrite the file, run Step A fresh
   - Wait for user selection. Do NOT proceed past this point without it.
   - For Resume: before proceeding, reconstruct the expected-state baseline using the §4 file-edit detection fallback procedure (read current file's Step A and all visible Step B groups as the baseline). Then proceed to the next incomplete Step B group (or Step C if all groups done).
   - For Restart: overwrite `pre-thinking.md`, run Step A fresh.

**Failure to detect K3b = planning may be invoked with zero commitment.** This check is mandatory at session start, not optional.

---

## 6. Return to Research Write Format

**When commitment = Return to Research (from mid-Step-B OR Step C):**

1. Write `## Step C — Commitment` section immediately.
2. Use this exact format:

```
## Step C — Commitment

**Date:** <ISO timestamp>
**Decision:** Return to Research
**Accepted gaps:** none
**Unresolved gaps:**
- Gap <n> (<label>): <specific question that needs research to answer>
[list ALL unresolved gaps from Step A by their exact gap labels]
```

3. `unresolved_gaps` must be non-empty. Each entry must reference a specific Step A gap label (e.g., `Gap 1 (interface-ownership)`) — do NOT write generic labels like "unclear requirements."
4. After writing, output: `"Pre-thinking suspended. The following gaps require clarification before planning: [gap list]. Please re-invoke samsara:research."`
5. **Do NOT invoke `samsara:planning`.** Stop.

**If Return to Research is triggered mid-Step-B** (user signals uncertainty during a Step B group): write Step C immediately with all gaps from Step A that have not been resolved by Step B answers so far. Mark any partially-answered groups as unresolved if the answers were insufficient.

---

## 7. AskUserQuestion Header Constraint

All `AskUserQuestion` calls in this skill must use a `header` field of **≤ 12 characters** for broadest client compatibility (Codex CLI, Gemini CLI v0.29.0+).

Examples of compliant headers: `"Pre-thinking"` (12 chars), `"Gap review"` (10 chars), `"Commitment"` (10 chars), `"Resume?"` (7 chars).

---

## 8. Quick-Pass Path

When Step A produces `gaps: none identified`:

1. Write Step A section with content: `gaps: none identified — proceeding directly to commitment.`
2. **Skip Step B entirely.** Do NOT write a Step B section. Do NOT issue any Step B AskUserQuestion calls.
3. Proceed directly to Step C.
4. Issue exactly one AskUserQuestion call for the Step C commitment.
5. Write Step C after receiving the commitment response.
6. Total AskUserQuestion calls for a quick-pass session: exactly 1 (the Step C commitment gate).
