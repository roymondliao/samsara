# Task 5: Create iteration-log.yaml template

## Context

Read: overview.md

Feature-level iteration（Level 2）需要一個 `iteration-log.yaml` template 來追蹤每輪 iteration 的狀態。

Template 放在 `samsara/skills/iteration/templates/`。

需要記錄的資訊：
- 每輪的 signal_lost before/after
- Triage 結果（fix/accept/defer items）
- Fixes applied 數量
- Fixes 產生的新 scar items 數量
- 每輪的 decision（continue/stop/forced_stop/interrupted）
- Safety valve 觸發原因（如果觸發的話）

參考 scar-schema.yaml 的設計慣例：schema + rules + verbatim example 在同一個檔案中。

## Files

- Create: `samsara/skills/iteration/templates/iteration-log.yaml`

## Death Test Requirements

- Test: template 必須能表達 interrupted 狀態（session 中斷，部分 round）
- Test: signal_lost_before/after 必須是必填欄位
- Test: decision 欄位的 enum 必須包含 interrupted（不能只有 continue/stop/forced_stop）

## Implementation Steps

- [ ] Step 1: 設計 iteration-log.yaml schema
- [ ] Step 2: 加入 schema validation 註解
- [ ] Step 3: 加入 verbatim example
- [ ] Step 4: Write scar report

## Expected Scar Report Items

- Assumption to verify: YAML 格式是否足以表達所有 iteration 狀態

## Acceptance Criteria

- Covers: "Degradation - Level 2 iteration interrupted mid-round"
- Covers: "Success - Level 2 iteration reduces feature-level signal_lost"
