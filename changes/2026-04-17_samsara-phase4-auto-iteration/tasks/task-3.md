# Task 3: Update implement/SKILL.md per-task execution order and transition

## Context

Read: overview.md

`samsara/skills/implement/SKILL.md` 需要兩處修改：

### 1. Per-Task Execution Order（Level 1 integration）

目前的 Implementer section（line 125-135）：
```
1. STEP 0
2-5. Death tests, unit tests
6. Implement
7. Run all tests
8. Write scar report
9. Report back
```

需要在 step 8 和 step 9 之間加入 self-iteration 步驟的描述，與 `implementer.md` 的修改保持一致。

### 2. Transition（Level 2 entry gate）

目前的 Transition section（line 175-181）直接跳到 validate-and-ship。需要改為 A/B 選項：
- (A) 進入 Iteration — 審視 feature-level scar items
- (B) Skip — 直接進入 Validation

Transition message 需要包含 remaining scar items 的 summary（Level 1 修完後剩餘的 items）。

## Files

- Modify: `samsara/skills/implement/SKILL.md`

## Death Test Requirements

- Test: 使用者選 B (skip) 的行為必須與修改前完全一致
- Test: Per-Task Execution Order 必須與 implementer.md 的步驟一致（不能出現兩份文件描述不同步）
- Test: Transition message 中的 remaining items 計算不能把 Level 1 resolved 的 items 計入

## Implementation Steps

- [ ] Step 1: 更新 Per-Task Execution Order，加入 self-iteration 步驟
- [ ] Step 2: 更新 Transition section，加入 A/B 選項
- [ ] Step 3: 更新 digraph 中的 transition node 反映新的 routing
- [ ] Step 4: 確認 skip 路徑完全向後兼容
- [ ] Step 5: Write scar report

## Expected Scar Report Items

- Potential shortcut: implement/SKILL.md 和 implementer.md 描述 self-iteration 的方式可能不完全一致 — 維護兩份描述的同步成本
- Assumption to verify: 使用者理解 A/B 選項的意義

## Acceptance Criteria

- Covers: "Success - user skips Level 2 (backward compatible)"
- Covers: "Success - Level 1 self-iteration resolves task-scope items"
