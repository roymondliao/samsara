# Task 4: Update skills/research/SKILL.md

## Context

Read: `overview.md`

`skills/research/SKILL.md` currently ends its Transition section with "invoke `samsara:planning` skill." With the new chain, research must invoke `samsara:pre-thinking` instead. This is a small but critical change — if research still points to planning, an agent reading research SKILL.md will skip pre-thinking entirely.

Two places to update:
1. The dot graph `next` node label
2. The Transition section's final instruction

## Files

- Modify: `skills/research/SKILL.md`

## Death Test Requirements

- Test: agent following research SKILL.md transition section invokes `samsara:pre-thinking` (not `samsara:planning`) after producing kickoff.md + problem-autopsy.md
- Test: agent following research SKILL.md dot graph shows `next` node pointing to pre-thinking

## Implementation Steps

- [ ] Step 1: Confirm `death-tests.md` exists from Task 1
- [ ] Step 2: Read `skills/research/SKILL.md` fully before editing
- [ ] Step 3: **Update dot graph** — find `next [label="invoke samsara:planning"...]` and change label to `invoke samsara:pre-thinking`
- [ ] Step 4: **Update Transition section** — find last line "invoke `samsara:planning` skill" and change to "invoke `samsara:pre-thinking` skill"
- [ ] Step 5: Verify no other references to "planning" remain in the Transition section
- [ ] Step 6: Write scar report

---

### Dot Graph Change

**Current:**
```dot
next [label="invoke samsara:planning" shape=doublecircle];
```

**Change to:**
```dot
next [label="invoke samsara:pre-thinking" shape=doublecircle];
```

---

### Transition Section Change

**Current (last 2 lines):**
```markdown
使用者確認後，invoke `samsara:planning` skill。
```

**Change to:**
```markdown
使用者確認後，invoke `samsara:pre-thinking` skill。
```

## Expected Scar Report Items

- Potential shortcut: only updating one of the two locations (dot graph or transition section) — both must be updated
- Assumption to verify: no support files or templates in `skills/research/` reference "planning" in a transition context

## Acceptance Criteria

- Covers: chain integrity — research → pre-thinking transition is explicit and unambiguous
