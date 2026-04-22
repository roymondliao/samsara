# Task 2: Add self-iteration step to implementer.md (Level 1)

## Context

Read: overview.md

`samsara/agents/implementer.md` 定義了 implementer subagent 的行為。目前的 execution order 是：

```
1-6. STEP 0 → death tests → unit tests → implement → all tests pass
7.   Write scar report
8.   Report back
```

需要在 step 7 和 step 8 之間加入 **self-iteration** 步驟：

```
7.   Write scar report
8.   Self-iteration: 審視 scar items，修 task-scope 內的 actionable items
9.   Updated scar report (resolved_items + remaining)
10.  Report back
```

Self-iteration 的規則：
- 只修 task scope 內的 items（不跨 files 到其他 tasks）
- Unverified assumptions → 嘗試 verify（寫 test 或檢查條件）
- Known shortcuts → 成本合理就修
- Silent failure conditions → 加 detection 或 handling
- 修不了的 → 標記 `deferred_to_feature_iteration: true`
- 不是所有 items 都必須修 — 但全部 defer 會被 code reviewer 質疑

同時需要更新 implementer 的 Self-Review checklist 加入 self-iteration 相關的檢查。

## Files

- Modify: `samsara/agents/implementer.md`

## Death Test Requirements

- Test: self-iteration 必須有 scope 限制的明確說明（只修 task scope 內的 files）
- Test: 全部 items defer 的情況必須被標記為需要解釋（不能 silently defer all）
- Test: self-iteration 修復後必須重跑 tests 確認沒有 regression

## Implementation Steps

- [ ] Step 1: 在 Execution Order section 加入 self-iteration 步驟（step 8-9）
- [ ] Step 2: 寫 self-iteration 的規則和 scope 限制
- [ ] Step 3: 更新 Scar Report section 說明 updated scar report 的格式（引用 scar-schema.yaml 的 resolved_items）
- [ ] Step 4: 更新 Self-Review checklist 加入 self-iteration 檢查
- [ ] Step 5: 更新 Report Format section 包含 self-iteration 結果
- [ ] Step 6: Write scar report

## Expected Scar Report Items

- Potential shortcut: self-iteration 的品質完全依賴 implementer agent 的自律 — 沒有外部 enforcement
- Assumption to verify: subagent 在 self-iteration 時是否還有足夠的 context window（implement + tests + scar report 已經消耗大量 context）
- Assumption to verify: self-iteration 修復後重跑 tests 的指示是否被 subagent 遵循

## Acceptance Criteria

- Covers: "Success - Level 1 self-iteration resolves task-scope items"
- Covers: "Silent failure - cargo-cult self-iteration defers all items to Level 2"
- Covers: "Silent failure - Level 1 self-iteration modifies files outside task scope"
