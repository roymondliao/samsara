# Death Tests: extract-pre-thinking-step

Behavioral verification scenarios for `samsara:pre-thinking`. These are human-reviewed checklists —
there is no test runner. A reviewer reads each scenario and evaluates whether the implemented
skill files (SKILL.md, flow.md, template) constrain the agent to produce the expected behavior.

Each scenario covers one silent failure path or degradation path. Happy-path coverage is
in acceptance.yaml; these tests focus on what must NOT happen.

**Acceptance.yaml cross-reference table** (verified at bottom of this file):

| Death test | acceptance.yaml scenario |
|-----------|--------------------------|
| DT-1: K3b interrupted session | "Silent failure - K3b interrupted session looks complete" |
| DT-2: Quick-pass with no gaps | "Silent failure - quick-pass overuse hides real gaps" + "Success - quick-pass for gap-free research" |
| DT-3: Group overflow | "Degradation - group overflow (> 3 questions in one AskUserQuestion call)" |
| DT-4: Append-only enforcement | "Silent failure - file-edit detection miss" (append side) |
| DT-5: File-edit detection | "Silent failure - file-edit detection miss" (detection side) |
| DT-6: Commitment via AskUserQuestion | "Silent failure - LLM leading the answers" |
| DT-7: Return to Research path | "Silent failure - Return to Research without gap documentation" + "Success - Return to Research with documented gap list" |

---

## DT-1: K3b Interrupted Session

**Scenario name:** K3b interrupted session — agent must detect and halt, not proceed silently

**Setup (precondition):**
- A `pre-thinking.md` file exists in the feature's `changes/` directory
- The file contains a written `## Step A — Questions` section with ≥1 gap entry
- The file contains a written `## Step B — Answers` section with ≥1 group
- The file does NOT contain a `## Step C — Commitment` section
- This represents a session that ended after Step B started but before Step C was written

**Action (what triggers it):**
A new agent session starts and reads `pre-thinking.md` as part of the pre-thinking skill's session-start check.

**Expected agent behavior:**
1. Agent reads the file and checks for the presence of `## Step C — Commitment`
2. Agent detects that the section is absent
3. Agent outputs a message that names the interrupted state explicitly — for example: "pre-thinking session was interrupted before commitment was reached"
4. Agent identifies the last completed step (Step A written, Step B partially or fully written)
5. Agent offers the user two options via AskUserQuestion: Resume (continue from last incomplete group) or Restart (overwrite file with fresh Step A)
6. Agent does NOT invoke `samsara:planning`
7. Agent does NOT proceed past this check without user input

**Failure signal (what wrong behavior looks like):**
- Agent reads `pre-thinking.md`, notes it exists, and proceeds directly to planning without checking for `## Step C — Commitment`
- Agent outputs "pre-thinking complete" or equivalent when Step C section is absent
- Agent invokes `samsara:planning` with a `pre-thinking.md` that has no commitment section
- Agent silently re-runs Step A without informing the user that a prior session's work exists
- Any variant of planning being invoked when `pre-thinking.md` lacks `## Step C — Commitment`

**Observable pass criterion:**
The SKILL.md or flow.md file contains an explicit instruction to check for `## Step C — Commitment` absence at session start, and prescribes halting with user notification before any planning invocation.

---

## DT-2: Quick-Pass — No Gaps Identified

**Scenario name:** Quick-pass produces correct minimal pre-thinking.md with no Step B

**Setup (precondition):**
- Research artifacts (`1-kickoff.md` + `problem-autopsy.md`) are present and complete
- All decisions and assumptions in the research output are explicitly documented — no undocumented assumptions visible in the artifacts
- The LLM has read the research artifacts and determined that no gaps exist

**Action (what triggers it):**
Pre-thinking skill is invoked. LLM reaches Step A determination and finds no gaps.

**Expected agent behavior:**
1. LLM writes `## Step A — Questions` section containing only: `gaps: none identified — proceeding directly to commitment.`
2. LLM does NOT write any `## Step B — Answers` section
3. LLM proceeds immediately to Step C (commitment)
4. Step C is collected via AskUserQuestion (not inferred from context) — see DT-6
5. `pre-thinking.md` contains: Step A (with `gaps: none identified`), NO Step B section, Step C with `Decision: Proceed`
6. Planning is invoked after Step C confirmation
7. Total AskUserQuestion calls: exactly 1 (the commitment gate in Step C)

**Failure signal (what wrong behavior looks like):**
- `pre-thinking.md` contains `gaps: none identified` in Step A but ALSO contains a `## Step B — Answers` section (Step B was written even though no gaps existed)
- LLM asks clarifying questions during Step B despite Step A showing no gaps
- LLM writes placeholder Step B content ("No questions for this session")
- More than 1 AskUserQuestion call issued when there were no gaps (extra questions asked despite quick-pass)
- Step C is absent from the file (quick-pass short-circuited but never closed the session)

**Observable pass criterion:**
The SKILL.md and flow.md explicitly state: when `gaps: none identified`, skip Step B entirely and proceed to Step C. The template marks Step B as absent (not empty) in the quick-pass case.

---

## DT-3: Group Overflow — More Than 3 Questions in One Topic Cluster

**Scenario name:** 5-question cluster must be split into two AskUserQuestion calls (3 + 2)

**Setup (precondition):**
- Research artifacts have a topic domain with 5 closely related questions that the LLM has identified as belonging to the same cluster (e.g., all about database schema design)
- All 5 questions require the same user's mental context to answer (legitimate grouping by topic)

**Action (what triggers it):**
Pre-thinking skill reaches Step B and begins forming groups. LLM has 5 questions for one cluster.

**Expected agent behavior:**
1. LLM splits the 5-question cluster into two sub-rounds: Round 1 with 3 questions, Round 2 with 2 questions
2. LLM issues first AskUserQuestion call with exactly 3 questions
3. LLM appends Round 1 answers to `pre-thinking.md` under `### Group N: <theme> (round 1)`
4. LLM issues second AskUserQuestion call with the remaining 2 questions
5. LLM appends Round 2 answers under `### Group N: <theme> (round 2)`
6. Both rounds are labeled as sub-rounds of the same group — the group identity is preserved in the file
7. Total questions per AskUserQuestion call: never more than 3

**Failure signal (what wrong behavior looks like):**
- A single AskUserQuestion call contains 4 or 5 questions
- LLM puts all 5 questions in one call and notes "these are all related"
- LLM drops 2 questions to stay under the limit rather than splitting into rounds
- Round 2 is labeled as a separate group (Group N+1) instead of a sub-round of Group N, breaking audit trail continuity
- `pre-thinking.md` shows Group N with only 3 questions and no trace that 2 were deferred

**Observable pass criterion:**
The flow.md contains an explicit group overflow procedure: if cluster size N > 3, split into ⌈N/3⌉ rounds, first round 3 questions, last round ≤3 questions, all labeled as sub-rounds of the same group.

---

## DT-4: Append-Only Enforcement — Step B Must Not Overwrite Prior Content

**Scenario name:** Appending Step B answers must leave Step A and prior groups intact

**Setup (precondition):**
- `pre-thinking.md` has a complete `## Step A — Questions` section with 3 gap entries
- `pre-thinking.md` has `## Step B — Answers` with one completed group (Group 1) already appended
- Agent is about to append Group 2 answers

**Action (what triggers it):**
Agent completes AskUserQuestion for Group 2 and is about to write the answers to `pre-thinking.md`.

**Expected agent behavior:**
1. Agent reads the current file before writing
2. Agent writes Group 2 content BELOW the existing Step A and Group 1 content
3. Step A section is byte-for-byte identical after the write
4. Group 1 content is byte-for-byte identical after the write
5. The only change to the file is the addition of Group 2 content at the end of Step B

**Failure signal (what wrong behavior looks like):**
- Step A content is absent or modified after the Group 2 append
- Group 1 content is absent or modified after the Group 2 append
- Agent rewrites the entire file from scratch (rather than appending) when recording Group 2
- Agent truncates the file before writing new content
- A re-generation of Step A occurs (even with identical content) — the write is not purely additive

**Observable pass criterion:**
The SKILL.md or flow.md contains an explicit instruction that Step B writes are append-only — agent appends BELOW all existing content, never rewrites or truncates the file.

---

## DT-5: File-Edit Detection — User Edits pre-thinking.md Between Steps

**Scenario name:** User direct edit between Step A and Step B must be detected and acknowledged, not silently overwritten

**Setup (precondition):**
- `pre-thinking.md` has a complete `## Step A — Questions` section (LLM wrote this in the current session)
- After Step A was written, the user directly edited `pre-thinking.md` — for example, they added a clarifying note to Gap 1 or corrected a hypothesis
- The file on disk differs from what the LLM last wrote
- Agent is about to perform the first Step B append (Group 1)

**Action (what triggers it):**
Agent reads `pre-thinking.md` before performing the first Step B append. The file content differs from the LLM's last-written state.

**Expected agent behavior:**
1. Agent reads `pre-thinking.md` before appending
2. Agent compares current file content against the expected content from its last write
3. Agent detects that the file differs
4. Agent outputs a specific acknowledgment message — exactly or approximately: "I see you've edited pre-thinking.md. Incorporating your changes."
5. Agent incorporates the user's edits (treats them as authoritative) before appending Group 1 answers
6. The appended Group 1 content appears below the user-edited Step A (not below the original Step A)
7. The user's edits are preserved in the final file

**Failure signal (what wrong behavior looks like):**
- Agent appends Group 1 answers without reading the file first (no comparison performed)
- Agent reads the file but does not compare to expected content — proceeds to append without acknowledging the difference
- Agent detects the difference but overwrites the user's edits with the original Step A content before appending
- Agent detects the difference and halts with an error (blocking progress) rather than incorporating and continuing
- No acknowledgment message printed — user has no visibility that their edit was detected

**Observable pass criterion:**
The flow.md contains a file-edit detection procedure prescribing: (a) read file before each Step B append, (b) compare to last-written state, (c) if different: print the acknowledgment message exactly, (d) incorporate edits before appending.

---

## DT-6: Commitment via AskUserQuestion — Never Inferred from Conversation

**Scenario name:** Step C commitment must come from an explicit AskUserQuestion call, not inferred from chat context

**Setup (precondition):**
- Pre-thinking Step B has completed (all groups answered)
- During a Step B AskUserQuestion exchange, the user has already volunteered a preference: "I think we should just proceed, the answers all seem fine"
- The agent has this statement in its conversation context

**Action (what triggers it):**
Agent reaches Step C and is about to record the commitment decision.

**Expected agent behavior:**
1. Agent does NOT treat the user's in-conversation statement as a binding commitment
2. Agent issues a new AskUserQuestion call specifically for Step C commitment
3. The AskUserQuestion offers explicit options: Proceed / Accept gap / Return to Research
4. Agent waits for the user to select one of the options via AskUserQuestion
5. Agent writes Step C to `pre-thinking.md` only after receiving the AskUserQuestion response
6. The `Decision:` field in Step C reflects the AskUserQuestion response, not the earlier conversational statement

**Failure signal (what wrong behavior looks like):**
- Agent skips the Step C AskUserQuestion call because the user already said "let's proceed" in conversation
- Agent writes `Decision: Proceed` to Step C without issuing an AskUserQuestion call
- Agent infers commitment from the tone of user answers in Step B
- Agent issues a text prompt (not AskUserQuestion) for the commitment decision
- `pre-thinking.md` Step C is written before any Step C AskUserQuestion call is recorded in the session

**Observable pass criterion:**
The SKILL.md body contains an explicit constraint: "Step C commitment must be collected via AskUserQuestion — never inferred from conversation context." The flow.md prescribes an AskUserQuestion call as the mandatory gate for writing Step C.

---

## DT-7: Return to Research Path — Gap Documentation Required

**Scenario name:** Return to Research commitment must produce a documented gap list in Step C, not silent termination

**Setup (precondition):**
- Pre-thinking has reached Step C (or a mid-Step-B Return to Research option was selected)
- User selects "Return to Research" as their decision (via AskUserQuestion)
- `pre-thinking.md` has Step A with 3 gap entries (Gap 1, Gap 2, Gap 3); Step B has partial answers

**Action (what triggers it):**
Agent receives "Return to Research" from the AskUserQuestion call in Step C (or mid-Step-B).

**Expected agent behavior:**
1. Agent writes `## Step C — Commitment` section to `pre-thinking.md`
2. The section contains `Decision: Return to Research`
3. The section contains a non-empty `unresolved_gaps:` list with specific gap labels (e.g., `Gap 1: <topic>`, `Gap 3: <topic>`)
4. The section contains a brief rationale for why each gap remains unresolved
5. Agent does NOT invoke `samsara:planning`
6. Agent outputs a message identifying which gaps need to be addressed in research
7. Agent terminates the pre-thinking session cleanly (does not loop back to Step B)

**Failure signal (what wrong behavior looks like):**
- Agent writes Step C with `Decision: Return to Research` but leaves `unresolved_gaps: none` or omits the field entirely
- Agent terminates without writing Step C (session ends but no commitment section exists — looks like K3b interruption)
- Agent invokes `samsara:planning` after a Return to Research commitment
- Agent writes Step C but does not specify which gaps are unresolved — user cannot tell what to re-research
- `unresolved_gaps` list contains generic labels ("unclear requirements") rather than references to specific Step A gap identifiers

**Observable pass criterion:**
The SKILL.md or flow.md specifies: when commitment = Return to Research, write Step C with `Decision: Return to Research` and a `unresolved_gaps` list referencing specific Step A gap labels; do NOT invoke planning; inform user of the gap list explicitly.

---

## Coverage Verification

### All 7 task-specified death cases covered:

- [x] DT-1 covers: K3b interrupted session
- [x] DT-2 covers: Quick-pass no gaps
- [x] DT-3 covers: Group overflow
- [x] DT-4 covers: Append-only enforcement
- [x] DT-5 covers: File-edit detection
- [x] DT-6 covers: Commitment via AskUserQuestion
- [x] DT-7 covers: Return to Research path

### All acceptance.yaml death_path and degradation scenarios covered:

- [x] "Silent failure - K3b interrupted session looks complete" → DT-1
- [x] "Silent failure - LLM leading the answers" → DT-6 (commitment inferred from conversation = LLM leading)
- [x] "Silent failure - quick-pass overuse hides real gaps" → DT-2 (observable failure signal: Step B present when gaps: none identified)
- [x] "Silent failure - file-edit detection miss" → DT-4 (append overwrites) + DT-5 (detection mechanism)
- [x] "Silent failure - Return to Research without gap documentation" → DT-7
- [x] "Degradation - group overflow (> 3 questions in one AskUserQuestion call)" → DT-3
- [x] "Degradation - planning starts without pre-thinking.md" → DT-1 (planning guard) + covered implicitly by DT-1 failure signal

### Note on "Degradation - planning starts without pre-thinking.md":

This scenario tests planning's guard (Task 3 scope — modifying `skills/planning/SKILL.md`), not
pre-thinking's behavior. DT-1 covers the pre-thinking side (detecting K3b). The planning-side
guard (blocking invocation when `pre-thinking.md` is absent) is verified in Task 3's own
test scope. The cross-reference is recorded here so Task 3 does not assume coverage from
these tests.
