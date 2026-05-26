# Task 2: Create samsara:pre-thinking skill

## Context

Read: `overview.md`

Create a new samsara chain skill at `skills/pre-thinking/`. This skill runs unconditionally between research and planning. It produces a single append-only artifact (`pre-thinking.md`) with LLM as sole writer.

The skill has 3 steps:
- **Step A**: Write ALL gaps to `pre-thinking.md` in one shot (or quick-pass if no gaps)
- **Step B**: Ask questions in groups of ≤3 via AskUserQuestion; append answers; detect user file edits
- **Step C**: Collect commitment via AskUserQuestion (Proceed / Accept gap / Return to Research)

## Files

- Create: `skills/pre-thinking/SKILL.md`
- Create: `skills/pre-thinking/support/flow.md`
- Create: `skills/pre-thinking/templates/pre-thinking.md`

## Death Test Requirements

Before writing SKILL.md, verify the following death scenarios against `death-tests.md` (Task 1 output):

- Test: K3b interrupted session — SKILL.md must instruct agent to check for `## Step C — Commitment` on session start
- Test: quick-pass — SKILL.md must describe the no-gap path explicitly (write minimal file, skip Step B, go to Step C)
- Test: group overflow — `flow.md` must contain explicit group-overflow procedure (N > 3 → split into 3 + remainder)
- Test: append-only — `templates/pre-thinking.md` comments must make clear each section is append-only
- Test: file-edit detection — `flow.md` must describe read-before-write procedure
- Test: commitment via AskUserQuestion — SKILL.md Step C must say "via AskUserQuestion" explicitly
- Test: Return to Research path — SKILL.md must describe what to write when commitment = Return to Research

## Implementation Steps

- [ ] Step 1: Write death tests (verify `death-tests.md` exists from Task 1; confirm 7 scenarios present)
- [ ] Step 2: Write `skills/pre-thinking/SKILL.md` per spec below
- [ ] Step 3: Write `skills/pre-thinking/support/flow.md` per spec below
- [ ] Step 4: Write `skills/pre-thinking/templates/pre-thinking.md` per spec below
- [ ] Step 5: Verify SKILL.md body word count ≤ 500 words (not counting frontmatter and code blocks)
- [ ] Step 6: Verify `description` field starts with "Use when" and describes triggering conditions (not workflow summary)
- [ ] Step 7: Write scar report

---

### SKILL.md Spec

**Frontmatter:**
```yaml
---
name: pre-thinking
description: Use when research output (1-kickoff.md + problem-autopsy.md) is complete and you need to surface user-LLM assumption gaps before planning — always runs between research and planning in the samsara chain
---
```

**Body must include:**
1. Core principle (1 sentence)
2. Prerequisites section (read 1-kickoff.md + problem-autopsy.md)
3. Process digraph with nodes: start, step_a, has_gaps (diamond), quick, step_b, uncertain (diamond), step_c, planning (doublecircle), rtr (doublecircle)
4. Brief Step A description (write all gaps once; quick-pass if none; see flow.md)
5. Brief Step B description (groups ≤3; AskUserQuestion; append; see flow.md)
6. Brief Step C description (AskUserQuestion: Proceed / Accept gap / Return to Research)
7. Output section: `changes/<feature>/pre-thinking.md` (single file, LLM single-writer, presence of `## Step C — Commitment` = complete)
8. Transition: invoke `samsara:planning` after Proceed or Accept gap

**Yin-side constraints to include in SKILL.md body:**
- "LLM is the sole writer to pre-thinking.md. User responds via AskUserQuestion only."
- "Presence of `## Step C — Commitment` signals session complete. Absence = K3b interrupted."
- "Step A is written in one shot. Do NOT start asking questions before Step A is complete."

---

### flow.md Spec

Sections to include:

**1. Gap Identification**
A gap is a decision the LLM would need to make that research has not constrained. Examples: interface ownership unclear, success definition undefined, location ambiguous. NOT a gap: implementation detail choices that don't change behavior.

**2. Group Formation**
Group questions by topic domain and answer-interdependency. Questions whose answers depend on each other belong in the same group. Across groups, order by resolution dependency (groups whose answers unblock other groups come first).

**3. Group Overflow Procedure**
If a group has N > 3 questions:
- Round 1: first 3 questions
- Round 2: remaining N-3 questions (≤3; if still > 3, add Round 3)
- Label each round in pre-thinking.md as "Group X, Round Y"

**4. File-Edit Detection Procedure**
Before each Step B append:
1. Read current `pre-thinking.md`
2. Compare Step A section and all prior Step B groups to the content written by LLM in those sections
3. If content differs: print "I see you've made edits to pre-thinking.md. Incorporating your changes." Treat the user's version as authoritative for the differing sections.
4. Then append the new group's answers.

**5. K3b Recovery Procedure**
On session start, read `pre-thinking.md` if present:
- If file absent: normal start
- If `## Step C — Commitment` present: session complete, proceed to planning
- If `## Step C — Commitment` absent: interrupted session. Inform user: "Pre-thinking was interrupted. Last completed section: [Step A | Group N]." Offer: Resume (continue from next group) / Restart (clear file, begin fresh Step A).

**6. Return to Research Write Format**
When commitment = Return to Research:
```markdown
## Step C — Commitment

**Date:** <ISO timestamp>
**Decision:** Return to Research
**Accepted gaps:** none
**Unresolved gaps:**
- Gap <n> (<label>): <specific question that needs research to answer>
[... list all unresolved gaps from Step A ...]
```
After writing, do NOT invoke `samsara:planning`. State to user: "Pre-thinking suspended. The above gaps require clarification before planning. Please re-invoke `samsara:research`."

---

### templates/pre-thinking.md Spec

```markdown
# Pre-thinking: <feature-name>

## Session: <ISO timestamp>

## Step A — Questions
<!-- LLM writes ALL gaps here in one shot. This section is written once and never modified. -->
<!-- For each gap, include: Question (specific, non-leading) + Hypothesis (LLM's current assumption). -->
<!-- If no gaps: write "gaps: none identified — proceeding directly to commitment." -->

### Gap 1: <short topic label>
**Question:** <specific, non-leading question>
**Hypothesis:** <what LLM would assume if user said nothing — visible for user to challenge>

---

## Step B — Answers
<!-- LLM appends here after each AskUserQuestion group. Never overwrites Step A or prior groups. -->
<!-- Each group is appended below the previous. Read file before appending (see flow.md). -->

### Group 1: <theme>
**Q:** <question text from Step A>
**A:** <user's answer, appended by LLM after AskUserQuestion>

---

## Step C — Commitment
<!-- LLM writes this section after Step C AskUserQuestion. Its presence = session complete. -->
<!-- Absence of this section = K3b interrupted state. -->

**Date:** <ISO timestamp>
**Decision:** <Proceed | Accept gap | Return to Research>
**Accepted gaps:** <list gap labels, or "none">
**Unresolved gaps:** <list gap labels with specific question, or "none">
```

## Expected Scar Report Items

- Potential shortcut: SKILL.md body exceeds 500 words — move detail to flow.md
- Potential shortcut: description field summarizes workflow instead of triggering conditions
- Potential shortcut: Step A and Step B share one "write" step — they must be separate writes with explicit yin constraints
- Assumption to verify: `header` field in all AskUserQuestion calls ≤ 12 chars

## Acceptance Criteria

- Covers: "Success - full Q&A with gaps resolved via Proceed"
- Covers: "Success - quick-pass for gap-free research"
- Covers: "Success - Return to Research with documented gap list"
- Covers: "Silent failure - K3b interrupted session looks complete"
