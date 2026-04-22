# Task 1: Create security-privacy-review SKILL.md

## Context

Read: overview.md

We are adding a new chain skill `samsara:security-privacy-review` to the samsara plugin. This skill sits between implement/iteration and validate-and-ship. It uses the platform's built-in security & privacy review capability to check committed changes before shipping.

The skill is platform-agnostic — it describes intent, not mechanism. It has a human gate when issues are found, and an inline fix loop.

## Files

- Create: `skills/security-privacy-review/SKILL.md`

## Death Test Requirements

- Test: skill must handle empty diff (no changes to review) — flag as unusual, not silently pass
- Test: skill must handle platform with no security review capability — make degradation visible, not silently skip
- Test: skill must handle unknown/partial review results — treat as unknown, never as pass
- Test: fix loop must re-review full diff (not just fix delta) to catch new issues introduced by fixes

## Implementation Steps

- [ ] Step 1: Write death tests (verify the SKILL.md content addresses all death cases)
- [ ] Step 2: Create `skills/security-privacy-review/SKILL.md` with:
  - YAML frontmatter (name, description)
  - Process flow (graphviz digraph)
  - Prerequisites: committed changes from implement/iteration
  - Step 1: Compute diff (git diff against base branch)
  - Step 2: Invoke platform security & privacy review (abstract — no specific tool named)
  - Step 3: Result handling (pass / fail / unknown)
  - Human gate on fail: present issues + fix suggestions
  - Fix loop: inline fix → commit fix → re-review full diff
  - Safety valve: max 3 fix rounds
  - Unknown handling: present to human with options (retry / manual confirm / stop)
  - Empty diff handling: flag as unusual
  - Platform absent handling: make degradation visible
  - Yin-side constraints
  - Red flags
  - Transition: → validate-and-ship
- [ ] Step 3: Verify SKILL.md covers all acceptance.yaml death_path scenarios
- [ ] Step 4: Write scar report
- [ ] Step 5: Commit

## Expected Scar Report Items

- Potential shortcut: writing generic "use platform's built-in tool" without specifying what happens when the tool doesn't exist
- Assumption to verify: that inline fix + commit + re-review cycle is simple enough to describe in a skill without needing a separate fix protocol
- Assumption to verify: that max 3 rounds is a reasonable safety valve (not too many, not too few)

## Acceptance Criteria

- Covers: "Silent failure - review tool silently skips file types"
- Covers: "Silent failure - empty diff treated as pass"
- Covers: "Silent failure - platform has no security review capability"
- Covers: "Silent failure - partial or timed-out review treated as pass"
- Covers: "Silent failure - fix loop produces new vulnerabilities"
- Covers: "Degradation - fix loop exceeds max rounds"
- Covers: "Success - no issues found"
- Covers: "Success - issues found, fixed, re-review passes"
- Covers: "Success - unknown state handled by human"
