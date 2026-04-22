# Task 1: Update Planning Skill — Add Step 1.5 Pre-thinking

## Context

Read: `overview.md`

This task modifies `samsara/skills/planning/SKILL.md`.

The problem: Planning currently reads Research and proceeds directly to writing content, without first asking "what information do I actually need to write this plan?" This allows Planning to silently fill gaps using bias, bypassing the human gate.

The fix: insert Step 1.5 "Pre-thinking" between the Prerequisites section and Step 2 (Technical Specification). Step 1.5 forces Planning to:
1. Reason about what information it needs to write this specific plan (feature-specific, not a checklist)
2. Output a visible "Information Assumptions" artifact
3. Stop at a human gate — human confirms or returns to Research with specific questions

Design principle: framework guarantees the floor (assumption list must be produced), LLM capability determines the ceiling (quality of what's identified). Step 1.5 must NOT contain a rigid checklist of information types.

Current SKILL.md structure:
```
## Prerequisites
## Process (diagram)
## Step 2: Technical Specification
## Step 2.5: Acceptance Criteria
## Step 3: Task Decomposition
## Output
## Transition
```

Target: insert Step 1.5 between Prerequisites and Step 2.

## Files

- Modify: `samsara/skills/planning/SKILL.md`

## Death Test Requirements

- **Death test 1**: Read the modified SKILL.md. Is Step 1.5 positioned BEFORE Step 2? If it appears after "write Tech Spec," the gate is useless.
- **Death test 2**: Is the assumption list described as a mandatory artifact — i.e., "its absence means Step 1.5 was skipped"? If it's described as optional or "recommended," it will be skipped under pressure.
- **Death test 3**: Does Step 1.5 use a checklist of information types (e.g., "check for architectural constraints, performance requirements...")? If yes, it's a rigid spec disguised as pre-thinking. Remove the checklist and replace with a reasoning instruction.
- **Death test 4**: Is the `unknown` / uncertainty case handled? If Step 1.5 only defines "gaps found" and "no gaps found," Planning will silently classify uncertainty as "no gap." The uncertainty state must be explicitly defined.
- **Death test 5**: Is the stop instruction hard? "Do not proceed" vs "consider returning to Research" — soft language is a silent bypass.

## Implementation Steps

- [ ] Step 1: Read current `samsara/skills/planning/SKILL.md` in full
- [ ] Step 2: Run death tests 1-5 against the current file — note what's missing
- [ ] Step 3: Draft Step 1.5 content:
  - Pre-thinking reasoning instruction (feature-specific derivation, not checklist)
  - Information Assumptions artifact format (assumptions, gaps, uncertainties)
  - Hard stop instruction: "If gaps or uncertainties → do NOT proceed to Step 2"
  - Mandatory artifact note: "Absence of assumption list = Step 1.5 skipped"
- [ ] Step 4: Run death tests 1-5 against the draft
- [ ] Step 5: Insert Step 1.5 into SKILL.md at correct position
- [ ] Step 6: Update the process diagram in SKILL.md to include Step 1.5 node
- [ ] Step 7: Verify overall skill flow reads coherently end-to-end
- [ ] Step 8: Write scar report
- [ ] Step 9: Commit

## Expected Scar Report Items

- Potential shortcut: Writing Step 1.5 as a bulleted checklist — this immediately turns it into a rigid spec. If you find yourself listing information types, stop. The instruction must be a reasoning prompt, not a list.
- Potential shortcut: Soft stop language ("should consider returning to Research") — replace with "must stop, do not proceed to Step 2."
- Assumption to verify: Planning agents read and follow SKILL.md steps in order — if agents skip steps, no text-based enforcement survives. Note this as an unresolvable assumption in scar report.
- Assumption to verify: Human gate reviews the assumption list artifact — framework cannot enforce human attention, only make the artifact visible. Note this limitation.

## Acceptance Criteria

- Covers: "Silent failure - gate passes but misses architectural decision" (assumption list is visible → human can catch what LLM missed)
- Covers: "Silent failure - Planning self-derives and labels as Research-confirmed" (hard stop before Step 2 prevents self-derivation from reaching plan content)
- Covers: "Unknown outcome - ambiguous scope decision" (uncertainty case explicitly handled in Step 1.5)
- Covers: "Degradation - gate exists but classification heuristic is too narrow" (pre-thinking has no checklist → no narrow heuristic to game)
- Covers: "Success - Research complete, Planning proceeds" (when all assumptions are confirmed, Step 1.5 completes cleanly)
