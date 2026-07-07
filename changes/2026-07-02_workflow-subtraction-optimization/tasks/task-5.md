# Task 5: iteration 資料驅動進入 + implement 轉場改寫 + UI 清單措辭修正

## Context

Read: overview.md

現況一：implement 完成後的轉場是無條件詢問「(A) 進入 Iteration (B) Skip」。實際歷史資料顯示 Level 2 iteration 大量橡皮圖章（15 項 triage 中 10 accept / 2 fix）。User 決定改為資料驅動：**存在 cross-task pattern（同一 item 出現於 ≥2 個 task scar）或 signal_lost ≥ 5** 才建議進入；否則預設 skip 並輸出一行可推翻紀錄。**關鍵防線：scar 解析失敗使 signal_lost 不可信時，判準結果是 unknown，不准 skip**（unknown ≠「不需要 iteration」）。

現況二：implement 的 Progress Tracking 段規定 index.yaml 與 TaskCreate「Always update both together. Never update one without the other」——把 UI 顯示抬成第二個 truth source。User 確認改為：index.yaml 是唯一真實狀態，TaskCreate/TaskUpdate 是盡力而為的 UI 投影，未更新投影不構成流程錯誤。

## Files

- Modify: `skills/implement/SKILL.md` —
  - Transition 段改寫：先計算（讀全部 scar reports）→ 三態分支：
    - 判準成立（cross-task pattern 或 signal_lost ≥ 5）→ 依 execution mode 過 gate 建議進入 iteration
    - 判準不成立且全部 scar 可解析 → 預設 skip，輸出一行可推翻紀錄：「signal_lost=N、無 cross-task pattern，已 skip iteration（回覆可推翻）」→ 進 validate-and-ship
    - 任何 scar 解析失敗 → unknown，不准 skip，列出 parse failures 並依 execution mode 過 gate
  - 閾值 5 標註來源（歷史 iteration log 粗估）與調整方式。
  - Progress Tracking 段：刪除「Never update one without the other」，改為「index.yaml 是唯一真實狀態（source of truth）；TaskCreate/TaskUpdate 是盡力而為的 UI 投影，投影未更新不構成流程錯誤，但 index.yaml 未更新是」。
- Modify: `skills/iteration/SKILL.md` — Prerequisites/Entry 補一段進入條件說明（與 implement 轉場同一判準、同一閾值，標注 canonical 定義位置在 implement 轉場段，此處只引用——避免兩處各自演化）。
- Test: `tests/test_skills/test_iteration_entry_criteria.py`（新）

## Death Test Requirements

- Test: implement SKILL.md 缺「解析失敗 → unknown → 不准 skip」條款時轉紅（DC6：靜默漏掉 system-level rot）
- Test: skip 紀錄條款消失（skip 不留可見可推翻紀錄）時轉紅（靜默 skip 是最危險形態）
- Test: implement SKILL.md 若同時殘留舊的無條件詢問「(A) 進入 Iteration (B) Skip」與新判準（兩套並存）時轉紅（文件自相矛盾）
- Test: Progress Tracking 若殘留「Never update one without the other」措辭時轉紅

## Unit Test Contract

- Contract source: 文件化 artifact shape——implement SKILL.md Transition 段的三態分支條款（判準、skip 紀錄格式、unknown 處置）、Progress Tracking 段的 truth/投影敘述、iteration SKILL.md 的引用式進入條件。concept-token 斷言含方向性（「不准 skip」必須是禁止句，防 presence-not-polarity）
- A unit test must assert this named contract source, not implementation details.

## Implementation Steps

- [ ] Step 1: Write death tests
- [ ] Step 2: Run death tests — verify they fail
- [ ] Step 3: Write unit tests asserting the named Unit Test Contract source
- [ ] Step 4: Run unit tests — verify they fail
- [ ] Step 5: Implement minimal doc changes to pass all tests
- [ ] Step 6: Run all tests — verify they pass
- [ ] Step 7: Write scar report
- [ ] Step 8: Report back (do not commit)

## Expected Scar Report Items

- Potential shortcut: 閾值 5 未經校準（樣本只有 10 份 iteration log）——kickoff 死亡條件已定回退路徑（連兩個 feature 出現被 skip 的 rot 漏到 ship 後即恢復詢問）
- Assumption to verify: cross-task pattern 的判定（「同一 item 出現於 ≥2 task scar」）在 doc 層如何操作化——語意相似 vs 字面相同；記錄採用的判定方式與其誤差方向
- Assumption to verify: implement Transition 的 Auto Mode Gate 指針（task-4 已改）與新三態分支相容——skip 在 auto mode 也要留紀錄

## Acceptance Criteria

- Covers: "Silent failure - scar 解析失敗誤觸 iteration 預設 skip"
- Covers: happy path 逐項條件之「iteration 判準落地」
