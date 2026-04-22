# Task 6: Update samsara-bootstrap skill chain and routing graph

## Context

Read: overview.md

`samsara-bootstrap/SKILL.md` 需要更新：

1. **Routing digraph** — 加入 iteration 節點：
   - implement → iteration（可選）→ validate-and-ship
   - 保留 implement → validate-and-ship 的 skip 路徑

2. **Chain Skills 清單** — 加入 `samsara:iteration`，描述為 chain skill（由 implement 觸發）

3. **Skill descriptions** — iteration 的 description 要清楚說明它是 feature-level iteration（Level 2），task-level iteration（Level 1）已融入 implement

注意：iteration 是 **Chain Skill**（不由使用者直接 invoke），但在 routing 中可見。

## Files

- Modify: `samsara/skills/samsara-bootstrap/SKILL.md`

## Death Test Requirements

- Test: routing digraph 必須顯示 implement → iteration → validate-and-ship 路徑
- Test: routing digraph 必須保留 implement → validate-and-ship skip 路徑
- Test: iteration 在 Chain Skills 清單中，不在 Entry Skills 中

## Implementation Steps

- [ ] Step 1: 更新 routing digraph
- [ ] Step 2: 更新 Chain Skills 清單
- [ ] Step 3: Write scar report

## Expected Scar Report Items

- Potential shortcut: bootstrap 的 digraph 是 documentation 不是 enforced routing
- Assumption to verify: bootstrap token 增加量是否影響 session context

## Acceptance Criteria

- Covers: "Success - user skips Level 2 (backward compatible)"
