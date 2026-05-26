# Task 6: Update skills/writing-skills/SKILL.md

## Context

Read: `overview.md`

`skills/writing-skills/SKILL.md` guides future skill authors. This task adds the **single-writer artifact invariant** to the "Yin-Side Check for Skills" section. This invariant prevents future skill designs from introducing dual-writer artifacts (the anti-pattern that triggered this entire feature).

This is the only change to writing-skills in this task.

## Files

- Modify: `skills/writing-skills/SKILL.md`

## Death Test Requirements

- Test: agent following writing-skills Yin-Side Check answers question 4 (single-writer check) for any new skill that produces a persisted artifact
- Test: a future skill design with a dual-writer artifact (user + LLM both write to same file) would fail question 4

## Implementation Steps

- [ ] Step 1: Confirm `death-tests.md` exists from Task 1
- [ ] Step 2: Read `skills/writing-skills/SKILL.md` fully before editing
- [ ] Step 3: Locate the "Yin-Side Check for Skills" section (currently 3 questions)
- [ ] Step 4: Add question 4 (single-writer invariant) per spec below
- [ ] Step 5: Verify the new question is framed as a check (actionable, not narrative)
- [ ] Step 6: Write scar report

---

### Addition to Yin-Side Check Section

**Current section ends with question 3.** Add after it:

```markdown
4. **Does this skill produce a persisted artifact?** If yes: who is the sole writer?
   - LLM must be the sole writer to any artifact produced by the skill. User interaction
     goes through AskUserQuestion — answers are written to the artifact BY the LLM, not
     by the user directly.
   - Dual-writer artifacts (user + LLM both write the same file) introduce K3b
     cross-session half-finished state and race conditions between sessions. Do not
     design them.
   - If you find yourself needing user to directly edit a file: that is a signal the
     artifact should either be split (LLM-only part + user-editable part) or the
     interaction should be redesigned as AskUserQuestion.
```

## Expected Scar Report Items

- Potential shortcut: adding the invariant as a note/aside rather than a numbered check — it must be a numbered question in the same format as existing questions 1–3
- Assumption to verify: the addition does not push SKILL.md body over token budget (check word count after edit)

## Acceptance Criteria

- Covers: single-writer invariant persisted in framework-level guidance for future skill authors
