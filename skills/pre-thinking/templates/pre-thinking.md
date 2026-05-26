# Pre-thinking: <feature-name>

## Session: <ISO timestamp>

## Step A — Questions
<!-- LLM writes ALL gaps here in one shot. This section is written ONCE and never modified after Step A completes. -->
<!-- For each gap: a specific non-leading Question + a Hypothesis (LLM's current assumption). -->
<!-- Hypothesis is shown to the user for challenge — do NOT frame it as the answer. -->
<!-- Quick-pass: if no gaps found, write the single line below and skip Step B entirely. -->

<!-- quick-pass line: -->
<!-- gaps: none identified — proceeding directly to commitment. -->

### Gap 1: <short topic label>
**Question:** <specific, non-leading question — no embedded recommendation>
**Hypothesis:** <LLM's current assumption — what it would assume if the user said nothing>

### Gap 2: <short topic label>
**Question:** <specific, non-leading question>
**Hypothesis:** <LLM's current assumption>

<!-- Add more Gap N sections as needed. Remove unused template sections before writing. -->

---

## Step B — Answers
<!-- LLM APPENDS here after each AskUserQuestion group. -->
<!-- NEVER overwrite Step A or any prior group. Each append adds content BELOW all existing content. -->
<!-- Read the file before each append (see flow.md §4 file-edit detection procedure). -->
<!-- If file differs from last-written state: print acknowledgment, incorporate edits, then append. -->
<!-- Quick-pass: if Step A contains "gaps: none identified", this section is ABSENT (not empty). -->

### Group 1: <theme>
**Q:** <question text from Step A>
**A:** <user's answer, appended by LLM after AskUserQuestion>

<!-- For groups with > 3 questions, use round labels: -->
<!-- ### Group 1: <theme> (round 1) -->
<!-- ### Group 1: <theme> (round 2) -->
<!-- Group identity must be preserved across rounds — do NOT relabel as Group 2. -->

<!-- Add more Group N sections as needed. Remove unused template sections before writing. -->

---

## Step C — Commitment
<!-- LLM writes this section ONCE, after the Step C AskUserQuestion call. -->
<!-- PRESENCE of this section = session complete. ABSENCE = K3b interrupted state. -->
<!-- Step C commitment must be collected via AskUserQuestion — never inferred from conversation context. -->
<!-- Do NOT write this section before receiving the AskUserQuestion commitment response. -->

**Date:** <ISO timestamp>
**Decision:** <Proceed | Accept gap | Return to Research>
**Accepted gaps:** <list gap labels accepted as undocumented assumptions, or "none">
**Unresolved gaps:** <list gap labels with specific Step A question reference, or "none">

<!-- Return to Research format for Unresolved gaps: -->
<!-- - Gap 1 (interface-ownership): <specific question that needs research to answer> -->
<!-- - Gap 3 (success-definition): <specific question that needs research to answer> -->
<!-- Unresolved gaps MUST reference specific Step A gap labels — not generic descriptions. -->
