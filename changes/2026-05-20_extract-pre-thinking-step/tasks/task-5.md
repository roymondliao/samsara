# Task 5: Update skills/samsara-bootstrap/SKILL.md

## Context

Read: `overview.md`

`skills/samsara-bootstrap/SKILL.md` is the session-start skill that establishes routing for the entire samsara chain. It has two places that need updating:

1. **Dot graph**: The `research -> planning [label="human gate"]` edge must become `research -> pre_thinking -> planning` with a new `pre_thinking` node.
2. **Chain Skills list**: `samsara:pre-thinking` must be added to the "Chain Skills" section in the right position (between research and planning in chain order).

This is a high-visibility change — every session that reads bootstrap will see the new chain.

## Files

- Modify: `skills/samsara-bootstrap/SKILL.md`

## Death Test Requirements

- Test: agent reading bootstrap dot graph sees `research -> pre_thinking -> planning` chain (not `research -> planning`)
- Test: agent reading bootstrap Chain Skills list finds `samsara:pre-thinking` listed between research and planning chain steps

## Implementation Steps

- [ ] Step 1: Confirm `death-tests.md` exists from Task 1
- [ ] Step 2: Read `skills/samsara-bootstrap/SKILL.md` fully before editing
- [ ] Step 3: **Update dot graph** — add `pre_thinking` node and update edges per spec below
- [ ] Step 4: **Update Chain Skills list** — add pre-thinking entry per spec below
- [ ] Step 5: Verify the dot graph renders correctly (check for matching node references)
- [ ] Step 6: Verify `research -> planning` edge no longer exists (replaced by two-step chain)
- [ ] Step 7: Write scar report

---

### Dot Graph Changes

**Find and remove:**
```dot
research -> planning [label="human gate"];
```

**Add these nodes and edges** (in the node declarations section):
```dot
pre_thinking [label="samsara:pre-thinking\n(assumption alignment)"];
```

**Add these edges** (after research node declarations):
```dot
research -> pre_thinking [label="human gate"];
pre_thinking -> planning [label="human gate"];
```

The rest of the graph (planning → implement, etc.) remains unchanged.

---

### Chain Skills List Changes

**Current "Chain Skills" section:**
```markdown
**Chain Skills（鏈式 — 由前一階段觸發，不直接 invoke）：**
- **samsara:planning** — research 完成後。產出 plan + acceptance + tasks
- **samsara:implement** — ...
```

**Replace with:**
```markdown
**Chain Skills（鏈式 — 由前一階段觸發，不直接 invoke）：**
- **samsara:pre-thinking** — research 完成後、planning 前。顯化 user-LLM assumption gap，產出 pre-thinking.md audit log；恆被 invoke（無條件）
- **samsara:planning** — pre-thinking 完成後（commitment = Proceed 或 Accept gap）。產出 plan + acceptance + tasks
- **samsara:implement** — ...
```

(Keep all entries after `samsara:planning` unchanged.)

## Expected Scar Report Items

- Potential shortcut: updating the Chain Skills list but not the dot graph (or vice versa) — both must be updated
- Potential shortcut: listing pre-thinking as an Entry Skill instead of Chain Skill (it is NOT directly invocable from user intent)
- Assumption to verify: the dot graph remains syntactically valid after changes (all node references match declared nodes)

## Acceptance Criteria

- Covers: chain routing — agent reading bootstrap knows the unconditional research → pre-thinking → planning chain
