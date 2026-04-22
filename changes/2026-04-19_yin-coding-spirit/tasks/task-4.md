# Task 4: Wire parallel dispatch into samsara:iteration skill

## Context

Read: overview.md

`samsara:iteration` skill 在每個 deferred scar fix 完成後也 dispatch `samsara:code-reviewer` 做 review (line ~100)。此 task 將該觸發點改為並行 dispatch 兩個 reviewer。

邏輯與 Task 3 相同（Task 3 為 implement skill、Task 4 為 iteration skill），但 file 和 exact context 不同。兩 task 可獨立並行執行。

關鍵差異 vs Task 3：
- iteration skill 的 fix loop 是 per-scar-item，per-fix commit，review 頻率可能比 implement 高
- iteration 也要更新 signal_lost 計算，code quality review 的結果可能影響 signal_lost metric（但不在此 task scope）

## Files

- Modify: `/Users/yuyu_liao/personal/kaleidoscope-tools/samsara/skills/iteration/SKILL.md`
  - Line ~96-102 (Fix loop: dispatch samsara:implementer → code review → per-fix commit)

## Death Test Requirements

- **Dispatch statement test**: iteration SKILL.md 必須明確說明兩個 reviewer 並行 dispatch
- **Missing-reviewer handling test**: 必須有段落說明「若只收到一份，block per-fix commit」
- **Commit-gate test**: per-fix commit 只能在 both reviewers PASS 時發生
- **Consistency test**: iteration 和 implement 的 review dispatch spec 應結構一致（避免 skill-specific drift）

## Implementation Steps

- [ ] Step 1: 讀現有 `samsara/skills/iteration/SKILL.md`，找出 L100 附近 review dispatch 位置
- [ ] Step 2: Cross-reference Task 3 完成後的 implement SKILL.md（若 Task 3 先完成），確保 spec 結構一致
- [ ] Step 3: 寫 validation shell `tests/samsara/code-quality-reviewer/iteration-wiring.sh` 檢查關鍵 sentences
- [ ] Step 4: 執行 validation — verify fails
- [ ] Step 5: 修改 SKILL.md：
  - Line ~100 改為: "Main agent: parallel dispatch `samsara:code-reviewer` 和 `samsara:code-quality-reviewer`"
  - 加入 Aggregation rule（同 Task 3）
  - 更新 per-fix commit 的前置條件: "兩個 reviewers 都 PASS 才 commit"
- [ ] Step 6: 執行 validation — verify passes
- [ ] Step 7: 寫 scar report — 特別 note 任何與 implement skill 的 drift
- [ ] Step 8: Commit

## Expected Scar Report Items

- Potential shortcut: 複製 implement SKILL.md 的文字但沒針對 iteration 的 per-fix commit 語境調整
- Potential shortcut: 漏掉 signal_lost recalculation 與 code-quality review 的潛在 interaction（不在此 scope 但要 flag）
- Potential shortcut: 和 Task 3 drift，兩個 skill 的 review dispatch 說法不一致，造成未來維護者困惑
- Assumption to verify: iteration 的 fix dispatch 和 implement 的 task dispatch 在 aggregation 規則上可以完全對稱（若有差異，需要明確說明）

## Acceptance Criteria

Covers:
- "Parallel dispatch silent skip" — iteration skill 的 Aggregation rule section
- "Success - parallel dispatch returns both results" — iteration 在 per-fix 循環中的支撐
