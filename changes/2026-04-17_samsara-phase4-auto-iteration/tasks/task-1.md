# Task 1: Extend scar-schema.yaml with resolved_items and deferred flag

## Context

Read: overview.md

雙層 iteration 需要 scar report 能表達：
1. **Task-level iteration 已修復的 items**（resolved_items）
2. **推遲到 feature-level 的 items**（deferred_to_feature_iteration flag）

目前的 `scar-schema.yaml`（位於 `samsara/skills/implement/templates/`）有 `known_shortcuts`、`silent_failure_conditions`、`assumptions_made`，但沒有追蹤哪些 items 被修復了、哪些被推遲了。

需要向後兼容 — 新增的欄位是 optional，舊格式的 scar reports 仍然有效。

## Files

- Modify: `samsara/skills/implement/templates/scar-schema.yaml`

## Death Test Requirements

- Test: 新增的欄位必須是 optional — 不加 resolved_items 和 deferred flag 的 scar report 仍然是 valid
- Test: resolved_items 中的每個 item 必須引用原始 section（known_shortcuts / silent_failure_conditions / assumptions_made）

## Implementation Steps

- [ ] Step 1: 在 schema 中加入 `resolved_items` section
- [ ] Step 2: 在 `assumptions_made` 的 item 中加入 optional `deferred_to_feature_iteration` flag
- [ ] Step 3: 在 `known_shortcuts` 和 `silent_failure_conditions` 中加入 optional `deferred_to_feature_iteration` flag
- [ ] Step 4: 更新 Verbatim Example 展示新欄位
- [ ] Step 5: 更新 Rules section 說明新欄位語義
- [ ] Step 6: Write scar report

## Expected Scar Report Items

- Potential shortcut: resolved_items 是 free-form list，沒有 strong reference 回原始 item — 可能出現 resolved_items 描述與原始 item 不匹配的情況
- Assumption to verify: 向後兼容 — 舊 scar reports 在 Level 2 aggregate 時是否能正確處理（缺少 deferred flag = 全部視為 unresolved）

## Acceptance Criteria

- Covers: "Success - Level 1 self-iteration resolves task-scope items"
