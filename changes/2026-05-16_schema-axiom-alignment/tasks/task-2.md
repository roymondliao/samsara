# Task 2: Update implement skill scar structure

## Context

Read: `../overview.md` 與 `../2-plan.md`

依 task-1 已完成的 enum 定義（`silent_failure` + `boundary_fail` 並存），把 implement skill 的 scar schema 從「單一 `silent_failure_conditions` 收容兩種死法」改為「`silent_failure_conditions` 與 `boundary_fail_conditions` 並列」。

設計決策：兩個 list 並列而非合併為單一 typed list——理由為名稱承擔清楚責任 + grep 友善。每個 list 內容仍是 description-only 結構，但語意上分流。

## Files

- Modify: `skills/implement/templates/scar-schema.yaml` — 新增 `boundary_fail_conditions` parallel 區塊；example 部分同步增加 boundary_fail 範例；Rules 第 1 條更新（兩個 list 不可都為空）
- Modify: `skills/implement/scar-report.md` — anti-pattern 「The Clean Scar」描述補充「同時兩個 list 都為空更可疑」
- Modify: `skills/implement/SKILL.md` — 任何提及 "silent failure paths first" 改為 "silent_failure and boundary_fail paths first"；死路測試流程加 boundary_fail awareness
- Test: 死路測試在 task-7 整合，本 task 內 grep 自我驗證

## Death Test Requirements

- Test: `grep -r "death_path" skills/implement/` 必須回傳 0 matches
- Test: `grep "boundary_fail_conditions" skills/implement/templates/scar-schema.yaml` 必須回傳 ≥1 match（schema 主體）+ ≥1 match（example）
- Test: `grep "silent_failure_conditions" skills/implement/templates/scar-schema.yaml` 必須回傳 ≥1 match（並列驗證——舊欄位仍存在）
- Test: `grep "boundary_fail" skills/implement/SKILL.md` 必須回傳 ≥1 match（prose 提及）

## Implementation Steps

- [ ] Step 1: 寫死路 fixture——在臨時 scar-report 範例 fixtures 放只填 `silent_failure_conditions` 不填 `boundary_fail_conditions` 的 case，驗證新 schema 是否要求兩個都評估（即使其一為空 list）
- [ ] Step 2: 改 `scar-schema.yaml` schema 主體——在 `silent_failure_conditions` 區塊後加 `boundary_fail_conditions` parallel 區塊，欄位結構相同
- [ ] Step 3: 改 `scar-schema.yaml` Rules 區塊 — Rule 1 從「No empty scar reports」加註「兩個 failure list 都為空更可疑」
- [ ] Step 4: 改 `scar-schema.yaml` Verbatim Example — 增加 1 個 boundary_fail_conditions 範例 entry
- [ ] Step 5: 改 `scar-report.md` Anti-Pattern 段落 — 補充並列空 list 的詭異性
- [ ] Step 6: 改 `SKILL.md` 中提到 silent failure 為唯一死路類別的 prose
- [ ] Step 7: 跑上述 4 條 grep 死路測試——確認全綠
- [ ] Step 8: **Semantic alignment review** — Before writing scar report, verify:
  - 對齊 `../1.6-recalibration.md` first-principle 結論（schema 層責任明確化，非新 manifesto / 非 backward-compat）
  - 不違反 `docs/philosophy.md` / `thinking.md` / `docs/develop.md` 既有 manifesto
  - 新 enum 語意精確：`silent_failure` 嚴格指「system 啟動後死亡」、`boundary_fail` 嚴格指「system 啟動前死亡」
  - Prose 沒有退化為 yang-side：詞彙換新但思維框架仍假設「死路只有一種」即為失敗
  - Review 結論寫進 scar report `narrative` 欄位；發現本 task 修不到的語意偏差 → 標記 `assumptions_made` 並提請 cross-task iteration
- [ ] Step 9: 寫 scar report → `../scar-reports/task-2-scar.yaml`，self-test 新 scar schema 是否好用（同時填 silent + boundary）

## Expected Scar Report Items

- Potential shortcut: 改 schema 但忘記改 example 區段——schema 與 example 應同步
- Potential shortcut: Rules 第 3 條「debt_registered must be true if any known_shortcuts or silent_failure_conditions exist」——需擴展為涵蓋 boundary_fail_conditions 觸發 debt_registered
- Assumption to verify: 「兩個 list 並列」是否會讓 implementer 產生「分類焦慮」（不確定某個 failure 該放哪邊）。本 task 預設「會」但屬於可接受成本——若 task-7 死路測試後仍有大量誤分類，回 Planning
- Assumption to verify: 既有 v0.9.1 scar 報告（plain string format 向後相容條款，Rule 8）是否仍 valid？預設「是，但僅作為 legacy_imprecise 標記下的歷史紀錄，不能作為新 scar 範本」

## Acceptance Criteria

從 `../acceptance.yaml` 涵蓋的 scenarios：

- Covers: "Silent failure - partial migration leaves cross-doc schema drift"（本 task 是 cross-doc 鏈中的關鍵環節）
- Covers: "Degradation - 部分 skill prose 殘留舊 vocabulary 但 type 欄位已更新"（本 task 必須避免此情況——schema 改新但 SKILL.md prose 留舊框架）
